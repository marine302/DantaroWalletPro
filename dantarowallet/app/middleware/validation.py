"""
요청 검증 미들웨어.
API 요청의 크기, 형식, 내용을 검증합니다.
"""

import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    요청 크기 및 컨텐츠 타입 검증 미들웨어.
    악의적인 요청이나 너무 큰 요청을 차단합니다.
    """

    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):
        """
        미들웨어 초기화.

        Args:
            app: FastAPI 앱 인스턴스
            max_content_length: 허용되는 최대 요청 크기 (바이트 단위, 기본값 10MB)
        """
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next):
        """
        요청을 검증하고 처리합니다.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 엔드포인트 핸들러 호출 함수

        Returns:
            유효한 요청이면 다음 핸들러의 응답을, 그렇지 않으면 오류 응답을 반환
        """
        # Content-Length 체크
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "REQUEST_TOO_LARGE",
                    "message": "Request entity too large",
                    "max_size_bytes": self.max_content_length,
                },
            )

        # JSON 요청 검증
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body = await request.body()
                if body:  # 요청 본문이 비어있지 않은 경우만 검증
                    try:
                        json.loads(body)
                    except json.JSONDecodeError:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": "INVALID_JSON",
                                "message": "Invalid JSON format in request body",
                            },
                        )

        # 유효한 요청은 계속 처리
        response = await call_next(request)
        return response
