from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
import logging
import traceback
from typing import Union

# Configure logger
logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling middleware."""
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP_ERROR",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path)
            }
        )
    
    @staticmethod
    async def validation_exception_handler(
        request: Request,
        exc: Union[RequestValidationError, PydanticValidationError]
    ) -> JSONResponse:
        """Handle request validation errors."""
        logger.warning(f"Validation error: {exc} - {request.url}")

        errors = []
        if hasattr(exc, 'errors'):
            for error in exc.errors():
                errors.append({
                    "field": " -> ".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
        else:
            errors.append({"message": str(exc)})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
                "path": str(request.url.path)
            }
        )
    
    @staticmethod
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle database errors."""
        logger.error(f"Database error: {exc} - {request.url}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "DATABASE_ERROR",
                "message": "Database operation failed",
                "details": "Please check your request and try again",
                "path": str(request.url.path)
            }
        )
    
    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error(f"Unhandled exception: {exc} - {request.url}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": "Please contact support if this persists",
                "path": str(request.url.path)
            }
        )
    
    @staticmethod
    async def custom_404_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle 404 errors with custom message."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "NOT_FOUND",
                "message": f"Endpoint not found: {request.url.path}",
                "details": "Please check the API documentation for available endpoints",
                "path": str(request.url.path)
            }
        )
    
    @staticmethod
    async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle rate limiting errors."""
        logger.warning(f"Rate limit exceeded: {request.client.host} - {request.url}")
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "details": "Please wait before making another request",
                "path": str(request.url.path)
            }
        )


def setup_error_handlers(app):
    """Setup error handlers for FastAPI application."""
    error_handler = ErrorHandler()

    # HTTP exceptions
    app.add_exception_handler(HTTPException, error_handler.http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, error_handler.validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, error_handler.validation_exception_handler)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, error_handler.sqlalchemy_exception_handler)

    # General exceptions (catch-all)
    app.add_exception_handler(Exception, error_handler.general_exception_handler)

    logger.info("Error handlers configured successfully")