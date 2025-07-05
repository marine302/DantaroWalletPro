"""
웹 인증 유틸리티 함수들.
JWT 토큰 기반 웹 페이지 인증을 처리합니다.
"""
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user_from_request(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    요청에서 현재 사용자를 가져옵니다.
    Authorization 헤더 또는 쿠키에서 토큰을 확인합니다.
    """
    token = None

    # 1. Authorization 헤더에서 토큰 확인
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. 쿠키에서 토큰 확인
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    # 토큰 검증
    payload = verify_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # 사용자 조회
    result = await db.execute(select(User).filter(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    return user


def require_auth(redirect_url: str = "/auth/login"):
    """
    인증이 필요한 웹 페이지를 위한 데코레이터 의존성.
    인증되지 않은 사용자는 로그인 페이지로 리디렉션합니다.
    """

    async def dependency(request: Request, db: AsyncSession = Depends(get_db)) -> User:
        user = await get_current_user_from_request(request, db)
        if not user:
            raise HTTPException(
                status_code=302,
                detail="Authentication required",
                headers={"Location": redirect_url},
            )
        return user

    return dependency


async def optional_auth(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    선택적 인증. 인증되지 않아도 페이지 접근 가능.
    """
    return await get_current_user_from_request(request, db)
