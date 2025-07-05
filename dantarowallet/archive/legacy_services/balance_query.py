"""
잔고 조회/검색 관련 기능 분리 모듈
"""
from app.core.exceptions import NotFoundError
from app.models.balance import Balance
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class BalanceQuery:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: int, asset: str = "USDT") -> Balance:
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
        try:
            return await self.get_balance(user_id, asset)
        except NotFoundError:
            balance = Balance(user_id=user_id, asset=asset)
            self.db.add(balance)
            await self.db.flush()
            return balance
