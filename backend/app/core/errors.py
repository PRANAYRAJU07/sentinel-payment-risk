"""
Sentinel Backend — API Error Handling
Consistent, structured error responses. Never expose stack traces in production.
"""
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("errors")


def make_error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    status_code: int = 400,
) -> JSONResponse:
    """Create a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id or str(uuid.uuid4()),
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("validation_error", errors=exc.errors(), path=str(request.url))
    return make_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    settings = get_settings()
    request_id = str(uuid.uuid4())
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        path=str(request.url),
        error=str(exc),
        exc_info=True,
    )

    if settings.app_debug:
        # Return details in debug mode
        return make_error_response(
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(exc)}",
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    else:
        # Never expose exception details in production
        return make_error_response(
            code="INTERNAL_ERROR",
            message="An internal error occurred. Please try again.",
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class SentinelException(Exception):
    """Base exception for Sentinel-specific errors."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def sentinel_exception_handler(
    request: Request, exc: SentinelException
) -> JSONResponse:
    logger.warning(
        "sentinel_error",
        code=exc.code,
        message=exc.message,
        path=str(request.url),
    )
    return make_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )
