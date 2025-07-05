"""
트랜잭션 분석 및 모니터링 서비스
"""
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction_analytics import (
    AlertLevel,
    AlertType,
    SystemAlert,
    TransactionAlert,
    TransactionSummary,
)
from app.models.user import User
from app.schemas.transaction_analytics import (
    AlertRequest,
    AlertResponse,
    AssetStats,
    DailyStats,
    RealTimeTransactionMetrics,
    SuspiciousPatternAlert,
    TransactionAnalyticsFilter,
    TransactionAnalyticsResponse,
    TransactionMonitoringConfig,
    TransactionStats,
    TransactionTrendAnalysis,
    UserTransactionProfile,
)
from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class TransactionAnalyticsService:
    """트랜잭션 분석 서비스"""

    def __init__(self):
        self.monitoring_config = TransactionMonitoringConfig()

    async def get_transaction_analytics(
        self, db: AsyncSession, filters: TransactionAnalyticsFilter
    ) -> TransactionAnalyticsResponse:
        """트랜잭션 분석 데이터 조회"""
        try:
            # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 30일)
            end_date = filters.end_date or datetime.utcnow()
            start_date = filters.start_date or (end_date - timedelta(days=30))

            # 전체 통계 계산
            overall_stats = await self._calculate_overall_stats(
                db, filters, start_date, end_date
            )

            # 자산별 통계
            asset_breakdown = await self._calculate_asset_stats(
                db, filters, start_date, end_date
            )

            # 일별 통계
            daily_breakdown = await self._calculate_daily_stats(
                db, filters, start_date, end_date
            )

            # 상위 사용자 (거래량 기준)
            top_users = await self._get_top_users(db, filters, start_date, end_date)

            return TransactionAnalyticsResponse(
                period=f"{start_date.date()} to {end_date.date()}",
                start_date=start_date,
                end_date=end_date,
                overall_stats=overall_stats,
                asset_breakdown=asset_breakdown,
                daily_breakdown=daily_breakdown,
                top_users=top_users,
            )

        except Exception as e:
            logger.error(f"트랜잭션 분석 조회 중 오류: {str(e)}")
            raise ValidationError(f"트랜잭션 분석을 조회할 수 없습니다: {str(e)}")

    async def _calculate_overall_stats(
        self,
        db: AsyncSession,
        filters: TransactionAnalyticsFilter,
        start_date: datetime,
        end_date: datetime,
    ) -> TransactionStats:
        """전체 통계 계산"""

        # 기본 쿼리 조건
        conditions = [
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
        ]

        # 필터 조건 추가
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
            # 빈 결과 처리
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

    async def _calculate_asset_stats(
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
                    COALESCE(SUM(CASE WHEN direction = 'out' THEN amount ELSE 0 END), 0) as withdrawals_volume,
                    COALESCE(SUM(fee), 0) as total_fees
                FROM transactions
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY asset
                ORDER BY total_volume DESC
            """
            ).bindparams(start_date=start_date, end_date=end_date)
        )

        return [
            AssetStats(
                asset=row.asset,
                transaction_count=row.transaction_count,
                total_volume=Decimal(str(row.total_volume)),
                deposits_count=row.deposits_count,
                deposits_volume=Decimal(str(row.deposits_volume)),
                withdrawals_count=row.withdrawals_count,
                withdrawals_volume=Decimal(str(row.withdrawals_volume)),
                total_fees=Decimal(str(row.total_fees)),
            )
            for row in result.fetchall()
        ]

    async def _calculate_daily_stats(
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
                    COUNT(CASE WHEN direction = 'in' THEN 1 END) as deposits_count,
                    COALESCE(SUM(CASE WHEN direction = 'in' THEN amount ELSE 0 END), 0) as deposits_volume,
                    COUNT(CASE WHEN direction = 'out' THEN 1 END) as withdrawals_count,
                    COALESCE(SUM(CASE WHEN direction = 'out' THEN amount ELSE 0 END), 0) as withdrawals_volume
                FROM transactions
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
            ).bindparams(start_date=start_date, end_date=end_date)
        )

        return [
            DailyStats(
                date=row.date,
                transaction_count=row.transaction_count,
                total_volume=Decimal(str(row.total_volume)),
                deposits_count=row.deposits_count,
                deposits_volume=Decimal(str(row.deposits_volume)),
                withdrawals_count=row.withdrawals_count,
                withdrawals_volume=Decimal(str(row.withdrawals_volume)),
            )
            for row in result.fetchall()
        ]

    async def _get_top_users(
        self,
        db: AsyncSession,
        filters: TransactionAnalyticsFilter,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """상위 사용자 조회 (거래량 기준)"""

        result = await db.execute(
            text(
                """
                SELECT
                    t.user_id,
                    u.email,
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(t.amount), 0) as total_volume,
                    COALESCE(SUM(t.fee), 0) as total_fees
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                WHERE t.created_at >= :start_date AND t.created_at <= :end_date
                GROUP BY t.user_id, u.email
                ORDER BY total_volume DESC
                LIMIT :limit
            """
            ).bindparams(start_date=start_date, end_date=end_date, limit=limit)
        )

        return [
            {
                "user_id": row.user_id,
                "email": row.email,
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume),
                "total_fees": float(row.total_fees),
            }
            for row in result.fetchall()
        ]

    async def detect_suspicious_patterns(
        self, db: AsyncSession, user_id: Optional[int] = None, hours_back: int = 24
    ) -> List[SuspiciousPatternAlert]:
        """의심스러운 패턴 감지"""
        try:
            alerts = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            # 1. 대량 거래 감지
            large_transactions = await self._detect_large_transactions(
                db, cutoff_time, user_id
            )
            alerts.extend(large_transactions)

            # 2. 빈번한 거래 감지
            frequent_transactions = await self._detect_frequent_transactions(
                db, cutoff_time, user_id
            )
            alerts.extend(frequent_transactions)

            # 3. 비정상적인 시간대 거래 감지
            unusual_timing = await self._detect_unusual_timing(db, cutoff_time, user_id)
            alerts.extend(unusual_timing)

            # 4. 연속 실패 거래 감지
            failed_patterns = await self._detect_failed_patterns(
                db, cutoff_time, user_id
            )
            alerts.extend(failed_patterns)

            return alerts

        except Exception as e:
            logger.error(f"의심스러운 패턴 감지 중 오류: {str(e)}")
            return []

    async def _detect_large_transactions(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """대량 거래 감지"""
        threshold = self.monitoring_config.large_transaction_threshold_usd

        conditions = [
            Transaction.created_at >= cutoff_time,
            Transaction.amount >= threshold,
            Transaction.status == TransactionStatus.COMPLETED,
        ]

        if user_id:
            conditions.append(Transaction.user_id == user_id)

        result = await db.execute(
            text(
                """
                SELECT user_id, COUNT(*) as count, SUM(amount) as total_amount, MAX(amount) as max_amount
                FROM transactions
                WHERE created_at >= :cutoff_time AND amount >= :threshold
                GROUP BY user_id
                HAVING COUNT(*) > 1 OR MAX(amount) > :large_threshold
            """
            ).bindparams(
                cutoff_time=cutoff_time,
                threshold=threshold,
                large_threshold=threshold * 2,
            )
        )

        alerts = []
        for row in result.fetchall():
            confidence = min(0.9, float(row.max_amount) / float(threshold * 5))
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="large_transaction",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "transaction_count": row.count,
                        "total_amount": float(row.total_amount),
                        "max_amount": float(row.max_amount),
                        "threshold": float(threshold),
                    },
                    recommendations=["사용자 신원 재확인", "거래 목적 문의", "추가 KYC 검증 고려"],
                )
            )

        return alerts

    async def _detect_frequent_transactions(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """빈번한 거래 감지"""
        hourly_threshold = self.monitoring_config.max_transactions_per_hour
        daily_threshold = self.monitoring_config.max_transactions_per_day

        # 시간당 거래량 체크
        hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await db.execute(
            text(
                """
                SELECT user_id, COUNT(*) as hourly_count
                FROM transactions
                WHERE created_at >= :hour_ago
                GROUP BY user_id
                HAVING COUNT(*) > :hourly_threshold
            """
            ).bindparams(hour_ago=hour_ago, hourly_threshold=hourly_threshold)
        )

        alerts = []
        for row in result.fetchall():
            confidence = min(0.95, row.hourly_count / (hourly_threshold * 2))
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="frequent_transactions",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "hourly_count": row.hourly_count,
                        "threshold": hourly_threshold,
                        "time_window": "1_hour",
                    },
                    recommendations=["계정 활동 모니터링 강화", "거래 패턴 분석", "일시적 거래 제한 고려"],
                )
            )

        return alerts

    async def _detect_unusual_timing(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """비정상적인 시간대 거래 감지 (새벽 시간대)"""
        # 새벽 2-6시 거래를 비정상으로 간주

        result = await db.execute(
            text(
                """
                SELECT user_id, COUNT(*) as night_count
                FROM transactions
                WHERE created_at >= :cutoff_time
                AND (EXTRACT(hour FROM created_at) BETWEEN 2 AND 6)
                GROUP BY user_id
                HAVING COUNT(*) > 3
            """
            ).bindparams(cutoff_time=cutoff_time)
        )

        alerts = []
        for row in result.fetchall():
            confidence = min(0.8, row.night_count / 10)
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="unusual_timing",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "night_transactions": row.night_count,
                        "time_range": "02:00-06:00",
                    },
                    recommendations=["사용자 활동 패턴 분석", "계정 보안 상태 확인", "추가 인증 요구 고려"],
                )
            )

        return alerts

    async def _detect_failed_patterns(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """연속 실패 거래 감지"""

        result = await db.execute(
            text(
                """
                SELECT user_id, COUNT(*) as failed_count, AVG(amount) as avg_amount
                FROM transactions
                WHERE created_at >= :cutoff_time
                AND status = 'failed'
                GROUP BY user_id
                HAVING COUNT(*) > 5
            """
            ).bindparams(cutoff_time=cutoff_time)
        )

        alerts = []
        for row in result.fetchall():
            confidence = min(0.7, row.failed_count / 20)
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="repeated_failures",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "failed_count": row.failed_count,
                        "average_amount": float(row.avg_amount),
                    },
                    recommendations=["계정 상태 점검", "기술적 문제 확인", "사용자 지원 제공"],
                )
            )

        return alerts

    async def create_alert(
        self, db: AsyncSession, alert_request: AlertRequest
    ) -> AlertResponse:
        """알림 생성"""
        try:
            alert_data_json = (
                json.dumps(alert_request.alert_data)
                if alert_request.alert_data
                else None
            )

            alert = TransactionAlert(
                user_id=alert_request.user_id,
                transaction_id=alert_request.transaction_id,
                alert_type=alert_request.alert_type,
                level=alert_request.level.value,
                title=alert_request.title,
                description=alert_request.description,
                alert_data=alert_data_json,
            )

            db.add(alert)
            await db.commit()
            await db.refresh(alert)

            logger.info(
                f"알림 생성됨: {alert.id} (타입: {alert.alert_type}, 레벨: {alert.level})"
            )

            return AlertResponse(
                id=alert.id,  # type: ignore
                user_id=alert.user_id,  # type: ignore
                transaction_id=alert.transaction_id,  # type: ignore
                alert_type=alert.alert_type,  # type: ignore
                level=alert.level,  # type: ignore
                title=alert.title,  # type: ignore
                description=alert.description,  # type: ignore
                is_resolved=alert.is_resolved,  # type: ignore
                resolved_by=alert.resolved_by,  # type: ignore
                resolved_at=alert.resolved_at,  # type: ignore
                created_at=alert.created_at,  # type: ignore
                alert_data=json.loads(alert.alert_data) if alert.alert_data else None,  # type: ignore
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"알림 생성 중 오류: {str(e)}")
            raise ValidationError(f"알림을 생성할 수 없습니다: {str(e)}")

    async def get_real_time_metrics(
        self, db: AsyncSession
    ) -> RealTimeTransactionMetrics:
        """실시간 트랜잭션 메트릭 조회"""
        try:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            # 초당 거래 수 (최근 1분 기준)
            result = await db.execute(
                text(
                    """
                    SELECT COUNT(*) as count FROM transactions
                    WHERE created_at >= :minute_ago
                """
                ).bindparams(minute_ago=minute_ago)
            )
            tps_count = result.scalar() or 0
            tps = float(tps_count) / 60.0

            # 분당 거래량
            result = await db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(amount), 0) as volume FROM transactions
                    WHERE created_at >= :minute_ago
                """
                ).bindparams(minute_ago=minute_ago)
            )
            volume_result = result.scalar() or 0
            volume_per_minute = Decimal(str(volume_result))

            # 최근 1시간 활성 사용자
            result = await db.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT user_id) as count FROM transactions
                    WHERE created_at >= :hour_ago
                """
                ).bindparams(hour_ago=hour_ago)
            )
            active_users = result.scalar() or 0

            # 대기 중 거래
            result = await db.execute(
                text(
                    """
                    SELECT COUNT(*) as count FROM transactions
                    WHERE status = 'pending'
                """
                )
            )
            pending_transactions = result.scalar() or 0

            # 실패율 (최근 1시간)
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
                failed_rate = (
                    (failed_count / total_count * 100) if total_count > 0 else 0
                )
            else:
                failed_rate = 0

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
            raise ValidationError(f"실시간 메트릭을 조회할 수 없습니다: {str(e)}")

    def _calculate_health_score(
        self, tps: float, failed_rate: float, pending_count: int, active_users: int
    ) -> float:
        """시스템 건강도 점수 계산"""
        # 기본 점수
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

    async def get_user_transaction_profile(
        self, db: AsyncSession, user_id: int
    ) -> UserTransactionProfile:
        """사용자 거래 프로필 조회"""
        try:
            # 사용자 존재 확인
            from sqlalchemy import select

            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise NotFoundError("사용자를 찾을 수 없습니다")

            # 최근 30일 거래 통계
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            # 기본 통계
            result = await db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total_transactions,
                        COALESCE(SUM(amount), 0) as total_volume,
                        COUNT(DISTINCT asset) as assets_used,
                        MIN(created_at) as first_transaction,
                        MAX(created_at) as last_transaction
                    FROM transactions
                    WHERE user_id = :user_id AND created_at >= :start_date
                """
                ).bindparams(user_id=user_id, start_date=start_date)
            )
            row = result.fetchone()

            if not row:
                # 빈 프로필 반환
                return UserTransactionProfile(
                    user_id=user_id,
                    total_transactions=0,
                    total_volume_usd=Decimal("0"),
                    avg_transaction_amount=Decimal("0"),
                    most_used_asset="",
                    transaction_frequency="low",
                    risk_score=0.0,
                    last_transaction_date=None,
                    preferred_transaction_hours=[],
                    monthly_volume_trend=[],
                )

            total_transactions = row[0] or 0
            total_volume = Decimal(str(row[1] or 0))
            first_transaction = row[3]
            last_transaction = row[4]

            # 평균 거래 금액 계산
            avg_amount = (
                total_volume / total_transactions
                if total_transactions > 0
                else Decimal("0")
            )

            # 가장 많이 사용한 자산
            result = await db.execute(
                text(
                    """
                    SELECT asset, COUNT(*) as count
                    FROM transactions
                    WHERE user_id = :user_id AND created_at >= :start_date
                    GROUP BY asset
                    ORDER BY count DESC
                    LIMIT 1
                """
                ).bindparams(user_id=user_id, start_date=start_date)
            )
            asset_row = result.fetchone()
            most_used_asset = asset_row[0] if asset_row else ""

            # 거래 빈도 계산
            days_active = (end_date - start_date).days
            daily_avg = total_transactions / days_active if days_active > 0 else 0

            if daily_avg > 5:
                frequency = "high"
            elif daily_avg > 1:
                frequency = "medium"
            else:
                frequency = "low"

            # 리스크 점수 (간단한 계산)
            risk_score = min(
                1.0,
                (total_transactions / 1000) * 0.5
                + (float(total_volume) / 100000) * 0.5,
            )

            return UserTransactionProfile(
                user_id=user_id,
                total_transactions=total_transactions,
                total_volume_usd=total_volume,
                avg_transaction_amount=avg_amount,
                most_used_asset=most_used_asset,
                transaction_frequency=frequency,
                risk_score=risk_score,
                last_transaction_date=last_transaction,
                preferred_transaction_hours=[],  # 간단화를 위해 빈 리스트
                monthly_volume_trend=[],  # 간단화를 위해 빈 리스트
            )

        except NotFoundError as e:
            # NotFoundError는 그대로 전파
            raise e
        except Exception as e:
            logger.error(f"사용자 프로필 조회 중 오류: {str(e)}")
            raise ValidationError(f"사용자 프로필을 조회할 수 없습니다: {str(e)}")

    async def get_transaction_trends(
        self, db: AsyncSession, period: str, asset: Optional[str] = None
    ) -> TransactionTrendAnalysis:
        """트랜잭션 트렌드 분석"""
        try:
            # 기간 설정
            end_date = datetime.utcnow()
            if period == "1d":
                start_date = end_date - timedelta(days=1)
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                raise ValidationError("지원하지 않는 기간입니다")

            # 간단한 트렌드 분석 (실제로는 더 복잡한 로직 필요)
            result = await db.execute(
                text(
                    """
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as transaction_count,
                        COALESCE(SUM(amount), 0) as volume
                    FROM transactions
                    WHERE created_at >= :start_date
                    AND (:asset IS NULL OR asset = :asset)
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """
                ).bindparams(start_date=start_date, asset=asset)
            )

            daily_data = result.fetchall()

            return TransactionTrendAnalysis(
                period=period,
                asset=asset,
                trend_direction="stable",  # 간단화
                growth_rate=0.0,  # 간단화
                daily_volume_trend=[],  # 간단화
                peak_hours=[],  # 간단화
                seasonal_patterns=[],  # 간단화
                prediction_next_7_days=[],  # 간단화
            )

        except Exception as e:
            logger.error(f"트렌드 분석 중 오류: {str(e)}")
            raise ValidationError(f"트렌드 분석을 수행할 수 없습니다: {str(e)}")

    async def get_alerts(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        level: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AlertResponse]:
        """알림 목록 조회"""
        try:
            from sqlalchemy import select

            query = select(TransactionAlert)

            if user_id:
                query = query.where(TransactionAlert.user_id == user_id)
            if alert_type:
                query = query.where(TransactionAlert.alert_type == alert_type)
            if level:
                query = query.where(TransactionAlert.level == level)
            if is_resolved is not None:
                query = query.where(TransactionAlert.is_resolved == is_resolved)

            query = query.order_by(desc(TransactionAlert.created_at))
            query = query.offset(offset).limit(limit)

            result = await db.execute(query)
            alerts = result.scalars().all()

            return [
                AlertResponse(
                    id=alert.id,  # type: ignore
                    user_id=alert.user_id,  # type: ignore
                    transaction_id=alert.transaction_id,  # type: ignore
                    alert_type=alert.alert_type,  # type: ignore
                    level=alert.level,  # type: ignore
                    title=alert.title,  # type: ignore
                    description=alert.description,  # type: ignore
                    is_resolved=alert.is_resolved,  # type: ignore
                    resolved_by=alert.resolved_by,  # type: ignore
                    resolved_at=alert.resolved_at,  # type: ignore
                    created_at=alert.created_at,  # type: ignore
                    alert_data=json.loads(alert.alert_data) if alert.alert_data else None,  # type: ignore
                )
                for alert in alerts
            ]

        except Exception as e:
            logger.error(f"알림 목록 조회 중 오류: {str(e)}")
            raise ValidationError(f"알림 목록을 조회할 수 없습니다: {str(e)}")

    async def get_alert_by_id(self, db: AsyncSession, alert_id: int) -> AlertResponse:
        """알림 상세 조회"""
        try:
            from sqlalchemy import select

            result = await db.execute(
                select(TransactionAlert).where(TransactionAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()

            if not alert:
                raise NotFoundError("알림을 찾을 수 없습니다")

            return AlertResponse(
                id=alert.id,  # type: ignore
                user_id=alert.user_id,  # type: ignore
                transaction_id=alert.transaction_id,  # type: ignore
                alert_type=alert.alert_type,  # type: ignore
                level=alert.level,  # type: ignore
                title=alert.title,  # type: ignore
                description=alert.description,  # type: ignore
                is_resolved=alert.is_resolved,  # type: ignore
                resolved_by=alert.resolved_by,  # type: ignore
                resolved_at=alert.resolved_at,  # type: ignore
                created_at=alert.created_at,  # type: ignore
                alert_data=json.loads(alert.alert_data) if alert.alert_data else None,  # type: ignore
            )

        except Exception as e:
            logger.error(f"알림 조회 중 오류: {str(e)}")
            raise ValidationError(f"알림을 조회할 수 없습니다: {str(e)}")

    async def resolve_alert(self, db: AsyncSession, alert_id: int, admin_id: int):
        """알림 해결 처리"""
        try:
            from sqlalchemy import select

            result = await db.execute(
                select(TransactionAlert).where(TransactionAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()

            if not alert:
                raise NotFoundError("알림을 찾을 수 없습니다")

            if alert.is_resolved:  # type: ignore
                raise ValidationError("이미 해결된 알림입니다")

            alert.is_resolved = True  # type: ignore
            alert.resolved_by = admin_id  # type: ignore
            alert.resolved_at = datetime.utcnow()  # type: ignore

            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"알림 해결 중 오류: {str(e)}")
            raise ValidationError(f"알림을 해결할 수 없습니다: {str(e)}")

    async def get_daily_stats(self, db: AsyncSession, date: datetime):
        """일별 통계 조회"""
        try:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

            result = await db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total_count,
                        COALESCE(SUM(amount), 0) as total_volume,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_count,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                        COUNT(DISTINCT user_id) as active_users
                    FROM transactions
                    WHERE created_at >= :start_date AND created_at < :end_date
                """
                ).bindparams(start_date=start_date, end_date=end_date)
            )

            row = result.fetchone()

            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_transactions": row[0] if row else 0,
                "total_volume": float(row[1]) if row else 0.0,
                "successful_transactions": row[2] if row else 0,
                "failed_transactions": row[3] if row else 0,
                "active_users": row[4] if row else 0,
            }

        except Exception as e:
            logger.error(f"일별 통계 조회 중 오류: {str(e)}")
            raise ValidationError(f"일별 통계를 조회할 수 없습니다: {str(e)}")

    async def get_stats_summary(self, db: AsyncSession, period: str):
        """통계 요약 조회"""
        try:
            end_date = datetime.utcnow()

            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                raise ValidationError("지원하지 않는 기간입니다")

            result = await db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total_count,
                        COALESCE(SUM(amount), 0) as total_volume,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_count,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                        COUNT(DISTINCT user_id) as active_users
                    FROM transactions
                    WHERE created_at >= :start_date
                """
                ).bindparams(start_date=start_date)
            )

            row = result.fetchone()

            return {
                "period": period,
                "total_transactions": row[0] if row else 0,
                "total_volume": float(row[1]) if row else 0.0,
                "successful_transactions": row[2] if row else 0,
                "failed_transactions": row[3] if row else 0,
                "active_users": row[4] if row else 0,
                "success_rate": (row[2] / row[0] * 100) if row and row[0] > 0 else 0.0,
            }

        except Exception as e:
            logger.error(f"통계 요약 조회 중 오류: {str(e)}")
            raise ValidationError(f"통계 요약을 조회할 수 없습니다: {str(e)}")

    async def get_monitoring_config(
        self, db: AsyncSession
    ) -> TransactionMonitoringConfig:
        """현재 트랜잭션 모니터링 설정 조회"""
        return self.monitoring_config

    async def update_monitoring_config(
        self, db: AsyncSession, config: TransactionMonitoringConfig
    ) -> TransactionMonitoringConfig:
        """트랜잭션 모니터링 설정 업데이트"""
        try:
            self.monitoring_config = config
            logger.info("모니터링 설정이 업데이트되었습니다")
            return self.monitoring_config
        except Exception as e:
            logger.error(f"모니터링 설정 업데이트 중 오류: {str(e)}")
            raise ValidationError(f"모니터링 설정을 업데이트할 수 없습니다: {str(e)}")
