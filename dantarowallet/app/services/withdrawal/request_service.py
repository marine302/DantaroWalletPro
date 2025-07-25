"""
출금 요청 서비스
출금 요청 생성, 취소 등의 기능을 제공합니다.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.services.withdrawal.validation_service import WithdrawalValidationService

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

        # 에너지 필요량 계산 및 자동 할당
        await self._allocate_energy_for_withdrawal(user_id, asset, amount)

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

        logger.info(
            f"출금 요청 생성: ID {withdrawal.id}, 사용자 {user_id}, 금액 {amount} {asset}"
        )

        return withdrawal

    async def cancel_withwithdrawal(self, withdrawal_id: int, user_id: int) -> Withdrawal:
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
            raise ValidationError(
                f"{withdrawal.status} 상태의 출금은 취소할 수 없습니다"
            )

        # 상태 업데이트 - DB에서 직접 업데이트
        await self.db.execute(
            update(Withdrawal)
            .where(Withdrawal.id == withdrawal_id)
            .values(status="cancelled")
        )

        # 잔고 잠금 해제
        asset_str = str(getattr(withdrawal, "asset", "USDT"))
        total_amount = Decimal(str(getattr(withdrawal, "total_amount", 0)))

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
            # DB에서 직접 업데이트
            await self.db.execute(
                update(Transaction)
                .where(Transaction.id == transaction.id)
                .values(status="cancelled")
            )

        logger.info(f"출금 취소: ID {withdrawal_id}, 사용자 {user_id}")

        return withdrawal

    async def _allocate_energy_for_withdrawal(
        self, user_id: int, asset: str, amount: Decimal
    ) -> None:
        """출금을 위한 에너지 자동 할당"""
        try:
            # TRON 네트워크에서만 에너지가 필요
            if asset != "USDT":
                return

            # 사용자의 파트너 정보 조회
            from app.models.user import User
            from app.models.partner import Partner
            
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user or not user.partner_id:
                logger.warning(f"사용자 {user_id}의 파트너 정보를 찾을 수 없음")
                return

            # USDT 전송에 필요한 에너지 계산 (약 13,000 에너지)
            required_energy = 13000
            
            # TODO: 에너지 할당 로직 구현 필요
            # 현재는 로깅만 수행
            logger.info(f"사용자 {user_id}의 출금을 위해 {required_energy} 에너지 할당 필요")
            
        except Exception as e:
            logger.error(f"출금용 에너지 할당 실패: {user_id}, {str(e)}")
            # 에너지 할당 실패해도 출금 요청은 계속 진행
            # (수동 처리 또는 다른 방식으로 해결 가능)
            pass

    def _determine_priority(self, amount: Decimal) -> int:
        """출금 금액에 따른 우선순위 결정"""
        if amount >= Decimal("10000"):
            return 1  # 높은 우선순위
        elif amount >= Decimal("1000"):
            return 2  # 중간 우선순위
        else:
            return 3  # 낮은 우선순위
