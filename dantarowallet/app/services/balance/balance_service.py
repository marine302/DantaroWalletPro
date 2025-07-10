"""
Balance Service - 잔액 관리 서비스
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.logger import get_logger
from app.models.balance import Balance
from app.models.user import User

logger = get_logger(__name__)


class BalanceService:
    """잔액 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_balance(self, user_id: int, token_symbol: str = "TRX") -> Optional[Balance]:
        """사용자 잔액 조회"""
        try:
            result = await self.db.execute(
                select(Balance).where(
                    Balance.user_id == user_id,
                    Balance.token_symbol == token_symbol
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"잔액 조회 실패: {e}")
            return None
    
    async def update_balance(self, user_id: int, token_symbol: str, amount: float) -> bool:
        """잔액 업데이트"""
        try:
            balance = await self.get_user_balance(user_id, token_symbol)
            if balance:
                balance.amount = amount
            else:
                balance = Balance(
                    user_id=user_id,
                    token_symbol=token_symbol,
                    amount=amount
                )
                self.db.add(balance)
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"잔액 업데이트 실패: {e}")
            await self.db.rollback()
            return False
    
    async def get_all_balances(self, user_id: int) -> list:
        """사용자의 모든 토큰 잔액 조회"""
        try:
            result = await self.db.execute(
                select(Balance).where(Balance.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"전체 잔액 조회 실패: {e}")
            return []