"""
공통 타입 정의 및 유틸리티
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction_analytics import (
    SystemTransactionAlert,
    TransactionAlert,
    TransactionSummary,
)
from app.schemas.transaction_analytics import (
    AssetStats,
    DailyStats,
    TransactionAnalyticsFilter,
    TransactionMonitoringConfig,
    TransactionStats,
)


class BaseAnalyticsService:
    """분석 서비스 베이스 클래스"""

    def __init__(self):
        self.monitoring_config = TransactionMonitoringConfig()

    def _validate_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> Tuple[datetime, datetime]:
        """날짜 범위 검증 및 기본값 설정"""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        if start_date > end_date:
            raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다")

        return start_date, end_date

    def _build_base_conditions(
        self,
        filters: TransactionAnalyticsFilter,
        start_date: datetime,
        end_date: datetime,
    ) -> List:
        """기본 쿼리 조건 생성"""
        conditions = [
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
        ]

        if filters.user_id:
            conditions.append(Transaction.user_id == filters.user_id)
        if filters.asset:
            conditions.append(Transaction.asset == filters.asset)
        if filters.transaction_type:
            conditions.append(Transaction.type == filters.transaction_type)
        if filters.status:
            conditions.append(Transaction.status == filters.status)
        if filters.direction:
            conditions.append(Transaction.direction == filters.direction)
        if filters.min_amount:
            conditions.append(Transaction.amount >= filters.min_amount)
        if filters.max_amount:
            conditions.append(Transaction.amount <= filters.max_amount)

        return conditions
