"""
Scoring Service - Creates evaluation records from LLM results.
"""
import logging
from decimal import Decimal

from apps.artworks.models import Category
from apps.evaluations.models import Evaluation, CategoryScore, EvaluationHistory
from apps.evaluations.services.prompt_templates import get_grade

logger = logging.getLogger(__name__)


class ScoringService:
    """
    Service for creating and managing evaluation scores.

    Handles:
    - Evaluation record creation
    - Per-category score creation
    - Weighted average calculation
    - Artwork status updates
    - History logging
    """

    # Mapping from Category.name to LLM response key
    CATEGORY_KEY_MAP = {
        'Composition': 'composition',
        'composition': 'composition',
        'Kompozitsiya': 'composition',
        'kompozitsiya': 'composition',
        'Color and Light': 'color_light',
        'color and light': 'color_light',
        "Rang va yorug'lik": 'color_light',
        "rang va yorug'lik": 'color_light',
        'Technique': 'technique',
        'technique': 'technique',
        'Texnika': 'technique',
        'texnika': 'technique',
        'Creativity': 'creativity',
        'creativity': 'creativity',
        'Kreativlik': 'creativity',
        'kreativlik': 'creativity',
        'Overall Impact': 'overall_impact',
        'overall impact': 'overall_impact',
        "Umumiy ta'sir": 'overall_impact',
        "umumiy ta'sir": 'overall_impact',
    }
    PROMPT_VERSION = '2.0'

    def init_evaluation(self, artwork, model_name='gemini-flash-latest', language='uz'):
        """
        Create or reset an evaluation record before processing.
        """
        defaults = {
            'llm_provider': 'google',
            'llm_model': model_name,
            'prompt_version': self.PROMPT_VERSION,
            'total_score': Decimal('0.00'),
            'summary': '',
            'grade': '',
            'raw_response': {},
            'processing_time': Decimal('0.00'),
            'api_cost': Decimal('0.00'),
        }
        evaluation, created = Evaluation.objects.get_or_create(
            artwork=artwork,
            defaults=defaults,
        )
        if not created:
            for field, value in defaults.items():
                setattr(evaluation, field, value)
            evaluation.save()

        artwork.status = 'processing'
        artwork.save(update_fields=['status'])

        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action='started' if created else 'retried',
            message='Baholash jarayoni boshlandi' if created else 'Baholash qayta boshlandi',
            metadata={
                'artwork_id': artwork.id,
                'model': model_name,
                'language': language,
            }
        )

        logger.info(
            "Initialized evaluation %s for artwork %s (created=%s)",
            evaluation.id,
            artwork.id,
            created,
        )
        return evaluation

    def update_evaluation(self, evaluation, llm_result):
        """
        Update an existing evaluation with LLM results.
        Replaces 'create_evaluation'.
        """
        categories = Category.objects.filter(is_active=True)
        result_data = llm_result.get('result', {})

        # 1. Update Evaluation record
        evaluation.llm_model = llm_result.get('model', evaluation.llm_model)
        evaluation.summary = result_data.get('summary', '')
        evaluation.grade = result_data.get('grade', '')
        evaluation.raw_response = result_data
        evaluation.processing_time = Decimal(str(llm_result.get('processing_time', 0)))
        evaluation.api_cost = Decimal(str(llm_result.get('api_cost', 0)))
        
        # 2. Create CategoryScores and calculate weighted average
        total_weighted_score = Decimal('0.00')
        feedback_data = result_data.get('feedback', {})
        score_data = result_data.get('scores', {})

        # Clear existing scores if any (for re-evaluation safety)
        evaluation.category_scores.all().delete()

        for category in categories:
            search_name = (
                getattr(category, 'name_en', None)
                or getattr(category, 'name', None)
                or getattr(category, 'name_uz', '')
            )
            category_key = self._get_category_key(search_name)
            category_feedback = feedback_data.get(category_key, {})

            score_value = category_feedback.get('score', score_data.get(category_key, 0))
            score = Decimal(str(score_value))
            if score < 0:
                score = Decimal('0.00')
            if score > 100:
                score = Decimal('100.00')

            CategoryScore.objects.create(
                evaluation=evaluation,
                category=category,
                score=score,
                feedback=category_feedback.get('analysis', 'Tahlil mavjud emas'),
                strengths=category_feedback.get('strengths', []),
                improvements=category_feedback.get('improvements', [])
            )

            # Weighted score
            weight = category.weight / Decimal('100')
            total_weighted_score += (score * weight)

        official_rubric = result_data.get('official_rubric', {})
        official_total = Decimal(str(official_rubric.get('total_score', 0)))
        official_max = Decimal(str(official_rubric.get('max_score', 0)))
        if official_max > 0:
            normalized_score = (official_total / official_max) * Decimal('100')
            evaluation.total_score = round(normalized_score, 2)
            if not evaluation.grade:
                evaluation.grade = get_grade(evaluation.total_score)
        else:
            evaluation.total_score = round(total_weighted_score, 2)
            if not evaluation.grade:
                evaluation.grade = get_grade(evaluation.total_score)

        evaluation.save()

        # 4. Update artwork status
        evaluation.artwork.status = 'completed'
        evaluation.artwork.save(update_fields=['status'])

        # 5. History: completed
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action='completed',
            message=f'Baholash muvaffaqiyatli yakunlandi. Ball: {evaluation.total_score}',
            metadata={
                'total_score': float(evaluation.total_score),
                'processing_time': float(evaluation.processing_time),
                'official_rubric_total': float(official_total),
                'official_rubric_max': float(official_max),
            }
        )

        logger.info(
            f"Evaluation updated for artwork #{evaluation.artwork.id}: "
            f"score={evaluation.total_score}, grade={evaluation.grade}"
        )

        return evaluation

    def fail_evaluation(self, evaluation, error_message):
        """
        Log failure for an existing evaluation.
        """
        # Update artwork status
        evaluation.artwork.status = 'failed'
        evaluation.artwork.save(update_fields=['status'])
        
        # Log failure
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action='failed',
            message=str(error_message),
            metadata={'error': str(error_message)}
        )
        logger.error(f"Evaluation #{evaluation.id} marked as failed: {error_message}")

    def _get_category_key(self, category_name):
        """Map category name to LLM response key."""
        normalized = (category_name or '').strip().lower()
        for candidate in (
            category_name,
            (category_name or '').strip(),
            (category_name or '').strip().title(),
            normalized,
        ):
            if candidate in self.CATEGORY_KEY_MAP:
                return self.CATEGORY_KEY_MAP[candidate]
        return normalized.replace(' ', '_')
