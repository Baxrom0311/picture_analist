"""
URL configuration for Users app.
"""
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    TokenRefreshAPIView,
    LogoutView,
    ProfileView,
    ProfileStatsView,
    ChangePasswordView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshAPIView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/stats/', ProfileStatsView.as_view(), name='profile-stats'),
]
