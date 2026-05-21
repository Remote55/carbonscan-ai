"""Custom application exceptions with structured error responses."""

from typing import Any


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    error_code: str = "InternalError"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if message:
            self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    error_code = "NotFound"
    message = "Resource not found"


class UnauthorizedError(AppException):
    status_code = 401
    error_code = "Unauthorized"
    message = "Authentication required"


class ForbiddenError(AppException):
    status_code = 403
    error_code = "Forbidden"
    message = "Insufficient permissions"


class ValidationError(AppException):
    status_code = 400
    error_code = "ValidationError"
    message = "Invalid input"


class ConflictError(AppException):
    status_code = 409
    error_code = "Conflict"
    message = "Resource conflict"


class PayloadTooLargeError(AppException):
    status_code = 413
    error_code = "PayloadTooLarge"
    message = "Upload exceeds maximum size"


class RateLimitError(AppException):
    status_code = 429
    error_code = "RateLimitExceeded"
    message = "Rate limit exceeded"


class ExternalServiceError(AppException):
    status_code = 503
    error_code = "ExternalServiceUnavailable"
    message = "External service unavailable"
