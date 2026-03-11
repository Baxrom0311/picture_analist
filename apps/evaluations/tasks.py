"""
Celery tasks for async artwork evaluation.
"""
import logging
from celery import shared_task

from apps.artworks.models import Artwork, Category
from apps.evaluations.models import EvaluationHistory
from apps.evaluations.services.llm_service import LLMService
from apps.evaluations.services.scoring_service import ScoringService
from core.language import normalize_language

logger = logging.getLogger(__name__)
NON_RETRYABLE_EXCEPTIONS = (ValueError,)
NON_RETRYABLE_LLM_ERROR_MARKERS = (
    '400 INVALID_ARGUMENT',
    'API_KEY_INVALID',
    'API key not valid',
    'PERMISSION_DENIED',
    'UNAUTHENTICATED',
)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name='evaluations.evaluate_artwork_async'
)
def evaluate_artwork_async(self, artwork_id, language='uz'):
    """
    Async task to evaluate an artwork using Gemini LLM.
    """
    try:
        artwork = Artwork.objects.get(id=artwork_id)
    except Artwork.DoesNotExist:
        logger.error(f"Artwork #{artwork_id} not found")
        return {'success': False, 'error': f'Artwork #{artwork_id} not found'}

    language = normalize_language(language)

    # Initialize scoring service
    scoring_service = ScoringService()
    evaluation = None
    llm_result = None

    try:
        # Import settings to get current model name if needed
        from django.conf import settings
        
        # 0. Initialize evaluation record
        evaluation = scoring_service.init_evaluation(artwork, model_name=settings.GEMINI_MODEL, language=language)
        
        # Get active categories
        categories = Category.objects.filter(is_active=True)
        if not categories.exists():
            raise ValueError("Faol kategoriyalar topilmadi.")

        # LLM evaluation
        llm_service = LLMService()
        llm_result = llm_service.evaluate_artwork(
            artwork,
            categories,
            language=language,
            evaluation_scheme=artwork.evaluation_scheme,
        )

        if not llm_result['success']:
            raise _build_llm_exception(llm_result)

        # Update evaluation with results
        evaluation = scoring_service.update_evaluation(evaluation, llm_result)

        return {
            'success': True,
            'evaluation_id': evaluation.id,
            'total_score': float(evaluation.total_score),
            'grade': evaluation.grade
        }

    except Exception as exc:
        logger.error(f"Artwork #{artwork_id} evaluation failed: {str(exc)}")

        # Retry logic
        if not isinstance(exc, NON_RETRYABLE_EXCEPTIONS) and self.request.retries < self.max_retries:
            if evaluation:
                EvaluationHistory.objects.create(
                    evaluation=evaluation,
                    action='retried',
                    message=f'Qayta urinish #{self.request.retries + 1}',
                    metadata={'error': str(exc)},
                )
            logger.info(f"Retrying artwork #{artwork_id} evaluation (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc)

        # Log failure on final attempt
        if evaluation:
            scoring_service.fail_evaluation(
                evaluation,
                str(exc),
                metadata=_build_failure_metadata(llm_result),
            )
        else:
            artwork.status = 'failed'
            artwork.save(update_fields=['status'])

        return {
            'success': False,
            'error': str(exc)
        }


def _build_failure_metadata(llm_result):
    if not isinstance(llm_result, dict):
        return {}

    metadata = {}
    parsed_result = llm_result.get('result')
    raw_response = llm_result.get('raw_response')

    if isinstance(parsed_result, dict):
        metadata['result_keys'] = sorted(parsed_result.keys())

        scores = parsed_result.get('scores')
        if isinstance(scores, dict):
            metadata['score_keys'] = sorted(scores.keys())

        feedback = parsed_result.get('feedback')
        if isinstance(feedback, dict):
            metadata['feedback_keys'] = sorted(feedback.keys())

        # Keep the parsed payload for postmortem debugging when validation fails.
        metadata['llm_result'] = parsed_result

    if raw_response:
        metadata['llm_raw_response'] = str(raw_response)[:10000]

    model_name = llm_result.get('model')
    if model_name:
        metadata['llm_model'] = model_name

    return metadata


def _build_llm_exception(llm_result):
    error_message = str(llm_result.get('error', 'LLM evaluation failed'))
    if any(marker in error_message for marker in NON_RETRYABLE_LLM_ERROR_MARKERS):
        return ValueError(error_message)
    return RuntimeError(error_message)
