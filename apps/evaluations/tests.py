"""
Tests for Evaluations app.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from PIL import Image
import io

from apps.artworks.models import Category, Artwork
from apps.evaluations.models import Evaluation, CategoryScore, EvaluationHistory
from apps.evaluations.services.scoring_service import ScoringService
from apps.evaluations.services.prompt_templates import get_grade

User = get_user_model()


def create_test_image():
    """Create a test image file."""
    image = Image.new('RGB', (200, 200), color='blue')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile('test.jpg', buffer.getvalue(), content_type='image/jpeg')


def create_test_categories():
    """Create the default 5 categories."""
    categories = [
        ('Composition', 'Kompozitsiya', 20),
        ('Color and Light', 'Rang va yorug\'lik', 20),
        ('Technique', 'Texnika', 25),
        ('Creativity', 'Kreativlik', 20),
        ('Overall Impact', 'Umumiy ta\'sir', 15),
    ]
    return [
        Category.objects.create(
            name=name, name_uz=name_uz, name_en=name, weight=weight, is_active=True
        )
        for name, name_uz, weight in categories
    ]


class EvaluationModelTest(TestCase):
    """Tests for Evaluation model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='evaluser', password='testpass123'
        )
        self.artwork = Artwork.objects.create(
            user=self.user, title='Eval Art', image=create_test_image()
        )

    def test_evaluation_creation(self):
        evaluation = Evaluation.objects.create(
            artwork=self.artwork,
            llm_model='claude-3-5-sonnet',
            total_score=Decimal('85.50'),
            grade='B',
        )
        self.assertEqual(evaluation.total_score, Decimal('85.50'))
        self.assertEqual(evaluation.grade, 'B')


class ScoringServiceTest(TestCase):
    """Tests for ScoringService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='scoreuser', password='testpass123'
        )
        self.artwork = Artwork.objects.create(
            user=self.user, title='Score Art', image=create_test_image()
        )
        self.categories = create_test_categories()

    def test_evaluation_flow(self):
        service = ScoringService()
        
        # 1. Init
        evaluation = service.init_evaluation(self.artwork, model_name='gemini-flash-latest')
        self.assertEqual(evaluation.total_score, Decimal('0.00'))
        self.assertEqual(EvaluationHistory.objects.count(), 1)
        self.assertEqual(EvaluationHistory.objects.first().action, 'started')

        # 2. Update
        llm_result = {
            'success': True,
            'model': 'gemini-flash-latest',
            'processing_time': 3.5,
            'api_cost': 0.01,
            'result': {
                'scores': {
                    'composition': 85,
                    'color_light': 78,
                    'technique': 90,
                    'creativity': 82,
                    'overall_impact': 88,
                },
                'feedback': {
                    'composition': {'score': 85, 'analysis': 'Good'},
                    'color_light': {'score': 78, 'analysis': 'Good'},
                    'technique': {'score': 90, 'analysis': 'Good'},
                    'creativity': {'score': 82, 'analysis': 'Good'},
                    'overall_impact': {'score': 88, 'analysis': 'Good'},
                },
                'summary': 'Test summary',
                'grade': 'B',
            }
        }

        updated_evaluation = service.update_evaluation(evaluation, llm_result)

        self.assertIsNotNone(updated_evaluation)
        self.assertEqual(updated_evaluation.grade, 'B')
        self.assertEqual(updated_evaluation.category_scores.count(), 5)
        self.assertEqual(self.artwork.status, 'completed')
        
        # Check weighted average: 85*0.2 + 78*0.2 + 90*0.25 + 82*0.2 + 88*0.15 = 84.70
        self.assertEqual(float(updated_evaluation.total_score), 84.70)
        
        # History check
        self.assertEqual(EvaluationHistory.objects.count(), 2) # started + completed
        pass

    def test_fail_evaluation(self):
        service = ScoringService()
        evaluation = service.init_evaluation(self.artwork)
        service.fail_evaluation(evaluation, "Test Error")
        
        self.assertEqual(evaluation.artwork.status, 'failed')
        self.assertEqual(EvaluationHistory.objects.count(), 2) # started + failed
        self.assertTrue(EvaluationHistory.objects.filter(action='failed').exists())


class EvaluationAPITest(TestCase):
    """Tests for Evaluation API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='evalapi', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_evaluations(self):
        response = self.client.get('/api/v1/evaluations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_evaluations_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/v1/evaluations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LLMServiceTest(TestCase):
    """Tests for LLMService with Google Gemini."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='llmuser', password='testpass123'
        )
        self.artwork = Artwork.objects.create(
            user=self.user, title='LLM Art', image=create_test_image()
        )
        self.categories = create_test_categories()

    @patch('apps.evaluations.services.llm_service.genai')
    def test_evaluate_artwork_success(self, mock_genai):
        # Mock Gemini Client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"scores": {"composition": 90}, "grade": "A"}'
        mock_response.usage_metadata.prompt_token_count = 1000
        mock_response.usage_metadata.candidates_token_count = 500
        
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        from apps.evaluations.services.llm_service import LLMService
        service = LLMService()
        # Mocking settings because LLMService reads settings.GEMINI_API_KEY
        with patch('django.conf.settings.GEMINI_API_KEY', 'test-key'):
             with patch('django.conf.settings.GEMINI_MODEL', 'gemini-test'):
                service = LLMService() # re-init to pick up settings/mock
                result = service.evaluate_artwork(self.artwork, self.categories)

        self.assertTrue(result['success'])
        self.assertEqual(result['result']['grade'], 'A')
        # Cost: 1000*0.35/1M + 500*1.05/1M = 0.00035 + 0.000525 = 0.000875
        self.assertAlmostEqual(result['api_cost'], 0.000875)

    @patch('apps.evaluations.services.llm_service.genai')
    def test_evaluate_artwork_failure(self, mock_genai):
        # Mock failure
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client

        from apps.evaluations.services.llm_service import LLMService
        with patch('django.conf.settings.GEMINI_API_KEY', 'test-key'):
             with patch('django.conf.settings.GEMINI_MODEL', 'gemini-test'):
                service = LLMService()
                result = service.evaluate_artwork(self.artwork, self.categories)

        self.assertFalse(result['success'])
        self.assertIn("API Error", result['error'])


class PromptTemplatesTest(TestCase):
    """Tests for prompt template helpers."""

    def test_get_grade_handles_decimal_boundaries(self):
        self.assertEqual(get_grade(89.5), 'B')
        self.assertEqual(get_grade(79.2), 'C')
