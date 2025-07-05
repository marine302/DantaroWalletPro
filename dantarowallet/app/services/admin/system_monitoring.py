"""
시스템 모니터링 서비스.
시스템 전체 통계 및 위험도 분석을 담당합니다.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.admin import SystemStatsResponse, SystemRiskSummaryResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class SystemMonitoringService:
    """시스템 모니터링 서비스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_stats(self) -> SystemStatsResponse:
        """시스템 전체 통계 조회"""

        # 총 사용자 수
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        # 활성 사용자 수
        active_users_result = await self.db.execute(
            select(func.count(User.id)).filter(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0

        # 총 지갑 수
        total_wallets_result = await self.db.execute(select(func.count(Wallet.id)))
        total_wallets = total_wallets_result.scalar() or 0

        # 총 거래 수
        total_transactions_result = await self.db.execute(
            select(func.count(Transaction.id))
        )
        total_transactions = total_transactions_result.scalar() or 0

        # 시스템 총 잔고
        total_balance_result = await self.db.execute(select(func.sum(Balance.amount)))
        total_balance = total_balance_result.scalar() or Decimal("0")

        # 일일 거래 수 (24시간)
        day_ago = datetime.now() - timedelta(days=1)
        daily_transactions_result = await self.db.execute(
            select(func.count(Transaction.id)).filter(Transaction.created_at >= day_ago)
        )
        daily_transactions = daily_transactions_result.scalar() or 0

        # 월간 거래량 (30일)
        month_ago = datetime.now() - timedelta(days=30)
        monthly_volume_result = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                Transaction.created_at >= month_ago,
                Transaction.status == TransactionStatus.COMPLETED,
            )
        )
        monthly_volume = monthly_volume_result.scalar() or Decimal("0")

        return SystemStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_wallets=total_wallets,
            total_transactions=total_transactions,
            total_balance=total_balance,
            daily_transactions=daily_transactions,
            monthly_volume=monthly_volume,
        )

    async def get_system_risk_summary(self) -> SystemRiskSummaryResponse:
        """시스템 전체 위험도 요약"""
        # 기존 AdminService의 get_system_risk_summary 로직을 여기로 이동
        # 간단한 구현 예시
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        return SystemRiskSummaryResponse(
            high_risk_users=0,
            medium_risk_users=0,
            low_risk_users=total_users,
            total_users=total_users,
            updated_at=datetime.now()
        )
