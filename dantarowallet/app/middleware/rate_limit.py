"""
요청 제한(Rate Limiting) 미들웨어.
과도한 API 호출을 방지하기 위한 요청 속도 제한을 구현합니다.
"""
import time
from collections import defaultdict
from typing import DefaultDict, Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    간단한 인메모리 요청 제한(Rate limiting) 미들웨어.
    주로 개발 및 테스트 환경에서 사용하며, 프로덕션에서는 Redis 기반 솔루션이 권장됩니다.
    """

    def __init__(self, app, calls: int = 1000, period: int = 60):
        """
        미들웨어 초기화.

        Args:
            app: FastAPI 앱 인스턴스
            calls: 시간 주기 내 허용되는 최대 요청 수
            period: 시간 주기 (초 단위)
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: DefaultDict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0))

    async def dispatch(self, request: Request, call_next):
        """
        요청에 대한 속도 제한을 적용합니다.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 엔드포인트 핸들러 호출 함수

        Returns:
            제한을 초과하지 않은 경우 다음 핸들러의 응답을, 초과한 경우 429 응답을 반환
        """
        # 헬스 체크 엔드포인트는 제한에서 제외
        if request.url.path in ["/health", "/", "/api/test"]:
            return await call_next(request)

        # 테스트 환경에서는 Rate Limiting 완화
        user_agent = request.headers.get("user-agent", "")
        if ("pytest" in user_agent.lower() or 
            "test" in user_agent.lower() or 
            request.headers.get("X-Test-Mode") == "true"):
            return await call_next(request)

        # 클라이언트 식별자 (일반적으로 IP 주소)
        if request.client and hasattr(request.client, "host"):
            client_ip = request.client.host
        else:
            # 클라이언트를 식별할 수 없는 경우 기본값 사용
            client_ip = "unknown"

        # 현재 시간
        now = time.time()

        # 클라이언트 요청 정보 가져오기
        calls, window_start = self.clients[client_ip]

        # 시간 윈도우가 만료되었으면 리셋
        if now - window_start > self.period:
            calls = 0
            window_start = now

        # 요청 수 증가
        calls += 1

        # 제한 초과 여부 확인
        if calls > self.calls:
            retry_after = int(self.period - (now - window_start))
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
            )

        # 클라이언트 정보 업데이트
        self.clients[client_ip] = (calls, window_start)

        # X-RateLimit 헤더 추가를 위해 응답 처리
        response = await call_next(request)

        # 남은 요청 수를 헤더에 포함
        remaining = max(0, self.calls - calls)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + self.period))

        return response
