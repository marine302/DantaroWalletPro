"""
Withdrawal Service - 출금 관리 서비스
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logger import get_logger
from app.models.withdrawal import Withdrawal

logger = get_logger(__name__)


class WithdrawalService:
    """출금 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_withdrawal(self, user_id: int, amount: float, address: str) -> Optional[Withdrawal]:
        """출금 요청 생성"""
        try:
            withdrawal = Withdrawal(
                user_id=user_id,
                amount=amount,
                to_address=address,
                status="pending"
            )
            self.db.add(withdrawal)
            await self.db.commit()
            await self.db.refresh(withdrawal)
            return withdrawal
        except Exception as e:
            logger.error(f"출금 요청 생성 실패: {e}")
            await self.db.rollback()
            return None
    
    async def get_withdrawal(self, withdrawal_id: int) -> Optional[Withdrawal]:
        """출금 요청 조회"""
        try:
            result = await self.db.execute(
                select(Withdrawal).where(Withdrawal.id == withdrawal_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"출금 요청 조회 실패: {e}")
            return None
    
    async def get_user_withdrawals(self, user_id: int) -> List[Withdrawal]:
        """사용자 출금 내역 조회"""
        try:
            result = await self.db.execute(
                select(Withdrawal).where(Withdrawal.user_id == user_id)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"사용자 출금 내역 조회 실패: {e}")
            return []