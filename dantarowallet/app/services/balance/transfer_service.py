"""
잔고 이체 서비스
내부 이체 처리 기능을 제공합니다.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientBalanceError, NotFoundError, ValidationError
from app.models.balance import Balance
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.services.balance.base_service import BaseBalanceService

logger = logging.getLogger(__name__)


class BalanceTransferService(BaseBalanceService):
    """잔고 이체 서비스"""

    async def internal_transfer(
        self,
        sender_id: int,
        receiver_id: int,
        amount: Decimal,
        description: Optional[str] = None,
        asset: str = "USDT",
    ) -> Dict[str, Any]:
        """내부 이체 처리"""

        # 금액 검증
        if amount <= 0:
            raise ValidationError("Transfer amount must be positive")

        # 최소 금액 체크 (0.000001 USDT)
        if amount < Decimal("0.000001"):
            raise ValidationError("Amount too small")

        # 자기 자신에게 이체 방지
        if sender_id == receiver_id:
            raise ValidationError("Cannot transfer to yourself")

        # 트랜잭션 시작
        async with self.db.begin_nested():
            # 발신자 잔고 조회 (FOR UPDATE로 락)
            sender_balance = await self.db.execute(
                select(Balance)
                .filter(and_(Balance.user_id == sender_id, Balance.asset == asset))
                .with_for_update()
            )
            sender_balance = sender_balance.scalar_one_or_none()

            if not sender_balance:
                raise NotFoundError(f"Sender balance for {asset}")

            # 잔고 충분한지 확인
            if not sender_balance.can_withdraw(amount):
                raise InsufficientBalanceError(
                    required=float(amount),
                    available=float(sender_balance.available_amount),
                )

            # 수신자 잔고 조회 또는 생성
            receiver_balance = await self.get_or_create_balance(receiver_id, asset)

            # 잔고 업데이트
            sender_balance.amount -= amount
            receiver_balance.amount += amount

            # 트랜잭션 기록 생성
            reference_id = f"INT-{datetime.utcnow().timestamp()}"

            # 발신자 트랜잭션
            sender_tx = Transaction(
                user_id=sender_id,
                type=TransactionType.TRANSFER,
                direction=TransactionDirection.OUT,
                status=TransactionStatus.COMPLETED,
                asset=asset,
                amount=amount,
                fee=Decimal("0"),  # 내부 이체는 수수료 없음
                related_user_id=receiver_id,
                reference_id=f"{reference_id}-OUT",
                description=description or "Internal transfer",
            )

            # 수신자 트랜잭션
            receiver_tx = Transaction(
                user_id=receiver_id,
                type=TransactionType.TRANSFER,
                direction=TransactionDirection.IN,
                status=TransactionStatus.COMPLETED,
                asset=asset,
                amount=amount,
                fee=Decimal("0"),
                related_user_id=sender_id,
                reference_id=f"{reference_id}-IN",
                description=description or "Internal transfer received",
            )

            self.db.add(sender_tx)
            self.db.add(receiver_tx)

            await self.db.flush()

        # 커밋은 상위 레벨에서 처리
        logger.info(
            f"Internal transfer completed: {sender_id} -> {receiver_id}, "
            f"amount: {amount} {asset}"
        )

        return {
            "sender_balance": sender_balance.amount,
            "receiver_balance": receiver_balance.amount,
            "transaction_id": sender_tx.id,
            "reference_id": reference_id,
        }
