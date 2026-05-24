from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, code: str = "ERROR"
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND, code="NOT_FOUND")


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, status.HTTP_409_CONFLICT, code="CONFLICT")


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN, code="FORBIDDEN")


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, code="VALIDATION_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": {},
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)

        details = {}
        # Include traceback in details only in development mode
        try:
            from app.core.config import settings
            if settings.debug:
                details["traceback"] = traceback.format_exc()
                details["exception_type"] = exc.__class__.__name__
        except (ImportError, AttributeError):
            pass

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal server error occurred",
                    "details": details,
                }
            },
        )
