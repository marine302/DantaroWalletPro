"""
대시보드 관련 비즈니스 로직
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from app.models.balance import Balance
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.dashboard import (
    BalanceHistoryResponse,
    DashboardOverview,
    RecentTransactionResponse,
    WalletStatsResponse,
)
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_overview(self, user_id: int) -> DashboardOverview:
        """사용자 대시보드 개요 정보 조회"""

        # 총 잔고 계산
        balance_result = await self.db.execute(
            select(func.sum(Balance.amount)).filter(Balance.user_id == user_id)
        )
        total_balance = balance_result.scalar() or Decimal("0")

        # 총 지갑 수
        wallet_result = await self.db.execute(
            select(func.count(Wallet.id)).filter(
                Wallet.user_id == user_id, Wallet.is_active == True
            )
        )
        total_wallets = wallet_result.scalar() or 0

        # 총 거래 수
        transaction_result = await self.db.execute(
            select(func.count(Transaction.id)).filter(Transaction.user_id == user_id)
        )
        total_transactions = transaction_result.scalar() or 0

        # 대기 중인 거래 수
        pending_result = await self.db.execute(
            select(func.count(Transaction.id)).filter(
                Transaction.user_id == user_id, Transaction.status == "pending"
            )
        )
        pending_transactions = pending_result.scalar() or 0

        # 마지막 거래 날짜
        last_tx_result = await self.db.execute(
            select(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(1)
        )
        last_transaction = last_tx_result.scalar_one_or_none()
        last_transaction_date = safe_datetime(
            safe_get_attr(last_transaction, 'created_at') if last_transaction else None
        )

        # 월간 거래량
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        monthly_result = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= month_start,
                Transaction.status == "completed",
            )
        )
        monthly_volume = monthly_result.scalar() or Decimal("0")

        return DashboardOverview(
            total_balance=total_balance,
            total_wallets=total_wallets,
            total_transactions=total_transactions,
            pending_transactions=pending_transactions,
            last_transaction_date=last_transaction_date,
            monthly_volume=monthly_volume,
        )

    async def get_recent_transactions(
        self, user_id: int, limit: int = 10
    ) -> List[RecentTransactionResponse]:
        """최근 거래 내역 조회"""

        result = await self.db.execute(
            select(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        transactions = result.scalars().all()

        return [
            RecentTransactionResponse(
                id=safe_int(tx.id),
                transaction_type=str(safe_get_attr(tx, 'type', '')),
                amount=safe_decimal(tx.amount),
                currency=getattr(tx, "currency", "TRX") or "TRX",
                status=str(safe_get_attr(tx, 'status', '')),
                created_at=safe_datetime(tx.created_at, datetime.now()),
                wallet_address=getattr(tx, "to_address", "")
                or getattr(tx, "from_address", "")
                or "",
            )
            for tx in transactions
        ]

    async def get_balance_history(
        self, user_id: int, days: int = 30
    ) -> List[BalanceHistoryResponse]:
        """잔고 변화 이력 조회"""

        start_date = datetime.now() - timedelta(days=days)

        # 일별 잔고 변화 계산
        result = await self.db.execute(
            select(
                func.date(Balance.created_at).label("date"),
                func.sum(Balance.amount).label("balance"),
            )
            .filter(Balance.user_id == user_id, Balance.created_at >= start_date)
            .group_by(func.date(Balance.created_at))
            .order_by("date")
        )
        balance_history = result.all()

        response = []
        previous_balance = Decimal("0")

        for record in balance_history:
            current_balance = record.balance or Decimal("0")
            change = current_balance - previous_balance

            response.append(
                BalanceHistoryResponse(
                    date=record.date, balance=current_balance, change=change
                )
            )

            previous_balance = current_balance

        return response

    async def get_wallet_stats(self, user_id: int) -> WalletStatsResponse:
        """지갑 통계 정보 조회"""

        # 활성 지갑 수
        active_result = await self.db.execute(
            select(func.count(Wallet.id)).filter(
                Wallet.user_id == user_id, Wallet.is_active == True
            )
        )
        active_wallets = active_result.scalar() or 0

        # 비활성 지갑 수
        inactive_result = await self.db.execute(
            select(func.count(Wallet.id)).filter(
                Wallet.user_id == user_id, Wallet.is_active == False
            )
        )
        inactive_wallets = inactive_result.scalar() or 0

        # 총 받은 금액
        received_result = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.direction == "in",
                Transaction.status == "completed",
            )
        )
        total_received = received_result.scalar() or Decimal("0")

        # 총 보낸 금액
        sent_result = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.direction == "out",
                Transaction.status == "completed",
            )
        )
        total_sent = sent_result.scalar() or Decimal("0")

        # 평균 잔고
        avg_result = await self.db.execute(
            select(func.avg(Balance.amount)).filter(Balance.user_id == user_id)
        )
        average_balance = avg_result.scalar() or Decimal("0")

        # 지갑 분포
        wallet_distribution = [
            {"type": "active", "count": active_wallets},
            {"type": "inactive", "count": inactive_wallets},
        ]

        return WalletStatsResponse(
            active_wallets=active_wallets,
            inactive_wallets=inactive_wallets,
            total_received=total_received,
            total_sent=total_sent,
            average_balance=average_balance,
            wallet_distribution=wallet_distribution,
        )


def safe_get_attr(obj, attr, default=None):
    """SQLAlchemy 컬럼 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default
    
    value = getattr(obj, attr, default)
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if value is not None and hasattr(value, 'value'):
        return value.value
    else:
        return value


def safe_int(value, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_decimal(value, default=None):
    """안전한 Decimal 변환"""
    if value is None:
        return default or Decimal("0")
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return default or Decimal("0")


def safe_datetime(value, default=None):
    """안전한 datetime 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    # 이미 datetime이면 그대로 반환
    from datetime import datetime
    if isinstance(value, datetime):
        return value
    
    return default
