"""
Custom exception handling for DineFlow2 API.
Ensures consistent error response format across all endpoints.

Error Response Contract:
{
    "error": "ERROR_CODE",
    "message": "Human-readable description."
}
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404

logger = logging.getLogger(__name__)


# Error code mapping
ERROR_CODES = {
    'authentication_failed': 'AUTHENTICATION_FAILED',
    'not_authenticated': 'NOT_AUTHENTICATED',
    'permission_denied': 'PERMISSION_DENIED',
    'not_found': 'NOT_FOUND',
    'method_not_allowed': 'METHOD_NOT_ALLOWED',
    'validation_error': 'VALIDATION_ERROR',
    'throttled': 'RATE_LIMITED',
    'parse_error': 'PARSE_ERROR',
    'unsupported_media_type': 'UNSUPPORTED_MEDIA_TYPE',
}


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors consistently.
    
    Returns:
    {
        "error": "ERROR_CODE",
        "message": "Human-readable description.",
        "details": {...}  # Optional, for validation errors
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Preserve structured business errors (e.g. stock/availability enforcement)
        # when they intentionally return a top-level `code` contract.
        if isinstance(getattr(response, 'data', None), dict) and 'code' in response.data:
            # DRF may coerce dict values into one-element lists for ValidationError dicts.
            # Normalize to keep the contract stable for clients.
            for key in [
                'code',
                'message',
                'item_id',
                'item_name',
                'available_quantity',
                'requested_quantity',
            ]:
                if key in response.data and isinstance(response.data[key], list) and len(response.data[key]) == 1:
                    response.data[key] = response.data[key][0]
            return response
        if (
            isinstance(getattr(response, 'data', None), list)
            and len(response.data) == 1
            and isinstance(response.data[0], dict)
            and 'code' in response.data[0]
        ):
            response.data = response.data[0]
            for key in [
                'code',
                'message',
                'item_id',
                'item_name',
                'available_quantity',
                'requested_quantity',
            ]:
                if key in response.data and isinstance(response.data[key], list) and len(response.data[key]) == 1:
                    response.data[key] = response.data[key][0]
            return response

        error_code = ERROR_CODES.get(
            getattr(exc, 'default_code', 'error'),
            'SERVER_ERROR'
        )
        
        # Get message from exception
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                # Validation error with field details
                message = 'Validation failed.'
                details = exc.detail
            elif isinstance(exc.detail, list):
                message = '; '.join(str(d) for d in exc.detail)
                details = None
            else:
                message = str(exc.detail)
                details = None
        else:
            message = str(exc)
            details = None
        
        # Build response
        error_data = {
            'error': error_code,
            'message': message,
        }
        
        if details:
            error_data['details'] = details
        
        response.data = error_data
        
        # Log the error
        if response.status_code >= 500:
            logger.error(f"API Error [{error_code}]: {message}", exc_info=True)
        elif response.status_code >= 400:
            logger.warning(f"API Warning [{error_code}]: {message}")
    
    return response


class APIError(Exception):
    """
    Base exception for API errors with consistent formatting.
    
    Usage:
        raise APIError('ORDER_NOT_FOUND', 'The specified order was not found.', status.HTTP_404_NOT_FOUND)
    """
    
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
    
    def to_response(self) -> Response:
        """Convert exception to Response object."""
        data = {
            'error': self.code,
            'message': self.message,
        }
        if self.details:
            data['details'] = self.details
        return Response(data, status=self.status_code)


# Common API Errors
class NotFoundError(APIError):
    """Resource not found error."""
    def __init__(self, message: str = 'Resource not found.', details: dict = None):
        super().__init__('NOT_FOUND', message, status.HTTP_404_NOT_FOUND, details)


class PermissionDeniedError(APIError):
    """Permission denied error."""
    def __init__(self, message: str = 'You do not have permission to perform this action.', details: dict = None):
        super().__init__('PERMISSION_DENIED', message, status.HTTP_403_FORBIDDEN, details)


class ValidationError(APIError):
    """Validation error."""
    def __init__(self, message: str = 'Validation failed.', details: dict = None):
        super().__init__('VALIDATION_ERROR', message, status.HTTP_400_BAD_REQUEST, details)


class ConflictError(APIError):
    """Resource conflict error (409)."""
    def __init__(self, code: str, message: str, details: dict = None):
        super().__init__(code, message, status.HTTP_409_CONFLICT, details)


class OrderError(APIError):
    """Order-specific error."""
    pass


# Predefined order errors
class OrderNotFoundError(OrderError):
    def __init__(self):
        super().__init__('ORDER_NOT_FOUND', 'Order not found.', status.HTTP_404_NOT_FOUND)


class OrderAlreadyCompletedError(OrderError):
    def __init__(self):
        super().__init__('ORDER_ALREADY_COMPLETED', 'This order has already been completed.', status.HTTP_409_CONFLICT)


class InvalidStatusTransitionError(OrderError):
    def __init__(self, current: str, target: str):
        super().__init__(
            'INVALID_STATUS_TRANSITION',
            f'Cannot transition from {current} to {target}.',
            status.HTTP_400_BAD_REQUEST,
            {'current_status': current, 'target_status': target}
        )


class PaymentRequiredError(OrderError):
    def __init__(self):
        super().__init__('PAYMENT_REQUIRED', 'Payment must be collected before completing this order.', status.HTTP_402_PAYMENT_REQUIRED)


class CashCollectionNotAllowedError(OrderError):
    def __init__(self):
        super().__init__('CASH_COLLECTION_NOT_ALLOWED', 'You do not have permission to collect cash.', status.HTTP_403_FORBIDDEN)
