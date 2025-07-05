"""
관리자 대시보드 메인 페이지
"""
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.deposit import Deposit
from app.models.transaction import Transaction
from app.models.user import User
from app.models.withdrawal import Withdrawal
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_dashboard_stats(db: AsyncSession):
    """대시보드 통계 데이터 조회"""
    # 사용자 통계
    user_count = await db.scalar(select(func.count(User.id)))
    
    # 24시간 내 트랜잭션
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_transactions = await db.scalar(
        select(func.count(Transaction.id)).filter(
            Transaction.created_at >= yesterday
        )
    )
    
    # 대기 중인 출금
    pending_withdrawals = await db.scalar(
        select(func.count(Withdrawal.id)).filter(
            Withdrawal.status == "pending"
        )
    )
    
    return {
        "total_users": user_count or 0,
        "recent_transactions": recent_transactions or 0,
        "pending_withdrawals": pending_withdrawals or 0,
    }


async def get_recent_activities(db: AsyncSession, limit: int = 10):
    """최근 활동 조회"""
    activities = []
    
    # 최근 트랜잭션
    result = await db.execute(
        select(Transaction)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    for tx in transactions:
        activities.append({
            "type": "transaction",
            "message": f"Transaction {tx.tx_hash[:10]}... - {tx.status}",
            "timestamp": tx.created_at,
        })
    
    # 시간순 정렬
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자 대시보드 메인"""
    # 통계 수집
    stats = await get_dashboard_stats(db)

    # 최근 활동
    recent_activities = await get_recent_activities(db)

    # 시스템 상태 (간단한 더미 데이터)
    health_status = {
        "status": "healthy",
        "checks": {
            "database": {"status": "healthy", "message": "Connection OK"},
            "redis": {"status": "healthy", "message": "Connected"},
            "tron": {"status": "healthy", "message": "Network OK"},
        },
    }

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "activities": recent_activities,
            "health": health_status,
        },
    )
