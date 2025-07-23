"""
통계 계산 서비스
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.transaction_analytics import (
    AssetStats,
    DailyStats,
    TransactionAnalyticsFilter,
    TransactionStats,
)

from .utils import BaseAnalyticsService

logger = logging.getLogger(__name__)


class StatisticsService(BaseAnalyticsService):
    """통계 계산 전용 서비스"""

    async def calculate_overall_stats(
        self,
        db: AsyncSession,
        filters: TransactionAnalyticsFilter,
        start_date: datetime,
        end_date: datetime,
    ) -> TransactionStats:
        """전체 통계 계산"""

        # 전체 통계 쿼리
        result = await db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total_count,
                    COALESCE(SUM(amount), 0) as total_volume,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_count,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as successful_volume,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COALESCE(AVG(amount), 0) as average_amount,
                    COALESCE(SUM(fee), 0) as total_fees
                FROM transactions
                WHERE created_at >= :start_date AND created_at <= :end_date
            """
            ).bindparams(start_date=start_date, end_date=end_date)
        )

        row = result.fetchone()

        if not row:
            return self._create_empty_stats()

        return TransactionStats(
            total_count=row[0] or 0,
            total_volume=Decimal(str(row[1] or 0)),
            successful_count=row[2] or 0,
            successful_volume=Decimal(str(row[3] or 0)),
            failed_count=row[4] or 0,
            pending_count=row[5] or 0,
            average_amount=Decimal(str(row[6] or 0)),
            total_fees=Decimal(str(row[7] or 0)),
        )

    async def calculate_asset_stats(
        self,
        db: AsyncSession,
        filters: TransactionAnalyticsFilter,
        start_date: datetime,
        end_date: datetime,
    ) -> List[AssetStats]:
        """자산별 통계 계산"""

        result = await db.execute(
            text(
                """
                SELECT
                    asset,
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(amount), 0) as total_volume,
                    COUNT(CASE WHEN direction = 'in' THEN 1 END) as deposits_count,
                    COALESCE(SUM(CASE WHEN direction = 'in' THEN amount ELSE 0 END), 0) as deposits_volume,
                    COUNT(CASE WHEN direction = 'out' THEN 1 END) as withdrawals_count,
                    COALESCE(SUM(CASE WHEN direction = 'out' THEN amount ELSE 0 END), 0) as withdrawals_volume
                FROM transactions
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY asset
                ORDER BY total_volume DESC
            """
            ).bindparams(start_date=start_date, end_date=end_date)
        )

        rows = result.fetchall()

        return [
            AssetStats(
                asset=row[0],
                transaction_count=row[1],
                total_volume=Decimal(str(row[2])),
                deposits_count=row[3],
                deposits_volume=Decimal(str(row[4])),
                withdrawals_count=row[5],
                withdrawals_volume=Decimal(str(row[6])),
            )
            for row in rows
        ]

    async def calculate_daily_stats(
        self,
        db: AsyncSession,
        filters: TransactionAnalyticsFilter,
        start_date: datetime,
        end_date: datetime,
    ) -> List[DailyStats]:
        """일별 통계 계산"""

        result = await db.execute(
            text(
                """
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(amount), 0) as total_volume,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_count,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                    COUNT(DISTINCT user_id) as active_users
                FROM transactions
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            ).bindparams(start_date=start_date, end_date=end_date)
        )

        rows = result.fetchall()

        return [
            DailyStats(
                date=datetime.strptime(row[0], "%Y-%m-%d").date(),
                transaction_count=row[1],
                total_volume=Decimal(str(row[2])),
                successful_count=row[3],
                failed_count=row[4],
                active_users=row[5],
            )
            for row in rows
        ]

    def _create_empty_stats(self) -> TransactionStats:
        """빈 통계 객체 생성"""
        return TransactionStats(
            total_count=0,
            total_volume=Decimal("0"),
            successful_count=0,
            successful_volume=Decimal("0"),
            failed_count=0,
            pending_count=0,
            average_amount=Decimal("0"),
            total_fees=Decimal("0"),
        )
