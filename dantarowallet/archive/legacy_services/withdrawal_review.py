"""
출금 검토/승인/거절 관련 기능 분리 모듈
"""
from typing import Optional

from app.models.withdrawal import Withdrawal
from sqlalchemy.ext.asyncio import AsyncSession


class WithdrawalReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def review_withdrawal(
        self,
        withdrawal_id: int,
        admin_id: int,
        action: str,  # "approve" or "reject"
        admin_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> Withdrawal:
        # ...출금 검토/승인/거절 로직...
        pass
