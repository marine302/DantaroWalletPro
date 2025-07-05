"""
수수료 설정 관리 API 엔드포인트
"""
from decimal import Decimal

from app.core.database import get_db
from app.models.fee_config import FeeConfig
from app.models.user import User
from app.services.fee_service import FeeService
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/fees", response_class=HTMLResponse)
async def admin_fees(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """수수료 설정 관리 페이지"""
    # 현재 수수료 설정 조회
    result = await db.execute(
        select(FeeConfig).filter(FeeConfig.is_active == True)
    )
    fee_configs = result.scalars().all()

    # 서비스별 분류
    fees_by_service = {}
    for config in fee_configs:
        service = config.service_type
        if service not in fees_by_service:
            fees_by_service[service] = []
        fees_by_service[service].append(config)

    return templates.TemplateResponse(
        "admin/fees.html",
        {
            "request": request,
            "admin": admin,
            "fees_by_service": fees_by_service,
        },
    )


@router.post("/fees/create")
async def create_fee_config(
    service_type: str = Form(...),
    fee_type: str = Form(...),
    fee_value: Decimal = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """새 수수료 설정 생성"""
    try:
        fee_service = FeeService(db)
        
        await fee_service.create_fee_config(
            service_type=service_type,
            fee_type=fee_type,
            fee_value=fee_value,
        )

        return RedirectResponse(url="/admin/fees", status_code=302)

    except Exception as e:
        # 에러 처리 (실제로는 더 세밀한 에러 처리 필요)
        return RedirectResponse(url="/admin/fees?error=creation_failed", status_code=302)
