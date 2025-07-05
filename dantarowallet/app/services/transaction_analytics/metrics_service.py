"""
실시간 메트릭 서비스
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from app.schemas.transaction_analytics import RealTimeTransactionMetrics
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import BaseAnalyticsService

logger = logging.getLogger(__name__)


class MetricsService(BaseAnalyticsService):
    """실시간 메트릭 전용 서비스"""

    async def get_real_time_metrics(
        self, db: AsyncSession
    ) -> RealTimeTransactionMetrics:
        """실시간 트랜잭션 메트릭 조회"""
        try:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            # 각 메트릭을 병렬로 계산
            tps = await self._calculate_tps(db, minute_ago)
            volume_per_minute = await self._calculate_volume_per_minute(db, minute_ago)
            active_users = await self._calculate_active_users(db, hour_ago)
            pending_transactions = await self._calculate_pending_transactions(db)
            failed_rate = await self._calculate_failed_rate(db, hour_ago)

            # 평균 처리 시간 (임시로 5초로 설정)
            avg_processing_time = 5.0

            # 시스템 건강도 점수 계산
            health_score = self._calculate_health_score(
                tps, failed_rate, int(pending_transactions), int(active_users)
            )

            return RealTimeTransactionMetrics(
                current_tps=tps,
                current_volume_per_minute=volume_per_minute,
                active_users_last_hour=int(active_users),
                pending_transactions=int(pending_transactions),
                failed_transaction_rate=failed_rate,
                average_processing_time_seconds=avg_processing_time,
                system_health_score=health_score,
            )

        except Exception as e:
            logger.error(f"실시간 메트릭 조회 중 오류: {str(e)}")
            return self._create_empty_metrics()

    async def _calculate_tps(self, db: AsyncSession, minute_ago: datetime) -> float:
        """초당 거래 수 계산"""
        result = await db.execute(
            text(
                """
                SELECT COUNT(*) as count FROM transactions
                WHERE created_at >= :minute_ago
            """
            ).bindparams(minute_ago=minute_ago)
        )
        tps_count = result.scalar() or 0
        return float(tps_count) / 60.0

    async def _calculate_volume_per_minute(
        self, db: AsyncSession, minute_ago: datetime
    ) -> Decimal:
        """분당 거래량 계산"""
        result = await db.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0) as volume FROM transactions
                WHERE created_at >= :minute_ago
            """
            ).bindparams(minute_ago=minute_ago)
        )
        volume_result = result.scalar() or 0
        return Decimal(str(volume_result))

    async def _calculate_active_users(
        self, db: AsyncSession, hour_ago: datetime
    ) -> int:
        """활성 사용자 수 계산"""
        result = await db.execute(
            text(
                """
                SELECT COUNT(DISTINCT user_id) as count FROM transactions
                WHERE created_at >= :hour_ago
            """
            ).bindparams(hour_ago=hour_ago)
        )
        return result.scalar() or 0

    async def _calculate_pending_transactions(self, db: AsyncSession) -> int:
        """대기 중 거래 수 계산"""
        result = await db.execute(
            text(
                """
                SELECT COUNT(*) as count FROM transactions
                WHERE status = 'pending'
            """
            )
        )
        return result.scalar() or 0

    async def _calculate_failed_rate(
        self, db: AsyncSession, hour_ago: datetime
    ) -> float:
        """실패율 계산"""
        result = await db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
                FROM transactions
                WHERE created_at >= :hour_ago
            """
            ).bindparams(hour_ago=hour_ago)
        )
        row = result.fetchone()
        if row:
            total_count = row[0] or 0
            failed_count = row[1] or 0
            return (failed_count / total_count * 100) if total_count > 0 else 0
        return 0.0

    def _calculate_health_score(
        self, tps: float, failed_rate: float, pending_count: int, active_users: int
    ) -> float:
        """시스템 건강도 점수 계산"""
        score = 1.0

        # 실패율이 높으면 점수 감소
        if failed_rate > 10:
            score -= 0.3
        elif failed_rate > 5:
            score -= 0.1

        # 대기 거래가 너무 많으면 점수 감소
        if pending_count > 100:
            score -= 0.2
        elif pending_count > 50:
            score -= 0.1

        # TPS가 너무 높으면 (과부하) 점수 감소
        if tps > 10:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _create_empty_metrics(self) -> RealTimeTransactionMetrics:
        """빈 메트릭 객체 생성"""
        return RealTimeTransactionMetrics(
            current_tps=0.0,
            current_volume_per_minute=Decimal("0"),
            active_users_last_hour=0,
            pending_transactions=0,
            failed_transaction_rate=0.0,
            average_processing_time_seconds=0.0,
            system_health_score=0.0,
        )
