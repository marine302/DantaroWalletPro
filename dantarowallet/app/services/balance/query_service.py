"""
잔고 조회 서비스
사용자 잔고 조회 및 요약 정보 기능을 제공합니다.
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List

from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionDirection, TransactionStatus
from app.services.balance.base_service import BaseBalanceService
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BalanceQueryService(BaseBalanceService):
    """잔고 조회 서비스"""

    async def get_balance_summary(self, user_id: int) -> Dict[str, Any]:
        """잔고 요약 정보"""
        # 모든 잔고 조회
        result = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id)
        )
        balances = result.scalars().all()

        # 최근 트랜잭션
        recent_txs = await self._get_recent_transactions(user_id, limit=10)

        # 통계 계산
        total_in = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.direction == TransactionDirection.IN,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        total_in = total_in.scalar() or Decimal("0")

        total_out = await self.db.execute(
            select(func.sum(Transaction.amount + Transaction.fee)).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.direction == TransactionDirection.OUT,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        total_out = total_out.scalar() or Decimal("0")

        return {
            "balances": [
                {
                    "asset": b.asset,
                    "amount": str(b.amount),
                    "locked_amount": str(b.locked_amount),
                    "available_amount": str(b.available_amount),
                }
                for b in balances
            ],
            "recent_transactions": recent_txs,
            "statistics": {
                "total_received": str(total_in),
                "total_sent": str(total_out),
                "net_flow": str(total_in - total_out),
            },
        }

    async def _get_recent_transactions(
        self, user_id: int, limit: int = 10
    ) -> List[Transaction]:
        """최근 트랜잭션 내역 조회"""
        query = select(Transaction).filter(Transaction.user_id == user_id)
        query = query.order_by(Transaction.created_at.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_balances(self, user_id: int) -> List[Balance]:
        """사용자의 모든 자산 잔고 조회"""
        result = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id)
        )
        return result.scalars().all()
