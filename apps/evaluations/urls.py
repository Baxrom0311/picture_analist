"""
URL configuration for Evaluations app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvaluationViewSet

router = DefaultRouter()
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')

app_name = 'evaluations'

urlpatterns = [
    path('', include(router.urls)),
]
