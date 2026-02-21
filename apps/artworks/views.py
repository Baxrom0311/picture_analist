"""
Views for Artworks app.
"""
from django.db import transaction
from django.db.models import F
from rest_framework import viewsets, status, permissions, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from core.permissions import IsOwnerOrAdmin, IsJudgeOrAdmin
from core.security import ArtworkUploadThrottle, EvaluationThrottle
from core.language import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, normalize_language
from .models import Category, Artwork
from .serializers import (
    CategorySerializer,
    ArtworkListSerializer,
    ArtworkDetailSerializer,
    ArtworkCreateSerializer,
)


class ReEvaluateSerializer(drf_serializers.Serializer):
    """Optional language override for re-evaluation requests."""
    language = drf_serializers.ChoiceField(
        choices=tuple((code, code.upper()) for code in SUPPORTED_LANGUAGES),
        required=False,
    )


@extend_schema_view(
    list=extend_schema(
        tags=['Categories'],
        summary='List Categories',
        description='List all active evaluation categories. Public access.'
    ),
    retrieve=extend_schema(
        tags=['Categories'],
        summary='Get Category Details',
        description='Get details of a specific category.'
    ),
    create=extend_schema(
        tags=['Categories'],
        summary='Create Category',
        description='Create a new evaluation category (Judge/Admin only).'
    ),
    update=extend_schema(
        tags=['Categories'],
        summary='Update Category',
        description='Update an existing category (Judge/Admin only).'
    ),
    partial_update=extend_schema(
        tags=['Categories'],
        summary='Partially Update Category',
        description='Partially update an existing category (Judge/Admin only).'
    ),
    destroy=extend_schema(
        tags=['Categories'],
        summary='Delete Category',
        description='Delete a category (Judge/Admin only).'
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category management.
    Public: List/Retrieve
    Restricted (Judge/Admin): Create/Update/Delete
    """
    queryset = Category.objects.all() # Judge/Admin can see even inactive ones?
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsJudgeOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Admins/Judges see all, others see only active?
        user = self.request.user
        if user.is_authenticated and (user.role in ['admin', 'judge'] or user.is_staff):
            return Category.objects.all()
        return Category.objects.filter(is_active=True)


@extend_schema_view(
    list=extend_schema(
        tags=['Artworks'],
        summary='List Artworks',
        description='List artworks uploaded by the current user. Admins see all artworks.'
    ),
    create=extend_schema(
        tags=['Artworks'],
        summary='Upload Artwork',
        description='Upload a new artwork for evaluation. Deducts 1 credit.',
        responses={
            201: ArtworkCreateSerializer,
            400: OpenApiResponse(description='Bad Request'),
            402: OpenApiResponse(description='Payment Required (Insufficient credits)')
        }
    ),
    retrieve=extend_schema(
        tags=['Artworks'],
        summary='Get Artwork Details',
        description='Get detailed information about a specific artwork, including evaluation status.'
    ),
    update=extend_schema(
        tags=['Artworks'],
        summary='Update Artwork',
        description='Update artwork details (title, description).'
    ),
    partial_update=extend_schema(
        tags=['Artworks'],
        summary='Partially Update Artwork',
        description='Partially update artwork details.'
    ),
    destroy=extend_schema(
        tags=['Artworks'],
        summary='Delete Artwork',
        description='Delete an artwork and its associated data.'
    )
)
class ArtworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for artwork CRUD operations.
    """
    queryset = Artwork.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrAdmin)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return Artwork.objects.all().select_related('user')
        return Artwork.objects.filter(user=user).select_related('user')

    def get_serializer_class(self):
        if self.action == 'list':
            return ArtworkListSerializer
        if self.action == 'create':
            return ArtworkCreateSerializer
        return ArtworkDetailSerializer

    def get_throttles(self):
        if self.action == 'create':
            throttle_classes = [UserRateThrottle, ArtworkUploadThrottle]
        elif self.action == 're_evaluate':
            throttle_classes = [UserRateThrottle, EvaluationThrottle]
        else:
            return super().get_throttles()
        return [throttle() for throttle in throttle_classes]

    def _resolve_language(self, explicit_language=None):
        if explicit_language:
            return normalize_language(explicit_language)
        return normalize_language(self.request.LANGUAGE_CODE or DEFAULT_LANGUAGE)

    def _enqueue_evaluation(self, artwork, language):

        try:
            from apps.evaluations.tasks import evaluate_artwork_async
            evaluate_artwork_async.delay(artwork.id, language=language)
            return True
        except Exception:
            return False

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        language = self._resolve_language(serializer.validated_data.get('language'))
        user_model = request.user.__class__

        with transaction.atomic():
            user = user_model.objects.select_for_update().get(pk=request.user.pk)
            if user.credits <= 0:
                return Response(
                    {
                        'success': False,
                        'message': 'Kreditlaringiz yetarli emas. Admin bilan bog\'laning.'
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

            artwork = serializer.save(user=user)
            artwork.status = 'processing'
            artwork.save(update_fields=['status'])

            if not user.deduct_credit():
                return Response(
                    {
                        'success': False,
                        'message': 'Kreditlaringiz yetarli emas. Admin bilan bog\'laning.'
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

        if not self._enqueue_evaluation(artwork, language=language):
            artwork.status = 'failed'
            artwork.save(update_fields=['status'])
            user_model.objects.filter(pk=request.user.pk).update(credits=F('credits') + 1)
            return Response(
                {
                    'success': False,
                    'message': 'Baholash navbatga qo\'yilmadi. Iltimos qayta urinib ko\'ring.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Return artwork detail for frontend (needs 'id' for polling)
        artwork = Artwork.objects.get(pk=artwork.pk)
        detail_serializer = ArtworkDetailSerializer(artwork)
        headers = self.get_success_headers(serializer.data)
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @extend_schema(
        tags=['Artworks'],
        summary='Re-evaluate Artwork',
        description='Trigger re-evaluation for an existing artwork. Deducts 1 credit.',
        request=ReEvaluateSerializer,
        responses={
            200: OpenApiResponse(description='Re-evaluation started'),
            400: OpenApiResponse(description='Bad Request'),
            402: OpenApiResponse(description='Payment Required (Insufficient credits)')
        }
    )
    @action(detail=True, methods=['post'], url_path='re-evaluate')
    def re_evaluate(self, request, pk: int | None = None):
        """
        POST /api/artworks/{id}/re-evaluate/
        Re-evaluate an existing artwork.
        """
        serializer = ReEvaluateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        language = self._resolve_language(serializer.validated_data.get('language'))

        user_model = request.user.__class__
        with transaction.atomic():
            user = user_model.objects.select_for_update().get(pk=request.user.pk)
            artwork = Artwork.objects.select_for_update().get(pk=self.get_object().pk)
            if user.credits <= 0:
                return Response(
                    {
                        'success': False,
                        'message': 'Kreditlaringiz yetarli emas.'
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

            artwork.status = 'processing'
            artwork.save(update_fields=['status'])
            if not user.deduct_credit():
                return Response(
                    {
                        'success': False,
                        'message': 'Kreditlaringiz yetarli emas.'
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

        if not self._enqueue_evaluation(artwork, language=language):
            artwork.status = 'failed'
            artwork.save(update_fields=['status'])
            user_model.objects.filter(pk=request.user.pk).update(credits=F('credits') + 1)
            return Response(
                {
                    'success': False,
                    'message': 'Baholash navbatga qo\'yilmadi. Iltimos qayta urinib ko\'ring.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({
            'success': True,
            'message': 'Qayta baholash boshlandi.',
            'credits_remaining': user_model.objects.get(pk=request.user.pk).credits,
            'language': language,
        })
