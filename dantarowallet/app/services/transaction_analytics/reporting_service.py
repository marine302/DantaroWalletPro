"""
트랜잭션 보고서 생성 서비스 (통합 라우터)

기존 550줄의 ReportingService를 기능별로 분할:
- trend_reports.py: 트렌드 분석 보고서
- user_reports.py: 사용자 분석 보고서

이 파일은 백워드 호환성을 위한 통합 인터페이스입니다.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.schemas.transaction_analytics import (
    TransactionAnalyticsFilter,
    TransactionTrendAnalysis,
    UserTransactionProfile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .reports import get_trend_report_service, get_user_report_service

logger = logging.getLogger(__name__)


class ReportingService:
    """트랜잭션 보고서 생성 서비스 (통합 인터페이스)"""

    def __init__(self):
        self.trend_service = get_trend_report_service()
        self.user_service = get_user_report_service()

    async def generate_trend_analysis(
        self, db: AsyncSession, filters: TransactionAnalyticsFilter, days_back: int = 30
    ) -> TransactionTrendAnalysis:
        """트렌드 분석 보고서 생성"""
        return await self.trend_service.generate_trend_analysis(db, filters, days_back)

    async def generate_user_profile(
        self, db: AsyncSession, user_id: int, days_back: int = 30
    ) -> UserTransactionProfile:
        """사용자 거래 프로필 생성"""
        return await self.user_service.generate_user_profile(db, user_id, days_back)

    async def generate_top_users_report(
        self, db: AsyncSession, limit: int = 50, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """상위 사용자 보고서 생성"""
        return await self.user_service.generate_top_users_report(db, limit, days_back)

    async def generate_financial_summary(
        self, db: AsyncSession, days_back: int = 30
    ) -> Dict[str, Any]:
        """재무 요약 보고서 생성 (간단 버전)"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # 기본 필터 생성
            filters = TransactionAnalyticsFilter()
            
            # 트렌드 분석 데이터 활용
            trend_analysis = await self.generate_trend_analysis(db, filters, days_back)
            
            return {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "summary": {
                    "total_transactions": trend_analysis.key_metrics.get("total_transactions", 0),
                    "total_volume": trend_analysis.key_metrics.get("total_volume", 0),
                    "avg_daily_volume": (
                        trend_analysis.key_metrics.get("total_volume", 0) / days_back
                        if days_back > 0 else 0
                    ),
                    "unique_users": trend_analysis.key_metrics.get("unique_users", 0),
                },
                "growth_metrics": trend_analysis.growth_rates,
            }

        except Exception as e:
            logger.error(f"재무 요약 보고서 생성 실패: {str(e)}")
            raise

    async def generate_real_time_metrics(
        self, db: AsyncSession
    ) -> Dict[str, Any]:
        """실시간 메트릭 생성"""
        try:
            # 최근 24시간 데이터
            filters = TransactionAnalyticsFilter()
            trend_analysis = await self.generate_trend_analysis(db, filters, 1)
            
            if not trend_analysis.daily_trends:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_users": 0,
                    "transactions_last_hour": 0,
                    "volume_last_hour": 0,
                    "average_transaction_size": 0,
                }
            
            latest_data = trend_analysis.daily_trends[-1]
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "active_users": latest_data.get("unique_users", 0),
                "transactions_last_hour": latest_data.get("transaction_count", 0) // 24,  # 대략적 계산
                "volume_last_hour": latest_data.get("total_volume", 0) / 24,  # 대략적 계산
                "average_transaction_size": latest_data.get("avg_transaction_size", 0),
                "success_rate": latest_data.get("success_rate", 0),
            }

        except Exception as e:
            logger.error(f"실시간 메트릭 생성 실패: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Unable to generate real-time metrics",
            }
