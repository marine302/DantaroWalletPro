"""
인증 관련 웹 페이지 라우터.
로그인, 회원가입 등의 웹 페이지를 제공합니다.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """회원가입 페이지"""
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.get("/logout")
async def logout_page():
    """로그아웃 처리"""
    from fastapi.responses import RedirectResponse

    response = RedirectResponse(url="/auth/login")
    response.delete_cookie("access_token")
    return response
