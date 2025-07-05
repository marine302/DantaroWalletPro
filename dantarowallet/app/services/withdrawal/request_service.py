"""
출금 요청 서비스
출금 요청 생성, 취소 등의 기능을 제공합니다.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.services.withdrawal.validation_service import WithdrawalValidationService
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WithdrawalRequestService(WithdrawalValidationService):
    """출금 요청 서비스"""

    async def create_withdrawal_request(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal,
        asset: str = "USDT",
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Withdrawal:
        """출금 요청 생성"""

        # 검증
        await self.validate_withdrawal_request(user_id, to_address, amount, asset)

        # 잔고 잠금
        total_amount = amount + self.withdrawal_fee
        await self.balance_service.lock_amount(
            user_id=user_id, asset=asset, amount=total_amount
        )

        # 출금 요청 생성
        withdrawal = Withdrawal(
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            fee=self.withdrawal_fee,
            net_amount=amount,  # 수신자가 받을 금액
            asset=asset,
            status=WithdrawalStatus.PENDING,
            priority=self._determine_priority(amount),
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(withdrawal)
        await self.db.flush()

        # 트랜잭션 기록
        tx = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL,
            direction=TransactionDirection.OUT,
            status=TransactionStatus.PENDING,
            asset=asset,
            amount=amount,
            fee=self.withdrawal_fee,
            reference_id=f"WD-{withdrawal.id}",
            description=f"출금 요청: {to_address[:8]}...{to_address[-6:]}",
        )

        self.db.add(tx)
        await self.db.flush()

        logger.info(f"출금 요청 생성: ID {withdrawal.id}, 사용자 {user_id}, 금액 {amount} {asset}")

        return withdrawal

    async def cancel_withdrawal(self, withdrawal_id: int, user_id: int) -> Withdrawal:
        """출금 취소 (사용자)"""
        result = await self.db.execute(
            select(Withdrawal).filter(
                and_(Withdrawal.id == withdrawal_id, Withdrawal.user_id == user_id)
            )
        )
        withdrawal = result.scalar_one_or_none()

        if not withdrawal:
            raise NotFoundError("출금 요청을 찾을 수 없습니다")

        if not withdrawal.can_cancel():
            raise ValidationError(f"{withdrawal.status} 상태의 출금은 취소할 수 없습니다")

        # 상태 업데이트
        withdrawal.status = WithdrawalStatus.CANCELLED.value

        # 잔고 잠금 해제
        asset_str = (
            str(withdrawal.asset)
            if hasattr(withdrawal.asset, "value")
            else withdrawal.asset
        )
        total_amount = Decimal(str(withdrawal.total_amount))

        await self.balance_service.unlock_amount(
            user_id=user_id, asset=asset_str, amount=total_amount
        )

        # 트랜잭션 상태 업데이트
        tx_query = select(Transaction).filter(
            Transaction.reference_id == f"WD-{withdrawal.id}"
        )
        tx_result = await self.db.execute(tx_query)
        transaction = tx_result.scalar_one_or_none()
        if transaction:
            transaction.status = TransactionStatus.CANCELLED.value

        logger.info(f"출금 취소: ID {withdrawal_id}, 사용자 {user_id}")

        return withdrawal
