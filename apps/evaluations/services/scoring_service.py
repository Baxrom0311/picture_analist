"""
Scoring Service - Creates evaluation records from LLM results.
"""
import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction

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
        categories = list(Category.objects.filter(is_active=True))
        result_data = llm_result.get('result', {})
        self._validate_result_data(result_data, categories)

        with transaction.atomic():
            # 1. Update Evaluation record
            evaluation.llm_model = llm_result.get('model', evaluation.llm_model)
            evaluation.summary = result_data.get('summary', '')
            evaluation.grade = result_data.get('grade', '')
            evaluation.raw_response = result_data
            evaluation.processing_time = self._parse_decimal(
                llm_result.get('processing_time', 0),
                'processing_time',
            )
            evaluation.api_cost = self._parse_decimal(
                llm_result.get('api_cost', 0),
                'api_cost',
            )

            # 2. Create CategoryScores and calculate weighted average
            total_weighted_score = Decimal('0.00')
            feedback_data = result_data.get('feedback', {})
            score_data = result_data.get('scores', {})

            # Clear existing scores only after the payload is validated.
            evaluation.category_scores.all().delete()

            for category in categories:
                search_name = (
                    getattr(category, 'name_en', None)
                    or getattr(category, 'name', None)
                    or getattr(category, 'name_uz', '')
                )
                category_key = self._get_category_key(search_name)
                category_feedback = feedback_data[category_key]

                score_value = category_feedback.get('score', score_data[category_key])
                score = self._parse_decimal(score_value, f'{category_key} score')
                if score < 0:
                    score = Decimal('0.00')
                if score > 100:
                    score = Decimal('100.00')

                CategoryScore.objects.create(
                    evaluation=evaluation,
                    category=category,
                    score=score,
                    feedback=category_feedback['analysis'].strip(),
                    strengths=category_feedback.get('strengths', []),
                    improvements=category_feedback.get('improvements', []),
                )

                # Weighted score
                weight = category.weight / Decimal('100')
                total_weighted_score += (score * weight)

            official_rubric = result_data.get('official_rubric', {})
            official_total = self._parse_decimal(
                official_rubric.get('total_score'),
                'official_rubric.total_score',
            )
            official_max = self._parse_decimal(
                official_rubric.get('max_score'),
                'official_rubric.max_score',
            )
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
        # Preserve the last successful evaluation when a re-run fails.
        evaluation.artwork.status = 'completed' if self._has_published_result(evaluation) else 'failed'
        evaluation.artwork.save(update_fields=['status'])
        
        # Log failure
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action='failed',
            message=str(error_message),
            metadata={'error': str(error_message)}
        )
        logger.error(f"Evaluation #{evaluation.id} marked as failed: {error_message}")

    def _validate_result_data(self, result_data, categories):
        if not isinstance(result_data, dict):
            raise ValueError('LLM natijasi JSON object bo\'lishi kerak.')

        summary = result_data.get('summary')
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError('LLM natijasida summary maydoni topilmadi.')

        grade = result_data.get('grade', '')
        if grade and not isinstance(grade, str):
            raise ValueError('LLM natijasidagi grade noto\'g\'ri formatda.')

        scores = result_data.get('scores')
        if not isinstance(scores, dict):
            raise ValueError('LLM natijasida scores obyekt topilmadi.')

        feedback = result_data.get('feedback')
        if not isinstance(feedback, dict):
            raise ValueError('LLM natijasida feedback obyekt topilmadi.')

        for category in categories:
            category_key = self._get_category_key(
                getattr(category, 'name_en', None)
                or getattr(category, 'name', None)
                or getattr(category, 'name_uz', '')
            )
            if category_key not in scores:
                raise ValueError(f'LLM natijasida {category_key} uchun score topilmadi.')
            self._parse_decimal(scores[category_key], f'{category_key} score')

            category_feedback = feedback.get(category_key)
            if not isinstance(category_feedback, dict):
                raise ValueError(f'LLM natijasida {category_key} uchun feedback topilmadi.')

            analysis = category_feedback.get('analysis')
            if not isinstance(analysis, str) or not analysis.strip():
                raise ValueError(f'LLM natijasida {category_key} uchun analysis topilmadi.')

            if 'score' in category_feedback:
                self._parse_decimal(category_feedback['score'], f'{category_key} feedback score')

            for list_field in ('strengths', 'improvements'):
                value = category_feedback.get(list_field, [])
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise ValueError(
                        f'LLM natijasidagi {category_key}.{list_field} maydoni matnlar ro\'yxati bo\'lishi kerak.'
                    )

        official_rubric = result_data.get('official_rubric')
        if not isinstance(official_rubric, dict):
            raise ValueError('LLM natijasida official_rubric topilmadi.')

        max_score = self._parse_decimal(
            official_rubric.get('max_score'),
            'official_rubric.max_score',
        )
        total_score = self._parse_decimal(
            official_rubric.get('total_score'),
            'official_rubric.total_score',
        )
        if max_score <= 0:
            raise ValueError('official_rubric.max_score musbat bo\'lishi kerak.')
        if total_score < 0 or total_score > max_score:
            raise ValueError('official_rubric.total_score ruxsat etilgan oraliqda emas.')

        sections = official_rubric.get('sections')
        if not isinstance(sections, list) or not sections:
            raise ValueError('official_rubric.sections bo\'sh bo\'lmasligi kerak.')

        for section in sections:
            if not isinstance(section, dict):
                raise ValueError('official_rubric.sections elementlari obyekt bo\'lishi kerak.')
            if not isinstance(section.get('section_key'), str) or not section['section_key'].strip():
                raise ValueError('official_rubric.section_key topilmadi.')

            section_score = self._parse_decimal(
                section.get('section_score'),
                f"{section.get('section_key', 'section')}.section_score",
            )
            section_max_score = self._parse_decimal(
                section.get('section_max_score'),
                f"{section.get('section_key', 'section')}.section_max_score",
            )
            if section_score < 0 or section_score > section_max_score:
                raise ValueError('official_rubric section score noto\'g\'ri.')

            criteria = section.get('criteria')
            if not isinstance(criteria, list) or not criteria:
                raise ValueError('official_rubric criteria bo\'sh bo\'lmasligi kerak.')

            for criterion in criteria:
                if not isinstance(criterion, dict):
                    raise ValueError('official_rubric criterion obyekt bo\'lishi kerak.')
                if not isinstance(criterion.get('criterion_key'), str) or not criterion['criterion_key'].strip():
                    raise ValueError('criterion_key topilmadi.')
                if criterion.get('level') not in {'full', 'partial', 'none'}:
                    raise ValueError('criterion level noto\'g\'ri.')

                awarded_score = self._parse_decimal(
                    criterion.get('awarded_score'),
                    f"{criterion.get('criterion_key', 'criterion')}.awarded_score",
                )
                criterion_max_score = self._parse_decimal(
                    criterion.get('max_score'),
                    f"{criterion.get('criterion_key', 'criterion')}.max_score",
                )
                if criterion_max_score <= 0:
                    raise ValueError('criterion max_score musbat bo\'lishi kerak.')
                if awarded_score < 0 or awarded_score > criterion_max_score:
                    raise ValueError('criterion awarded_score noto\'g\'ri.')

    def _parse_decimal(self, value, field_name):
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f'{field_name} son bo\'lishi kerak.') from None

    def _has_published_result(self, evaluation):
        if evaluation.category_scores.exists():
            return True
        if isinstance(evaluation.raw_response, dict) and evaluation.raw_response:
            return True
        return evaluation.total_score > 0 or bool((evaluation.summary or '').strip())

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
