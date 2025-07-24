"""
Transaction Analytics API Endpoints
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.transaction_analytics import TransactionAnalyticsService

router = APIRouter()


@router.get("/stats")
async def get_transaction_stats(
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """트랜잭션 통계 조회"""
    try:
        analytics_service = TransactionAnalyticsService(db)

        # 기본값 설정
        if not start_date:
            start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if not end_date:
            end_date = datetime.now()

        stats = await analytics_service.get_transaction_stats(start_date, end_date)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/user-analytics")
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """사용자 분석 데이터 조회"""
    try:
        analytics_service = TransactionAnalyticsService(db)
        user_id: int = current_user.id  # type: ignore

        analytics = await analytics_service.get_user_analytics(user_id, days)
        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 분석 실패: {str(e)}")


@router.get("/anomalies")
async def detect_anomalies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """이상 거래 탐지"""
    try:
        analytics_service = TransactionAnalyticsService(db)

        # 기본 거래 데이터 (실제로는 더 복잡한 로직이 필요)
        transaction_data = {"user_id": current_user.id, "timestamp": datetime.now()}

        anomalies = await analytics_service.detect_anomalies(transaction_data)
        return {"anomalies": anomalies}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이상 거래 탐지 실패: {str(e)}")
