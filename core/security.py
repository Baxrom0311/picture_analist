"""
Security middleware and throttle classes for production hardening.
"""
import logging
import time

from django.conf import settings
from django.http import JsonResponse
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

logger = logging.getLogger('security')


# =============================================================================
# Security Headers Middleware
# =============================================================================

class SecurityHeadersMiddleware:
    """
    Add security headers to all responses.
    Supplements Django's built-in SecurityMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy (restrict browser features)
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=()'
        )

        # Cache control for API responses
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'

        # Remove server header (hide implementation details)
        if response.has_header('Server'):
            del response['Server']

        return response


# =============================================================================
# Request Logging Middleware
# =============================================================================

class RequestLoggingMiddleware:
    """
    Log all API requests with timing information.
    Useful for monitoring and debugging.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        # Only log API requests
        if request.path.startswith('/api/'):
            duration = time.time() - start_time
            user = getattr(request, 'user', None)
            username = user.username if user and user.is_authenticated else 'anonymous'

            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user': username,
                'ip': self._get_client_ip(request),
            }

            if response.status_code >= 500:
                logger.error('Server error', extra=log_data)
            elif response.status_code >= 400:
                logger.warning('Client error', extra=log_data)
            else:
                logger.info('Request completed', extra=log_data)

        return response

    @staticmethod
    def _get_client_ip(request):
        """Get client IP, accounting for reverse proxies."""
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


# =============================================================================
# Suspicious Activity Middleware
# =============================================================================

class SuspiciousActivityMiddleware:
    """
    Detect and block suspicious requests.
    """

    BLOCKED_USER_AGENTS = [
        'sqlmap', 'nikto', 'nmap', 'masscan', 'zgrab',
    ]

    BLOCKED_PATHS = [
        '/.env', '/wp-admin', '/wp-login', '/phpmyadmin',
        '/.git', '/config.php', '/admin.php',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        for blocked in self.BLOCKED_USER_AGENTS:
            if blocked in user_agent:
                logger.warning(
                    f'Blocked suspicious user agent: {user_agent}',
                    extra={'ip': request.META.get('REMOTE_ADDR')}
                )
                return JsonResponse(
                    {'error': 'Forbidden'}, status=403
                )

        # Check known malicious paths
        path = request.path.lower()
        for blocked_path in self.BLOCKED_PATHS:
            if path.startswith(blocked_path):
                logger.warning(
                    f'Blocked suspicious path: {path}',
                    extra={'ip': request.META.get('REMOTE_ADDR')}
                )
                return JsonResponse(
                    {'error': 'Not Found'}, status=404
                )

        return self.get_response(request)


# =============================================================================
# Custom Throttle Classes
# =============================================================================

class ArtworkUploadThrottle(UserRateThrottle):
    """Limit artwork uploads to 10 per hour per user."""
    rate = '10/hour'
    scope = 'artwork_upload'


class EvaluationThrottle(UserRateThrottle):
    """Limit evaluation requests to 20 per hour per user."""
    rate = '20/hour'
    scope = 'evaluation'


class BurstRateThrottle(AnonRateThrottle):
    """Limit burst anonymous requests."""
    rate = '30/minute'
    scope = 'burst'


class AuthRateThrottle(AnonRateThrottle):
    """Limit auth attempts to prevent brute force."""
    rate = '5/minute'
    scope = 'auth'
