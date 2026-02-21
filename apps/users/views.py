"""
Views for Users app - Authentication and Profile management.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Avg, Max, Sum

from core.security import AuthRateThrottle
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserStatsSerializer,
    ChangePasswordSerializer,
)

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary='Register a new user',
    description='Create a new user account with default role (Artist) and credits.',
    responses={
        201: UserRegistrationSerializer,
        400: OpenApiResponse(description='Bad Request')
    }
)
class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Register a new user account.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (AuthRateThrottle,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'Ro\'yxatdan muvaffaqiyatli o\'tdingiz!',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    summary='Login',
    description='Authenticate with username and password to obtain JWT access and refresh tokens.',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string'},
                'access': {'type': 'string'},
            }
        }
    }
)
class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Login with username and password, returns JWT tokens.
    """
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (AuthRateThrottle,)


@extend_schema(
    tags=['Authentication'],
    summary='Refresh Token',
    description='Get a new access token using a valid refresh token.'
)
class TokenRefreshAPIView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Refresh an access token using a refresh token.
    """
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (AuthRateThrottle,)


@extend_schema(
    tags=['Authentication'],
    summary='Logout',
    description='Blacklist the refresh token to end the session.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'Refresh token to blacklist'}
            },
            'required': ['refresh']
        }
    },
    responses={
        200: {'description': 'Successfully logged out'},
        400: {'description': 'Invalid token'}
    }
)
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token to log out.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {'success': True, 'message': 'Muvaffaqiyatli chiqildi.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'success': False, 'message': 'Token topilmadi yoki yaroqsiz.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['Profile'],
    summary='Get/Update Profile',
    description='Retrieve or update current user profile information.'
)
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/profile/ - Get current user profile
    PUT/PATCH /api/profile/ - Update profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=['Profile'],
    summary='Get User Statistics',
    description='Get statistics about user artworks, evaluations, and credits.',
    responses={200: UserStatsSerializer}
)
class ProfileStatsView(APIView):
    """
    GET /api/profile/stats/
    Get statistics for the current user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        artworks = user.artworks.all()

        stats = {
            'total_artworks': artworks.count(),
            'evaluated_artworks': artworks.filter(status='completed').count(),
            'pending_artworks': artworks.filter(status__in=['pending', 'processing']).count(),
            'average_score': artworks.filter(
                evaluation__isnull=False
            ).aggregate(avg=Avg('evaluation__total_score'))['avg'],
            'highest_score': artworks.filter(
                evaluation__isnull=False
            ).aggregate(max=Max('evaluation__total_score'))['max'],
            'credits_remaining': user.credits,
            'total_api_cost': artworks.filter(
                evaluation__isnull=False
            ).aggregate(total=Sum('evaluation__api_cost'))['total'],
        }

        serializer = UserStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema(
    tags=['Authentication'],
    summary='Change Password',
    description='Change the current user password.'
)
class ChangePasswordView(generics.UpdateAPIView):
    """
    PUT /api/auth/change-password/
    Change the current user's password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({
            'success': True,
            'message': 'Parol muvaffaqiyatli o\'zgartirildi.'
        })
