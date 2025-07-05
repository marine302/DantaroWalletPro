"""
트렌드 분석 보고서 생성 모듈
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.schemas.transaction_analytics import (
    TransactionAnalyticsFilter,
    TransactionTrendAnalysis,
)
from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TrendReportService:
    """트렌드 분석 보고서 생성 서비스"""

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
            )

        except Exception as e:
            logger.error(f"트렌드 분석 생성 실패: {str(e)}")
            raise

    async def _get_daily_trends(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        filters: TransactionAnalyticsFilter,
    ) -> List[Dict[str, Any]]:
        """일별 트렌드 데이터 조회"""
        query = text("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as transaction_count,
            SUM(amount) as total_volume,
            AVG(amount) as avg_transaction_size,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_transactions,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_transactions
        FROM transactions 
        WHERE created_at >= :start_date 
        AND created_at <= :end_date
        GROUP BY DATE(created_at)
        ORDER BY date
        """)

        result = await db.execute(
            query, {"start_date": start_date, "end_date": end_date}
        )

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
        if len(daily_trends) < 3:
            return []

        # 최근 7일 데이터로 선형 트렌드 계산
        recent_data = daily_trends[-7:] if len(daily_trends) >= 7 else daily_trends
        
        # 간단한 선형 회귀 (최소제곱법)
        n = len(recent_data)
        x_values = list(range(n))
        y_volume = [item["total_volume"] for item in recent_data]
        y_count = [item["transaction_count"] for item in recent_data]

        # 평균 계산
        x_mean = sum(x_values) / n
        y_volume_mean = sum(y_volume) / n
        y_count_mean = sum(y_count) / n

        # 기울기 계산 (volume)
        numerator_volume = sum((x - x_mean) * (y - y_volume_mean) for x, y in zip(x_values, y_volume))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        slope_volume = numerator_volume / denominator if denominator != 0 else 0

        # 기울기 계산 (count)
        numerator_count = sum((x - x_mean) * (y - y_count_mean) for x, y in zip(x_values, y_count))
        slope_count = numerator_count / denominator if denominator != 0 else 0

        # 예측 생성
        predictions = []
        last_date = datetime.fromisoformat(daily_trends[-1]["date"])
        
        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            future_x = n + i - 1
            
            predicted_volume = max(0, y_volume_mean + slope_volume * (future_x - x_mean))
            predicted_count = max(0, y_count_mean + slope_count * (future_x - x_mean))
            
            predictions.append({
                "date": future_date.isoformat(),
                "predicted_volume": predicted_volume,
                "predicted_count": int(predicted_count),
                "confidence": max(0.1, 0.9 - (i * 0.1))  # 신뢰도는 시간에 따라 감소
            })

        return predictions

    async def _get_trend_key_metrics(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        filters: TransactionAnalyticsFilter,
    ) -> Dict[str, Any]:
        """트렌드 주요 지표 계산"""
        # 전체 기간 통계
        total_result = await db.execute(
            text("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(amount) as total_volume,
                AVG(amount) as avg_transaction_size,
                COUNT(DISTINCT user_id) as unique_users
            FROM transactions 
            WHERE created_at >= :start_date AND created_at <= :end_date
            """),
            {"start_date": start_date, "end_date": end_date}
        )
        
        total_stats = total_result.fetchone()
        
        return {
            "total_transactions": total_stats.total_transactions,
            "total_volume": float(total_stats.total_volume or 0),
            "avg_transaction_size": float(total_stats.avg_transaction_size or 0),
            "unique_users": total_stats.unique_users,
            "period_days": (end_date - start_date).days,
        }
