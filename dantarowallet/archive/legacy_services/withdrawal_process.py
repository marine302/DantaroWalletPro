"""
출금 처리/완료 관련 기능 분리 모듈
"""
from decimal import Decimal
from typing import Optional

from app.models.withdrawal import Withdrawal
from sqlalchemy.ext.asyncio import AsyncSession


class WithdrawalProcessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_as_processing(self, withdrawal_id: int, admin_id: int) -> Withdrawal:
        # ...출금 처리 중 표시 로직...
        pass

    async def complete_withdrawal(
        self,
        withdrawal_id: int,
        tx_hash: str,
        admin_id: int,
        tx_fee: Optional[Decimal] = None,
    ) -> Withdrawal:
        # ...출금 완료 처리 로직...
        pass
