"""
관리자 인증 관련 API 엔드포인트
"""
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# 관리자 인증 헬퍼
async def get_current_admin(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """현재 관리자 사용자 가져오기"""
    admin_id = getattr(request.state, "admin_id", None)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(User).filter(User.id == int(admin_id)))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    return admin


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """관리자 로그인 페이지"""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """관리자 로그인 처리"""
    # 사용자 확인
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html", {"request": request, "error": "Invalid credentials"}
        )

    if not user.is_admin:
        return templates.TemplateResponse(
            "admin/login.html", {"request": request, "error": "Admin access required"}
        )

    # 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})

    # 대시보드로 리다이렉트
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )

    return response


@router.get("/logout")
async def admin_logout():
    """관리자 로그아웃"""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response
