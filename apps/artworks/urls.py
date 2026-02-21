"""
URL configuration for Artworks app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ArtworkViewSet

router = DefaultRouter()
router.register(r'artworks', ArtworkViewSet, basename='artwork')
router.register(r'categories', CategoryViewSet, basename='category')

app_name = 'artworks'

urlpatterns = [
    path('', include(router.urls)),
]
