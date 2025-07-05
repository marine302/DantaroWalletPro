"""
트렌드/패턴 관련 기능 분리 모듈
"""
from typing import List, Optional

from app.schemas.transaction_analytics import TransactionTrendAnalysis
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsTrends:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trend_analysis(
        self, user_id: Optional[int] = None
    ) -> List[TransactionTrendAnalysis]:
        # ...트렌드 분석 로직...
        pass
