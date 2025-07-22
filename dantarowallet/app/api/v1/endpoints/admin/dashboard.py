"""
슈퍼 어드민 통합 대시보드 API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.partner import Partner
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.energy_pool import EnergyPoolModel
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin/dashboard", tags=["Super Admin Dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db)
):
    """대시보드 개요 조회"""
    try:
        # 전체 사용자 수
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        # 전체 파트너 수
        total_partners_result = await db.execute(select(func.count(Partner.id)))
        total_partners = total_partners_result.scalar() or 0
        
        # 전체 지갑 수
        total_wallets_result = await db.execute(select(func.count(Wallet.id)))
        total_wallets = total_wallets_result.scalar() or 0
        
        # 최근 24시간 거래 수
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_tx_result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.created_at >= yesterday)
        )
        recent_transactions = recent_tx_result.scalar() or 0
        
        # 최근 24시간 거래 금액
        recent_volume_result = await db.execute(
            select(func.sum(Transaction.amount)).where(Transaction.created_at >= yesterday)
        )
        recent_volume = float(recent_volume_result.scalar() or 0)
        
        return {
            "success": True,
            "data": {
                "total_users": total_users,
                "total_partners": total_partners,
                "total_wallets": total_wallets,
                "recent_transactions": recent_transactions,
                "recent_volume": recent_volume,
                "system_status": "operational",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health")
async def get_system_health(
    db: AsyncSession = Depends(get_db)
):
    """시스템 건강도 조회"""
    try:
        # 데이터베이스 연결 테스트
        db_health = True
        try:
            await db.execute(select(1))
        except Exception:
            db_health = False
        
        # 활성 파트너 수 (is_active 필드 대신 status 사용)
        active_partners_result = await db.execute(
            select(func.count(Partner.id)).where(Partner.status == "active")
        )
        active_partners = active_partners_result.scalar() or 0
        
        # 최근 1시간 거래 수 (활성도 지표)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_activity_result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.created_at >= one_hour_ago)
        )
        recent_activity = recent_activity_result.scalar() or 0
        
        # 전체 건강도 점수 계산
        health_score = 100
        if not db_health:
            health_score -= 50
        if active_partners == 0:
            health_score -= 20
        if recent_activity == 0:
            health_score -= 10
            
        status = "healthy"
        if health_score < 70:
            status = "warning"
        if health_score < 50:
            status = "critical"
        
        return {
            "success": True,
            "data": {
                "overall_health": health_score,
                "status": status,
                "components": {
                    "database": {"status": "healthy" if db_health else "error", "score": 100 if db_health else 0},
                    "partners": {"active_count": active_partners, "score": min(100, active_partners * 10)},
                    "activity": {"recent_transactions": recent_activity, "score": min(100, recent_activity * 5)}
                },
                "last_checked": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"System health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partner-rankings")
async def get_partner_rankings(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """파트너 순위 조회"""
    try:
        # 파트너별 거래량 순위 (최근 30일)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 파트너별 거래 통계 서브쿼리
        partner_stats = await db.execute(
            select(
                Partner.id,
                Partner.name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_volume')
            )
            .join(User, Partner.id == User.partner_id)
            .join(Wallet, User.id == Wallet.user_id)
            .join(Transaction, Wallet.address == Transaction.from_address)
            .where(Transaction.created_at >= thirty_days_ago)
            .group_by(Partner.id, Partner.name)
            .order_by(desc('total_volume'))
            .limit(limit)
        )
        
        rankings = []
        for row in partner_stats:
            rankings.append({
                "partner_id": row.id,
                "partner_name": row.name,
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume or 0),
                "rank": len(rankings) + 1
            })
        
        return {
            "success": True,
            "data": {
                "rankings": rankings,
                "period": "30_days",
                "total_partners": len(rankings),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Partner rankings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue-stats")
async def get_revenue_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """수익 통계 조회"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 총 거래 수수료 (예상)
        total_fees_result = await db.execute(
            select(func.sum(Transaction.amount * 0.001))  # 0.1% 수수료 가정
            .where(Transaction.created_at >= start_date)
        )
        total_fees = float(total_fees_result.scalar() or 0)
        
        # 일별 수익 통계
        daily_stats = await db.execute(
            select(
                func.date(Transaction.created_at).label('date'),
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('volume'),
                func.sum(Transaction.amount * 0.001).label('estimated_fees')
            )
            .where(Transaction.created_at >= start_date)
            .group_by(func.date(Transaction.created_at))
            .order_by('date')
        )
        
        daily_revenue = []
        for row in daily_stats:
            daily_revenue.append({
                "date": str(row.date),
                "transaction_count": row.transaction_count,
                "volume": float(row.volume or 0),
                "estimated_fees": float(row.estimated_fees or 0)
            })
        
        return {
            "success": True,
            "data": {
                "total_fees": total_fees,
                "period_days": days,
                "daily_revenue": daily_revenue,
                "average_daily_fees": total_fees / days if days > 0 else 0,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Revenue stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
