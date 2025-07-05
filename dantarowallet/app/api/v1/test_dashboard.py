"""
간단한 대시보드 테스트 라우터
"""
from app.core.database import get_db
from app.core.web_auth import require_auth
from app.models.user import User
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/test", response_class=HTMLResponse)
async def test_dashboard_page(
    request: Request, current_user: User = Depends(require_auth())
):
    """간단한 테스트 대시보드 페이지"""
    return templates.TemplateResponse(
        "test_dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "message": "로그인 성공! 대시보드가 정상 작동합니다.",
        },
    )
