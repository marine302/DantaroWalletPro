"""
시스템 관리 관련 API 엔드포인트
"""
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.deposit import Deposit
from app.models.transaction import Transaction
from app.models.user import User
from app.models.withdrawal import Withdrawal
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/system", response_class=HTMLResponse)
async def admin_system(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """시스템 관리 페이지"""
    # 시스템 통계
    stats = await _get_system_stats(db)
    
    # 시스템 상태
    health_status = {
        "status": "healthy",
        "checks": {
            "database": {"status": "healthy", "message": "Connection OK"},
            "redis": {"status": "warning", "message": "High memory usage"},
            "tron": {"status": "healthy", "message": "Network OK"},
            "disk": {"status": "healthy", "message": "85% used"},
        },
    }

    return templates.TemplateResponse(
        "admin/system.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "health": health_status,
        },
    )


@router.get("/withdrawals", response_class=HTMLResponse)
async def admin_withdrawals(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """출금 관리 페이지"""
    # 대기 중인 출금 목록
    result = await db.execute(
        select(Withdrawal)
        .filter(Withdrawal.status == "pending")
        .order_by(desc(Withdrawal.created_at))
        .limit(50)
    )
    pending_withdrawals = result.scalars().all()

    return templates.TemplateResponse(
        "admin/withdrawals.html",
        {
            "request": request,
            "admin": admin,
            "withdrawals": pending_withdrawals,
        },
    )


@router.post("/emergency-stop")
async def emergency_stop(
    admin: User = Depends(get_current_admin),
):
    """긴급 정지"""
    # 실제 구현에서는 Redis나 다른 캐시를 사용하여
    # 모든 서비스에 긴급 정지 신호를 보내야 함
    
    # 임시로 리다이렉트만 처리
    return RedirectResponse(url="/admin/system", status_code=302)


async def _get_system_stats(db: AsyncSession):
    """시스템 통계 수집"""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    # 24시간 통계
    daily_deposits = await db.scalar(
        select(func.count(Deposit.id)).filter(
            Deposit.created_at >= yesterday
        )
    )
    
    daily_withdrawals = await db.scalar(
        select(func.count(Withdrawal.id)).filter(
            Withdrawal.created_at >= yesterday
        )
    )
    
    daily_transactions = await db.scalar(
        select(func.count(Transaction.id)).filter(
            Transaction.created_at >= yesterday
        )
    )
    
    return {
        "daily_deposits": daily_deposits or 0,
        "daily_withdrawals": daily_withdrawals or 0,
        "daily_transactions": daily_transactions or 0,
        "uptime": "99.9%",  # 임시 데이터
        "memory_usage": "1.2GB",  # 임시 데이터
        "disk_usage": "85%",  # 임시 데이터
    }
