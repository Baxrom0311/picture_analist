"""
Custom exception handler and exception classes for the API.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'success': False,
            'error': {
                'status_code': response.status_code,
                'message': _get_error_message(response),
                'details': response.data,
            }
        }
        response.data = custom_response

    return response


def _get_error_message(response):
    """Extract a readable error message from the response."""
    if response.status_code == 400:
        return 'Bad Request - Invalid data provided'
    elif response.status_code == 401:
        return 'Unauthorized - Authentication required'
    elif response.status_code == 403:
        return 'Forbidden - You do not have permission'
    elif response.status_code == 404:
        return 'Not Found - Resource does not exist'
    elif response.status_code == 429:
        return 'Too Many Requests - Rate limit exceeded'
    return 'An error occurred'


class InsufficientCreditsError(Exception):
    """Raised when user does not have enough credits."""
    pass


class ImageValidationError(Exception):
    """Raised when image validation fails."""
    pass


class LLMServiceError(Exception):
    """Raised when LLM service encounters an error."""
    pass


class EvaluationError(Exception):
    """Raised when evaluation process fails."""
    pass
