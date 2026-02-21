from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Evaluation
from .serializers import EvaluationListSerializer, EvaluationDetailSerializer


@extend_schema_view(
    list=extend_schema(
        tags=['Evaluations'],
        summary='List Evaluations',
        description='List evaluations for your artworks. Admins see all.'
    ),
    retrieve=extend_schema(
        tags=['Evaluations'],
        summary='Get Evaluation Details',
        description='Get detailed evaluation results including category scores and feedback.'
    )
)
class EvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for evaluations.
    """
    queryset = Evaluation.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        qs = Evaluation.objects.select_related('artwork', 'artwork__user')
        if user.is_staff or user.role == 'admin':
            return qs.all()
        return qs.filter(artwork__user=user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EvaluationDetailSerializer
        return EvaluationListSerializer
