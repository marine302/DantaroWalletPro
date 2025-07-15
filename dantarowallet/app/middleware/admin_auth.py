from app.core.config import settings
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """관리자 페이지 인증 미들웨어"""

    def __init__(self, app, admin_paths: list):
        super().__init__(app)
        self.admin_paths = admin_paths

    async def dispatch(self, request: Request, call_next):
        # 관리자 경로인지 확인
        if not any(request.url.path.startswith(path) for path in self.admin_paths):
            return await call_next(request)

        # API 엔드포인트는 제외 (이미 API 레벨에서 인증 처리)
        if "/api/v1/" in request.url.path:
            return await call_next(request)

        # 로그인 페이지는 제외
        if request.url.path.endswith("/login"):
            return await call_next(request)

        # 쿠키에서 토큰 확인
        token = request.cookies.get("admin_token")
        if not token:
            return RedirectResponse(url="/admin/login", status_code=302)

        # 토큰 검증
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if not payload:
                return RedirectResponse(url="/admin/login", status_code=302)
        except JWTError:
            return RedirectResponse(url="/admin/login", status_code=302)

        # request에 사용자 정보 추가
        request.state.admin_id = payload.get("sub")
        request.state.is_admin = True

        response = await call_next(request)
        return response
