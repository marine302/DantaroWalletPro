"""
트랜잭션 보고서 생성 서비스
다양한 형태의 분석 보고서를 생성합니다.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User
from app.schemas.transaction_analytics import (
    RealTimeTransactionMetrics,
    TransactionAnalyticsFilter,
    TransactionTrendAnalysis,
    UserTransactionProfile,
)
from sqlalchemy import desc, func, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ReportingService:
    """트랜잭션 보고서 생성 서비스"""

    async def generate_trend_analysis(
        self, db: AsyncSession, filters: TransactionAnalyticsFilter, days_back: int = 30
    ) -> TransactionTrendAnalysis:
        """트랜드 분석 보고서 생성"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # 일별 트랜드 데이터
            daily_trends = await self._get_daily_trends(
                db, start_date, end_date, filters
            )

            # 성장률 계산
            growth_rates = self._calculate_growth_rates(daily_trends)

            # 예측 데이터 (간단한 선형 예측)
            predictions = self._generate_predictions(daily_trends, 7)  # 7일 예측

            # 주요 통계
            key_metrics = await self._get_trend_key_metrics(
                db, start_date, end_date, filters
            )

            return TransactionTrendAnalysis(
                period_start=start_date,
                period_end=end_date,
                daily_trends=daily_trends,
                growth_rates=growth_rates,
                predictions=predictions,
                key_metrics=key_metrics,
                trend_direction=self._determine_trend_direction(growth_rates),
                volatility_score=self._calculate_volatility(daily_trends),
            )

        except Exception as e:
            logger.error(f"트랜드 분석 생성 중 오류: {str(e)}")
            raise

    async def _get_daily_trends(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        filters: TransactionAnalyticsFilter,
    ) -> List[Dict[str, Any]]:
        """일별 트랜드 데이터 조회"""
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN status = 'COMPLETED' THEN amount ELSE 0 END) as total_volume,
                AVG(CASE WHEN status = 'COMPLETED' THEN amount ELSE NULL END) as avg_transaction_size,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_transactions,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_transactions
            FROM transactions
            WHERE created_at >= :start_date AND created_at <= :end_date
        """

        params = {"start_date": start_date, "end_date": end_date}

        # 필터 조건 추가
        if filters.asset:
            query += " AND asset = :asset"
            params["asset"] = filters.asset
        if filters.transaction_type:
            query += " AND type = :transaction_type"
            params["transaction_type"] = filters.transaction_type.value

        query += " GROUP BY DATE(created_at) ORDER BY DATE(created_at)"

        result = await db.execute(text(query), params)

        return [
            {
                "date": row.date.isoformat(),
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume or 0),
                "avg_transaction_size": float(row.avg_transaction_size or 0),
                "unique_users": row.unique_users,
                "successful_transactions": row.successful_transactions,
                "failed_transactions": row.failed_transactions,
                "success_rate": (
                    row.successful_transactions / row.transaction_count
                    if row.transaction_count > 0
                    else 0
                ),
            }
            for row in result.fetchall()
        ]

    def _calculate_growth_rates(
        self, daily_trends: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """성장률 계산"""
        if len(daily_trends) < 2:
            return {}

        # 최근 7일 평균 vs 이전 7일 평균
        recent_days = daily_trends[-7:] if len(daily_trends) >= 7 else daily_trends
        previous_days = (
            daily_trends[-14:-7] if len(daily_trends) >= 14 else daily_trends[:-7]
        )

        if not previous_days:
            return {}

        def calculate_average(data, field):
            return sum(item[field] for item in data) / len(data) if data else 0

        recent_avg_volume = calculate_average(recent_days, "total_volume")
        previous_avg_volume = calculate_average(previous_days, "total_volume")

        recent_avg_count = calculate_average(recent_days, "transaction_count")
        previous_avg_count = calculate_average(previous_days, "transaction_count")

        return {
            "volume_growth_rate": (
                (recent_avg_volume - previous_avg_volume) / previous_avg_volume * 100
                if previous_avg_volume > 0
                else 0
            ),
            "count_growth_rate": (
                (recent_avg_count - previous_avg_count) / previous_avg_count * 100
                if previous_avg_count > 0
                else 0
            ),
        }

    def _generate_predictions(
        self, daily_trends: List[Dict[str, Any]], days_ahead: int
    ) -> List[Dict[str, Any]]:
        """간단한 선형 예측 생성"""
        if len(daily_trends) < 7:
            return []

        # 최근 7일 데이터로 선형 회귀
        recent_data = daily_trends[-7:]

        # 거래량 트랜드 계산
        volumes = [item["total_volume"] for item in recent_data]
        counts = [item["transaction_count"] for item in recent_data]

        volume_trend = (volumes[-1] - volumes[0]) / 6 if len(volumes) > 1 else 0
        count_trend = (counts[-1] - counts[0]) / 6 if len(counts) > 1 else 0

        predictions = []
        last_date = datetime.fromisoformat(daily_trends[-1]["date"])

        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            predicted_volume = max(0, volumes[-1] + (volume_trend * i))
            predicted_count = max(0, counts[-1] + (count_trend * i))

            predictions.append(
                {
                    "date": future_date.date().isoformat(),
                    "predicted_volume": predicted_volume,
                    "predicted_count": int(predicted_count),
                    "confidence": max(0.3, 1.0 - (i * 0.1)),  # 시간이 지날수록 신뢰도 감소
                }
            )

        return predictions

    async def _get_trend_key_metrics(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        filters: TransactionAnalyticsFilter,
    ) -> Dict[str, Any]:
        """트랜드 주요 지표"""
        query = """
            SELECT
                COUNT(*) as total_transactions,
                SUM(CASE WHEN status = 'COMPLETED' THEN amount ELSE 0 END) as total_volume,
                COUNT(DISTINCT user_id) as total_unique_users,
                MAX(amount) as largest_transaction,
                MIN(CASE WHEN status = 'COMPLETED' AND amount > 0 THEN amount ELSE NULL END) as smallest_transaction,
                AVG(CASE WHEN status = 'COMPLETED' THEN amount ELSE NULL END) as avg_transaction_size
            FROM transactions
            WHERE created_at >= :start_date AND created_at <= :end_date
        """

        params = {"start_date": start_date, "end_date": end_date}

        if filters.asset:
            query += " AND asset = :asset"
            params["asset"] = filters.asset

        result = await db.execute(text(query), params)
        row = result.fetchone()

        return {
            "total_transactions": row.total_transactions,
            "total_volume": float(row.total_volume or 0),
            "total_unique_users": row.total_unique_users,
            "largest_transaction": float(row.largest_transaction or 0),
            "smallest_transaction": float(row.smallest_transaction or 0),
            "avg_transaction_size": float(row.avg_transaction_size or 0),
        }

    def _determine_trend_direction(self, growth_rates: Dict[str, float]) -> str:
        """트랜드 방향 결정"""
        if not growth_rates:
            return "stable"

        volume_growth = growth_rates.get("volume_growth_rate", 0)
        count_growth = growth_rates.get("count_growth_rate", 0)

        avg_growth = (volume_growth + count_growth) / 2

        if avg_growth > 10:
            return "strong_upward"
        elif avg_growth > 3:
            return "upward"
        elif avg_growth > -3:
            return "stable"
        elif avg_growth > -10:
            return "downward"
        else:
            return "strong_downward"

    def _calculate_volatility(self, daily_trends: List[Dict[str, Any]]) -> float:
        """변동성 점수 계산"""
        if len(daily_trends) < 2:
            return 0.0

        volumes = [item["total_volume"] for item in daily_trends]

        # 표준편차를 평균으로 나눈 변동계수
        if not volumes or all(v == 0 for v in volumes):
            return 0.0

        avg_volume = sum(volumes) / len(volumes)
        if avg_volume == 0:
            return 0.0

        variance = sum((v - avg_volume) ** 2 for v in volumes) / len(volumes)
        std_dev = variance**0.5

        return std_dev / avg_volume

    async def generate_user_profile(
        self, db: AsyncSession, user_id: int, days_back: int = 90
    ) -> UserTransactionProfile:
        """사용자 거래 프로필 생성"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # 기본 통계
            basic_stats = await self._get_user_basic_stats(
                db, user_id, start_date, end_date
            )

            # 거래 패턴
            patterns = await self._get_user_patterns(db, user_id, start_date, end_date)

            # 선호 자산
            preferred_assets = await self._get_user_preferred_assets(
                db, user_id, start_date, end_date
            )

            # 리스크 점수
            risk_score = await self._calculate_user_risk_score(
                db, user_id, start_date, end_date
            )

            return UserTransactionProfile(
                user_id=user_id,
                analysis_period_days=days_back,
                basic_stats=basic_stats,
                transaction_patterns=patterns,
                preferred_assets=preferred_assets,
                risk_score=risk_score,
                profile_updated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"사용자 프로필 생성 중 오류: {str(e)}")
            raise

    async def _get_user_basic_stats(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """사용자 기본 통계"""
        result = await db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total_transactions,
                    SUM(CASE WHEN status = 'COMPLETED' THEN amount ELSE 0 END) as total_volume,
                    AVG(CASE WHEN status = 'COMPLETED' THEN amount ELSE NULL END) as avg_transaction_size,
                    MAX(amount) as largest_transaction,
                    COUNT(DISTINCT asset) as unique_assets,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_transactions,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_transactions
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )

        row = result.fetchone()

        return {
            "total_transactions": row.total_transactions,
            "total_volume": float(row.total_volume or 0),
            "avg_transaction_size": float(row.avg_transaction_size or 0),
            "largest_transaction": float(row.largest_transaction or 0),
            "unique_assets": row.unique_assets,
            "success_rate": (
                row.successful_transactions / row.total_transactions
                if row.total_transactions > 0
                else 0
            ),
        }

    async def _get_user_patterns(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """사용자 거래 패턴 분석"""
        # 시간대별 패턴
        hourly_result = await db.execute(
            text(
                """
                SELECT EXTRACT(hour FROM created_at) as hour, COUNT(*) as count
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
                GROUP BY EXTRACT(hour FROM created_at)
                ORDER BY count DESC
                LIMIT 3
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )

        most_active_hours = [
            {"hour": int(row.hour), "transaction_count": row.count}
            for row in hourly_result.fetchall()
        ]

        # 요일별 패턴
        weekday_result = await db.execute(
            text(
                """
                SELECT EXTRACT(dow FROM created_at) as weekday, COUNT(*) as count
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
                GROUP BY EXTRACT(dow FROM created_at)
                ORDER BY count DESC
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )

        weekday_pattern = [
            {"weekday": int(row.weekday), "transaction_count": row.count}
            for row in weekday_result.fetchall()
        ]

        return {
            "most_active_hours": most_active_hours,
            "weekday_pattern": weekday_pattern,
        }

    async def _get_user_preferred_assets(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """사용자 선호 자산"""
        result = await db.execute(
            text(
                """
                SELECT
                    asset,
                    COUNT(*) as transaction_count,
                    SUM(CASE WHEN status = 'COMPLETED' THEN amount ELSE 0 END) as total_volume
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
                GROUP BY asset
                ORDER BY transaction_count DESC
                LIMIT 5
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )

        return [
            {
                "asset": row.asset,
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume or 0),
            }
            for row in result.fetchall()
        ]

    async def _calculate_user_risk_score(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> float:
        """사용자 리스크 점수 계산 (0-100)"""
        # 여러 요소를 고려한 리스크 점수
        risk_factors = {}

        # 1. 거래 빈도 (높을수록 위험)
        frequency_result = await db.execute(
            text(
                """
                SELECT COUNT(*) as transaction_count
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )
        transaction_count = frequency_result.scalar() or 0
        days = (end_date - start_date).days or 1
        daily_avg = transaction_count / days
        risk_factors["frequency"] = min(20, daily_avg * 2)  # 최대 20점

        # 2. 거래 금액 변동성
        volatility_result = await db.execute(
            text(
                """
                SELECT amount
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
                    AND status = 'COMPLETED'
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )
        amounts = [float(row.amount) for row in volatility_result.fetchall()]

        if amounts and len(amounts) > 1:
            avg_amount = sum(amounts) / len(amounts)
            variance = sum((amt - avg_amount) ** 2 for amt in amounts) / len(amounts)
            volatility = (variance**0.5) / avg_amount if avg_amount > 0 else 0
            risk_factors["volatility"] = min(25, volatility * 100)  # 최대 25점
        else:
            risk_factors["volatility"] = 0

        # 3. 실패율
        failure_result = await db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )

        failure_row = failure_result.fetchone()
        if failure_row and failure_row.total > 0:
            failure_rate = failure_row.failed / failure_row.total
            risk_factors["failure_rate"] = failure_rate * 25  # 최대 25점
        else:
            risk_factors["failure_rate"] = 0

        # 4. 비정상 시간대 거래
        unusual_timing_result = await db.execute(
            text(
                """
                SELECT COUNT(*) as unusual_count
                FROM transactions
                WHERE user_id = :user_id
                    AND created_at >= :start_date
                    AND created_at <= :end_date
                    AND EXTRACT(hour FROM created_at) BETWEEN 2 AND 6
            """
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )

        unusual_count = unusual_timing_result.scalar() or 0
        unusual_ratio = unusual_count / max(transaction_count, 1)
        risk_factors["unusual_timing"] = unusual_ratio * 30  # 최대 30점

        # 총 리스크 점수 계산
        total_risk = sum(risk_factors.values())
        return min(100, total_risk)


class ExportService:
    """데이터 내보내기 서비스"""

    async def export_transactions_csv(
        self,
        db: AsyncSession,
        filters: TransactionAnalyticsFilter,
        user_id: Optional[int] = None,
    ) -> str:
        """트랜잭션 데이터 CSV 내보내기"""
        # CSV 생성 로직 (실제 구현에서는 pandas 사용 권장)
        pass

    async def export_analytics_report_pdf(
        self, analytics_data: dict, template_name: str = "default"
    ) -> bytes:
        """분석 보고서 PDF 내보내기"""
        # PDF 생성 로직 (실제 구현에서는 reportlab 사용 권장)
        pass
