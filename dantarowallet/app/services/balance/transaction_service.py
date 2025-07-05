"""
잔고 트랜잭션 서비스
트랜잭션 내역 조회 및 잔고 증가 등의 기능을 제공합니다.
"""
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.exceptions import ValidationError
from app.models.balance import Balance
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.services.balance.base_service import BaseBalanceService
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BalanceTransactionService(BaseBalanceService):
    """잔고 트랜잭션 서비스"""

    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        tx_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> List[Transaction]:
        """트랜잭션 내역 조회"""
        query = select(Transaction).filter(Transaction.user_id == user_id)

        if tx_type:
            query = query.filter(Transaction.type == tx_type)

        if status:
            query = query.filter(Transaction.status == status)

        query = query.order_by(Transaction.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_balance(
        self,
        user_id: int,
        asset: str,
        amount: Decimal,
        transaction_type: str = "deposit",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """잔고 증가 처리"""

        # 금액 검증
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        # 트랜잭션 시작
        async with self.db.begin_nested():
            # 사용자 잔고 조회 또는 생성
            balance = await self.get_or_create_balance(user_id, asset)

            # 잔고 업데이트 (FOR UPDATE로 락)
            balance_result = await self.db.execute(
                select(Balance)
                .filter(and_(Balance.user_id == user_id, Balance.asset == asset))
                .with_for_update()
            )
            balance = balance_result.scalar_one()

            # 이전 잔고
            previous_amount = balance.amount

            # 잔고 증가 (update 쿼리 사용)
            await self.db.execute(
                balance.__class__.__table__.update()
                .where(and_(Balance.user_id == user_id, Balance.asset == asset))
                .values(amount=Balance.amount + amount, updated_at=func.now())
            )

            # 새 잔고 조회
            new_balance_result = await self.db.execute(
                select(Balance).filter(
                    and_(Balance.user_id == user_id, Balance.asset == asset)
                )
            )
            new_balance = new_balance_result.scalar_one()

            # 트랜잭션 기록 생성
            transaction = Transaction(
                user_id=user_id,
                type=TransactionType.DEPOSIT
                if transaction_type == "deposit"
                else TransactionType.BONUS,
                direction=TransactionDirection.IN,
                asset=asset,
                amount=amount,
                status=TransactionStatus.COMPLETED,
                description=description
                or f"{transaction_type.title()}: {amount} {asset}",
                transaction_metadata=json.dumps(
                    {
                        "previous_balance": str(previous_amount),
                        "new_balance": str(new_balance.amount),
                        "transaction_type": transaction_type,
                    }
                ),
            )

            self.db.add(transaction)

            # 변경사항 플러시
            await self.db.flush()

            logger.info(f"잔고 증가: 사용자 {user_id}, {amount} {asset}")

            return {
                "user_id": user_id,
                "asset": asset,
                "amount": str(amount),
                "previous_balance": str(previous_amount),
                "new_balance": str(new_balance.amount),
                "transaction_id": transaction.id,
            }
