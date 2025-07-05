"""
트랜잭션 내역/통계 관련 기능 분리 모듈
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.balance import Balance
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class BalanceHistory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        tx_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> List[Transaction]:
        query = select(Transaction).filter(Transaction.user_id == user_id)
        if tx_type:
            query = query.filter(Transaction.type == tx_type)
        if status:
            query = query.filter(Transaction.status == status)
        query = (
            query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_balance_summary(self, user_id: int) -> Dict[str, Any]:
        result = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id)
        )
        balances = result.scalars().all()
        # ...existing code for statistics and recent transactions...
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
            # ...recent_transactions, statistics 등 추가...
        }
