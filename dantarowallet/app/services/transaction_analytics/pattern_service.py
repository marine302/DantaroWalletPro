"""
트랜잭션 패턴 감지 서비스
의심스러운 거래 패턴을 탐지하고 분석합니다.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction_analytics import (
    SuspiciousPatternAlert,
    TransactionMonitoringConfig,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PatternDetectionService:
    """트랜잭션 패턴 감지 서비스"""

    def __init__(self, monitoring_config: TransactionMonitoringConfig):
        self.monitoring_config = monitoring_config

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

            # 5. 라운드 트립 거래 감지
            round_trip_patterns = await self._detect_round_trip_patterns(
                db, cutoff_time, user_id
            )
            alerts.extend(round_trip_patterns)

            return alerts

        except Exception as e:
            logger.error(f"의심스러운 패턴 감지 중 오류: {str(e)}")
            return []

    async def _detect_large_transactions(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """대량 거래 감지"""
        threshold = self.monitoring_config.large_transaction_threshold_usd

        query = """
            SELECT user_id, COUNT(*) as count, SUM(amount) as total_amount, MAX(amount) as max_amount
            FROM transactions
            WHERE created_at >= :cutoff_time AND amount >= :threshold
                AND status = :status
        """

        params = {
            "cutoff_time": cutoff_time,
            "threshold": threshold,
            "status": TransactionStatus.COMPLETED.value,
        }

        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id

        query += """
            GROUP BY user_id
            HAVING COUNT(*) > 1 OR MAX(amount) > :large_threshold
        """
        params["large_threshold"] = threshold * 2

        result = await db.execute(text(query), params)

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

        # 시간당 거래량 체크
        hour_ago = datetime.utcnow() - timedelta(hours=1)

        query = """
            SELECT user_id, COUNT(*) as hourly_count
            FROM transactions
            WHERE created_at >= :hour_ago
        """

        params = {"hour_ago": hour_ago}

        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id

        query += """
            GROUP BY user_id
            HAVING COUNT(*) > :hourly_threshold
        """
        params["hourly_threshold"] = hourly_threshold

        result = await db.execute(text(query), params)

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
        """비정상적인 시간대 거래 감지"""
        # 새벽 시간대 거래 (02:00 - 06:00) 감지
        query = """
            SELECT user_id, COUNT(*) as count
            FROM transactions
            WHERE created_at >= :cutoff_time
                AND EXTRACT(hour FROM created_at) BETWEEN 2 AND 6
        """

        params = {"cutoff_time": cutoff_time}

        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id

        query += """
            GROUP BY user_id
            HAVING COUNT(*) > 3
        """

        result = await db.execute(text(query), params)

        alerts = []
        for row in result.fetchall():
            confidence = min(0.7, row.count / 10)
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="unusual_timing",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "unusual_hour_count": row.count,
                        "time_range": "02:00-06:00",
                    },
                    recommendations=["사용자 활동 시간 패턴 분석", "지역/시간대 확인", "계정 보안 검토"],
                )
            )

        return alerts

    async def _detect_failed_patterns(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """연속 실패 거래 감지"""
        query = """
            SELECT user_id, COUNT(*) as failed_count
            FROM transactions
            WHERE created_at >= :cutoff_time
                AND status = :failed_status
        """

        params = {"cutoff_time": cutoff_time, "failed_status": "FAILED"}

        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id

        query += """
            GROUP BY user_id
            HAVING COUNT(*) > 5
        """

        result = await db.execute(text(query), params)

        alerts = []
        for row in result.fetchall():
            confidence = min(0.8, row.failed_count / 20)
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="repeated_failures",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "failed_count": row.failed_count,
                        "threshold": 5,
                    },
                    recommendations=[
                        "실패 원인 분석",
                        "사용자 지원 제공",
                        "시스템 오류 검토",
                        "악의적 시도 가능성 검토",
                    ],
                )
            )

        return alerts

    async def _detect_round_trip_patterns(
        self, db: AsyncSession, cutoff_time: datetime, user_id: Optional[int] = None
    ) -> List[SuspiciousPatternAlert]:
        """라운드 트립 거래 패턴 감지 (예: 빠른 입출금 반복)"""
        query = """
            WITH deposit_withdraw_pairs AS (
                SELECT
                    user_id,
                    LAG(type) OVER (PARTITION BY user_id ORDER BY created_at) as prev_type,
                    type as current_type,
                    LAG(created_at) OVER (PARTITION BY user_id ORDER BY created_at) as prev_time,
                    created_at as current_time,
                    amount
                FROM transactions
                WHERE created_at >= :cutoff_time
                    AND type IN ('DEPOSIT', 'WITHDRAWAL')
                    AND status = :completed_status
            )
            SELECT
                user_id,
                COUNT(*) as round_trip_count
            FROM deposit_withdraw_pairs
            WHERE prev_type != current_type
                AND EXTRACT(EPOCH FROM (current_time - prev_time)) < 3600  -- 1시간 이내
        """

        params = {
            "cutoff_time": cutoff_time,
            "completed_status": TransactionStatus.COMPLETED.value,
        }

        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id

        query += """
            GROUP BY user_id
            HAVING COUNT(*) > 3
        """

        result = await db.execute(text(query), params)

        alerts = []
        for row in result.fetchall():
            confidence = min(0.85, row.round_trip_count / 10)
            alerts.append(
                SuspiciousPatternAlert(
                    pattern_type="round_trip_pattern",
                    confidence_score=confidence,
                    details={
                        "user_id": row.user_id,
                        "round_trip_count": row.round_trip_count,
                        "time_window": "1_hour",
                    },
                    recommendations=[
                        "거래 목적 확인",
                        "자금세탁 가능성 검토",
                        "거래 패턴 상세 분석",
                        "규제 당국 신고 검토",
                    ],
                )
            )

        return alerts


class VelocityCheckService:
    """거래 속도 체크 서비스"""

    def __init__(self, monitoring_config: TransactionMonitoringConfig):
        self.monitoring_config = monitoring_config

    async def check_transaction_velocity(
        self, db: AsyncSession, user_id: int, amount: float, asset: str
    ) -> dict:
        """거래 속도 체크"""
        try:
            now = datetime.utcnow()

            # 다양한 시간 윈도우에서 체크
            checks = {
                "hourly": await self._check_velocity_window(
                    db, user_id, now - timedelta(hours=1), amount
                ),
                "daily": await self._check_velocity_window(
                    db, user_id, now - timedelta(days=1), amount
                ),
                "weekly": await self._check_velocity_window(
                    db, user_id, now - timedelta(days=7), amount
                ),
            }

            return {
                "passed": all(check["passed"] for check in checks.values()),
                "checks": checks,
                "recommendations": self._get_velocity_recommendations(checks),
            }

        except Exception as e:
            logger.error(f"거래 속도 체크 중 오류: {str(e)}")
            return {"passed": True, "error": str(e)}

    async def _check_velocity_window(
        self, db: AsyncSession, user_id: int, since: datetime, current_amount: float
    ) -> dict:
        """특정 시간 윈도우에서 거래 속도 체크"""
        result = await db.execute(
            text(
                """
                SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :since
                    AND status = :status
            """
            ),
            {
                "user_id": user_id,
                "since": since,
                "status": TransactionStatus.COMPLETED.value,
            },
        )

        row = result.fetchone()
        current_count = row.count if row else 0
        current_total = float(row.total_amount) if row else 0.0

        # 새 거래 포함 계산
        new_count = current_count + 1
        new_total = current_total + current_amount

        # 윈도우별 제한 확인
        window_hours = (datetime.utcnow() - since).total_seconds() / 3600

        if window_hours <= 1:  # 1시간
            count_limit = self.monitoring_config.max_transactions_per_hour
            amount_limit = self.monitoring_config.max_amount_per_hour_usd
        elif window_hours <= 24:  # 1일
            count_limit = self.monitoring_config.max_transactions_per_day
            amount_limit = self.monitoring_config.max_amount_per_day_usd
        else:  # 1주일
            count_limit = self.monitoring_config.max_transactions_per_week
            amount_limit = self.monitoring_config.max_amount_per_week_usd

        return {
            "passed": new_count <= count_limit and new_total <= amount_limit,
            "current_count": current_count,
            "new_count": new_count,
            "count_limit": count_limit,
            "current_amount": current_total,
            "new_amount": new_total,
            "amount_limit": amount_limit,
            "window_hours": window_hours,
        }

    def _get_velocity_recommendations(self, checks: dict) -> List[str]:
        """속도 체크 결과에 따른 권고사항"""
        recommendations = []

        for window, check in checks.items():
            if not check["passed"]:
                if check["new_count"] > check["count_limit"]:
                    recommendations.append(f"{window} 거래 횟수 제한 초과")
                if check["new_amount"] > check["amount_limit"]:
                    recommendations.append(f"{window} 거래 금액 제한 초과")

        if recommendations:
            recommendations.extend(["거래 제한 적용 권장", "사용자 신원 재확인 필요", "거래 목적 문의"])

        return recommendations
