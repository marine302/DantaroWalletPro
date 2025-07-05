"""
출금 검증 서비스
출금 요청에 대한 유효성 검증 로직을 제공합니다.
"""
import logging
from datetime import datetime
from decimal import Decimal

from app.core.exceptions import InsufficientBalanceError, ValidationError
from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.services.withdrawal.base_service import BaseWithdrawalService
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WithdrawalValidationService(BaseWithdrawalService):
    """출금 검증 서비스"""

    async def validate_withdrawal_request(
        self, user_id: int, to_address: str, amount: Decimal, asset: str = "USDT"
    ) -> None:
        """출금 요청 검증"""

        # 1. 금액 검증
        if amount < self.min_withdrawal:
            raise ValidationError(f"최소 출금 금액은 {self.min_withdrawal} {asset}입니다")

        if amount > self.max_withdrawal_per_tx:
            raise ValidationError(
                f"1회 최대 출금 금액은 {self.max_withdrawal_per_tx} {asset}입니다"
            )

        # 2. 주소 검증
        is_valid = await self.wallet_service.validate_withdrawal_address(to_address)
        if not is_valid:
            raise ValidationError("유효하지 않은 출금 주소입니다")

        # 3. 일일 한도 체크
        daily_total = await self._get_daily_withdrawal_total(user_id, asset)
        if daily_total + amount > self.max_withdrawal_per_day:
            remaining = self.max_withdrawal_per_day - daily_total
            raise ValidationError(f"일일 출금 한도를 초과했습니다. 잔여 한도: {remaining} {asset}")

        # 4. 잔고 확인
        balance = await self.balance_service.get_balance(user_id, asset)
        total_amount = amount + self.withdrawal_fee

        if not balance.can_withdraw(total_amount):
            raise InsufficientBalanceError(
                required=float(total_amount), available=float(balance.available_amount)
            )

    async def _get_daily_withdrawal_total(self, user_id: int, asset: str) -> Decimal:
        """오늘 출금 총액 조회"""
        today = datetime.utcnow().date()
        result = await self.db.execute(
            select(func.sum(Withdrawal.amount)).filter(
                and_(
                    Withdrawal.user_id == user_id,
                    Withdrawal.asset == asset,
                    Withdrawal.requested_at >= today,
                    Withdrawal.status.notin_(
                        [
                            WithdrawalStatus.REJECTED,
                            WithdrawalStatus.CANCELLED,
                            WithdrawalStatus.FAILED,
                        ]
                    ),
                )
            )
        )
        total = result.scalar() or Decimal("0")
        return total
