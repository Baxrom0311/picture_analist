"""
Root URL Configuration for AI Art Evaluation System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from core.health import health_check, readiness_check

urlpatterns = [
    # Health checks (no auth required)
    path('health/', health_check, name='health-check'),
    path('health/ready/', readiness_check, name='readiness-check'),

    # Admin
    path(settings.ADMIN_URL, admin.site.urls),

    # API endpoints
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/', include('apps.artworks.urls')),
    path('api/v1/', include('apps.evaluations.urls')),

    # API Documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Admin site customization
admin.site.site_header = '🎨 AI Art Evaluation Admin'
admin.site.site_title = 'Art Evaluation'
admin.site.index_title = 'Dashboard'
