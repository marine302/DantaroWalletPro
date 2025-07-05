import time

from app.core.logging import setup_logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = setup_logging()


class RequestIdAndLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(time.time_ns()))
        request.state.request_id = request_id
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
            extra={"request_id": request_id},
        )
        return response
