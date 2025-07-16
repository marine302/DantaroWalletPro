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
        # API 엔드포인트는 모두 인증 제외
        if "/api/" in request.url.path:
            return await call_next(request)
            
        # 정적 파일 제외
        if any(request.url.path.startswith(path) for path in ["/static/", "/assets/", "/favicon"]):
            return await call_next(request)
            
        # 관리자 경로가 아니면 통과
        if not any(request.url.path.startswith(path) for path in self.admin_paths):
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
