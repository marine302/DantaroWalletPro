from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DantaroException
from app.core.logging import setup_logging

logger = setup_logging()


async def dantaro_exception_handler(request: Request, exc: DantaroException):
    logger.warning(
        f"Business exception: {exc.error_code} - {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details if exc.details else None,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None),
        },
    )
