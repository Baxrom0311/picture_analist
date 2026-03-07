"""
Tests for Users app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='artist'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'artist')
        self.assertEqual(self.user.credits, 10)

    def test_has_credits(self):
        self.assertTrue(self.user.has_credits)

    def test_deduct_credit(self):
        result = self.user.deduct_credit()
        self.assertTrue(result)
        self.assertEqual(self.user.credits, 9)

    def test_deduct_credit_zero(self):
        self.user.credits = 0
        self.user.save()
        result = self.user.deduct_credit()
        self.assertFalse(result)

    def test_add_credits(self):
        self.user.add_credits(5)
        self.assertEqual(self.user.credits, 15)

    def test_str(self):
        self.assertIn('testuser', str(self.user))


class AuthAPITest(TestCase):
    """Tests for authentication endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
        self.login_url = '/api/v1/auth/login/'

    def test_register_success(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'Test',
            'last_name': 'User',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)

    def test_register_cannot_escalate_role(self):
        data = {
            'username': 'elevated',
            'email': 'elevated@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'role': 'admin',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'artist')
        created_user = User.objects.get(username='elevated')
        self.assertEqual(created_user.role, 'artist')

    def test_register_password_mismatch(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'DifferentPass!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(
            username='logintest',
            password='StrongPass123!'
        )
        response = self.client.post(self.login_url, {
            'username': 'logintest',
            'password': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_profile_authenticated(self):
        user = User.objects.create_user(
            username='profiletest',
            password='StrongPass123!'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profile_unauthenticated(self):
        response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_blacklists_existing_refresh_tokens(self):
        user = User.objects.create_user(
            username='changepw',
            password='StrongPass123!',
        )
        refresh = RefreshToken.for_user(user)

        self.client.force_authenticate(user=user)
        response = self.client.put('/api/v1/auth/change-password/', {
            'old_password': 'StrongPass123!',
            'new_password': 'NewStrongPass123!',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=str(refresh['jti'])).exists()
        )
