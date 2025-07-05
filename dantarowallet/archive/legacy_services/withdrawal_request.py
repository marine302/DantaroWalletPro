"""
출금 요청/생성 관련 기능 분리 모듈
"""
from decimal import Decimal
from typing import Optional

from app.core.exceptions import ValidationError
from app.models.withdrawal import Withdrawal, WithdrawalPriority, WithdrawalStatus
from sqlalchemy.ext.asyncio import AsyncSession


class WithdrawalRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_withdrawal_request(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal,
        asset: str = "USDT",
        notes: Optional[str] = None,
    ) -> Withdrawal:
        # ...출금 요청 생성 로직...
        pass
