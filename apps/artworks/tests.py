"""
Tests for Artworks app.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from PIL import Image
import io

from apps.artworks.models import Category, Artwork

User = get_user_model()


def create_test_image(name='test.jpg', size=(200, 200)):
    """Create a test image file."""
    image = Image.new('RGB', size, color='red')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=buffer.getvalue(),
        content_type='image/jpeg'
    )


class CategoryModelTest(TestCase):
    """Tests for Category model."""

    def setUp(self):
        self.category = Category.objects.create(
            name='Composition',
            name_uz='Kompozitsiya',
            description='Balans, simmetriya',
            weight=20.00,
            criteria={'balance': 'Vizual balans'},
            is_active=True
        )

    def test_category_creation(self):
        # Default language is uz, so name returns name_uz
        self.assertEqual(self.category.name, 'Kompozitsiya')
        self.assertEqual(float(self.category.weight), 20.00)
        self.assertTrue(self.category.is_active)

    def test_str(self):
        self.assertIn('Kompozitsiya', str(self.category))


class ArtworkModelTest(TestCase):
    """Tests for Artwork model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='artist1',
            password='testpass123',
            role='artist'
        )
        self.image = create_test_image()

    def test_artwork_creation(self):
        artwork = Artwork.objects.create(
            user=self.user,
            title='Test Artwork',
            image=self.image,
        )
        self.assertEqual(artwork.title, 'Test Artwork')
        self.assertEqual(artwork.status, 'pending')
        self.assertEqual(artwork.user, self.user)

    def test_str(self):
        artwork = Artwork.objects.create(
            user=self.user,
            title='My Art',
            image=self.image,
        )
        self.assertIn('My Art', str(artwork))


class ArtworkAPITest(TestCase):
    """Tests for Artwork API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiartist',
            password='testpass123',
            role='artist',
            credits=10
        )
        self.client.force_authenticate(user=self.user)

    def test_create_artwork(self):
        image = create_test_image()
        response = self.client.post('/api/v1/artworks/', {
            'title': 'API Test Artwork',
            'image': image,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['title'], 'API Test Artwork')

    def test_create_artwork_with_scheme(self):
        image = create_test_image()
        response = self.client.post('/api/v1/artworks/', {
            'title': 'Scheme Test Artwork',
            'image': image,
            'evaluation_scheme': 'graphics',
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['evaluation_scheme'], 'graphics')

    def test_create_artwork_no_credits(self):
        self.user.credits = 0
        self.user.save()
        image = create_test_image()
        response = self.client.post('/api/v1/artworks/', {
            'title': 'No Credit Art',
            'image': image,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)

    def test_create_artwork_rejects_non_image_content(self):
        fake_image = SimpleUploadedFile(
            'fake.jpg',
            b'not-an-image',
            content_type='image/jpeg',
        )
        response = self.client.post('/api/v1/artworks/', {
            'title': 'Invalid',
            'image': fake_image,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_artworks(self):
        Artwork.objects.create(
            user=self.user,
            title='Listed Art',
            image=create_test_image(),
        )
        response = self.client.get('/api/v1/artworks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_category_list(self):
        Category.objects.create(
            name='Test Cat',
            name_uz='Test Kategoriya',
            weight=100,
        )
        response = self.client.get('/api/v1/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CategoryManagementTest(TestCase):
    """Tests for Category management by Judges/Admins."""

    def setUp(self):
        self.client = APIClient()
        self.artist = User.objects.create_user(username='artist_user', password='pw', role='artist')
        self.judge = User.objects.create_user(username='judge_user', password='pw', role='judge')
        self.admin = User.objects.create_user(username='admin_user', password='pw', role='admin')

    def test_list_public(self):
        Category.objects.create(name='Public Cat', name_uz='Ochiq', weight=10)
        self.client.logout()
        response = self.client.get('/api/v1/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Why > 0? Because setUp creates nothing, but CategoryModelTest setUp runs independently.
        # However, Django TestCase resets DB between tests.
        # So we need to create one here.
        self.assertTrue(len(response.data) > 0)

    def test_create_judge(self):
        self.client.force_authenticate(user=self.judge)
        data = {
            'name': 'Perspective',
            'name_uz': 'Perspektiva',
            'name_ru': 'Перспектива',
            'name_en': 'Perspective',
            'description': 'Depth analysis',
            'weight': 15,
            'is_active': True
        }
        response = self.client.post('/api/v1/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        cat = Category.objects.first()
        self.assertEqual(cat.name_ru, 'Перспектива')

    def test_create_artist_forbidden(self):
        self.client.force_authenticate(user=self.artist)
        data = {'name': 'Hack', 'weight': 100}
        response = self.client.post('/api/v1/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_admin(self):
        cat = Category.objects.create(name='Old', weight=10)
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/v1/categories/{cat.id}/', {'name': 'New'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'New')
