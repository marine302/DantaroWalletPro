"""
이상탐지/알림 관련 기능 분리 모듈
"""
from typing import List, Optional

from app.schemas.transaction_analytics import SuspiciousPatternAlert
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsAlerts:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_suspicious_patterns(
        self, user_id: Optional[int] = None, hours_back: int = 24
    ) -> List[SuspiciousPatternAlert]:
        # ...이상탐지 로직...
        pass
