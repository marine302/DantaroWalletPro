"""
대시보드 API 엔드포인트
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import (
    BalanceHistoryResponse,
    DashboardOverview,
    RecentTransactionResponse,
    WalletStatsResponse,
)
from app.services.dashboard_service import DashboardService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 대시보드 개요 정보 조회"""
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_user_overview(current_user.id)


@router.get("/recent-transactions", response_model=List[RecentTransactionResponse])
async def get_recent_transactions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """최근 거래 내역 조회"""
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_recent_transactions(current_user.id, limit)


@router.get("/balance-history", response_model=List[BalanceHistoryResponse])
async def get_balance_history(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """잔고 변화 이력 조회"""
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_balance_history(current_user.id, days)


@router.get("/wallet-stats", response_model=WalletStatsResponse)
async def get_wallet_stats(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """지갑 통계 정보 조회"""
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_wallet_stats(current_user.id)
