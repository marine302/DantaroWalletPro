"""
잔고 관리 서비스의 기본 클래스
공통 로직, 초기화 등을 정의합니다.
"""
import logging
from decimal import Decimal
from typing import Optional

from app.core.exceptions import InsufficientBalanceError, NotFoundError, ValidationError
from app.models.balance import Balance
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseBalanceService:
    """잔고 관리 기본 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: int, asset: str = "USDT") -> Balance:
        """사용자 잔고 조회"""
        result = await self.db.execute(
            select(Balance).filter(
                and_(Balance.user_id == user_id, Balance.asset == asset)
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            raise NotFoundError(f"Balance for asset {asset}")

        return balance

    async def get_or_create_balance(self, user_id: int, asset: str = "USDT") -> Balance:
        """잔고 조회 또는 생성"""
        try:
            return await self.get_balance(user_id, asset)
        except NotFoundError:
            # 잔고가 없으면 생성
            balance = Balance(
                user_id=user_id,
                asset=asset,
                amount=Decimal("0.000000"),
                locked_amount=Decimal("0.000000"),
            )
            self.db.add(balance)
            await self.db.flush()
            return balance

    async def lock_amount(
        self, user_id: int, asset: str = "USDT", amount: Decimal = Decimal("0")
    ) -> bool:
        """금액 잠금 (출금 준비 등)"""
        balance = await self.get_balance(user_id, asset)

        if balance.lock(amount):
            await self.db.flush()
            return True

        raise InsufficientBalanceError(
            required=float(amount), available=float(balance.available_amount)
        )

    async def unlock_amount(
        self, user_id: int, asset: str = "USDT", amount: Decimal = Decimal("0")
    ) -> bool:
        """금액 잠금 해제"""
        balance = await self.get_balance(user_id, asset)

        if balance.unlock(amount):
            await self.db.flush()
            return True

        raise ValidationError(f"Cannot unlock {amount} {asset}")
