"""
Tests for core security, sanitization, and health check modules.
"""
from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from rest_framework.test import APIClient
from rest_framework import status

from core.security import (
    SecurityHeadersMiddleware,
    SuspiciousActivityMiddleware,
)
from core.sanitizers import sanitize_text, sanitize_filename


class SecurityHeadersMiddlewareTest(TestCase):
    """Tests for SecurityHeadersMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware(
            get_response=lambda r: HttpResponse('ok')
        )

    def test_adds_referrer_policy(self):
        request = self.factory.get('/api/test/')
        response = self.middleware(request)
        self.assertEqual(
            response['Referrer-Policy'],
            'strict-origin-when-cross-origin'
        )

    def test_adds_permissions_policy(self):
        request = self.factory.get('/api/test/')
        response = self.middleware(request)
        self.assertIn('camera=()', response['Permissions-Policy'])

    def test_api_cache_control(self):
        request = self.factory.get('/api/v1/artworks/')
        response = self.middleware(request)
        self.assertIn('no-store', response['Cache-Control'])

    def test_non_api_no_cache_control(self):
        request = self.factory.get('/admin/')
        response = self.middleware(request)
        self.assertNotIn('Cache-Control', response)


class SuspiciousActivityMiddlewareTest(TestCase):
    """Tests for SuspiciousActivityMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SuspiciousActivityMiddleware(
            get_response=lambda r: HttpResponse('ok')
        )

    def test_blocks_sqlmap_user_agent(self):
        request = self.factory.get('/', HTTP_USER_AGENT='sqlmap/1.5')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_blocks_env_path(self):
        request = self.factory.get('/.env')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 404)

    def test_blocks_wp_admin(self):
        request = self.factory.get('/wp-admin/')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 404)

    def test_allows_normal_request(self):
        request = self.factory.get('/api/v1/artworks/',
                                   HTTP_USER_AGENT='Mozilla/5.0')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)


class SanitizeTextTest(TestCase):
    """Tests for text sanitization."""

    def test_strips_html_tags(self):
        result = sanitize_text('<script>alert("xss")</script>Hello')
        self.assertNotIn('<script>', result)
        self.assertIn('Hello', result)

    def test_strips_javascript(self):
        result = sanitize_text('javascript:alert(1)')
        self.assertNotIn('javascript', result.lower())

    def test_preserves_normal_text(self):
        result = sanitize_text("Mening rasmim — 'Bahor'")
        self.assertIn('Mening rasmim', result)

    def test_removes_control_characters(self):
        result = sanitize_text('test\x00\x01\x02text')
        self.assertEqual(result, 'testtext')

    def test_empty_input(self):
        self.assertEqual(sanitize_text(''), '')

    def test_non_string(self):
        self.assertEqual(sanitize_text(123), 123)


class SanitizeFilenameTest(TestCase):
    """Tests for filename sanitization."""

    def test_basic_filename(self):
        result = sanitize_filename('my_art.jpg')
        self.assertEqual(result, 'my_art.jpg')

    def test_strips_path(self):
        result = sanitize_filename('/etc/passwd')
        self.assertEqual(result, 'passwd')

    def test_removes_null_bytes(self):
        result = sanitize_filename('image\x00.jpg')
        self.assertEqual(result, 'image.jpg')

    def test_empty_filename(self):
        result = sanitize_filename('')
        self.assertEqual(result, 'unnamed')

    def test_special_characters(self):
        result = sanitize_filename('my art (2024).jpg')
        self.assertNotIn(' ', result)


class HealthCheckTest(TestCase):
    """Tests for health check endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_liveness_probe(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'healthy')

    def test_readiness_probe(self):
        response = self.client.get('/health/ready/')
        # DB should be ok (SQLite in tests), Redis may fail
        self.assertIn(response.status_code, [200, 503])
        self.assertIn('checks', response.data)
        self.assertIn('database', response.data['checks'])

    def test_health_no_auth_required(self):
        # Do not authenticate
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
