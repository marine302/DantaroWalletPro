"""
잔고 변경/이체/락 관련 기능 분리 모듈
"""
from decimal import Decimal

from app.core.exceptions import InsufficientBalanceError, ValidationError
from app.models.balance import Balance
from sqlalchemy.ext.asyncio import AsyncSession


class BalanceUpdate:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def lock_amount(
        self, user_id: int, amount: Decimal, asset: str = "USDT"
    ) -> bool:
        balance = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id, Balance.asset == asset)
        )
        balance = balance.scalar_one_or_none()
        if not balance or not balance.lock(amount):
            raise InsufficientBalanceError(
                required=float(amount),
                available=float(balance.available_amount if balance else 0),
            )
        await self.db.flush()
        return True

    async def unlock_amount(
        self, user_id: int, amount: Decimal, asset: str = "USDT"
    ) -> bool:
        balance = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id, Balance.asset == asset)
        )
        balance = balance.scalar_one_or_none()
        if not balance or not balance.unlock(amount):
            raise ValidationError(f"Cannot unlock {amount} {asset}")
        await self.db.flush()
        return True
