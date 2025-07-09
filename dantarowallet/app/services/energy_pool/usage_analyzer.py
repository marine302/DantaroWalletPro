"""
에너지 풀 서비스 - 사용량 분석기
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.models.energy_pool import EnergyUsageLog
from .utils import safe_int, safe_get_attr
from .models import EnergyUsageStats

logger = logging.getLogger(__name__)


class EnergyUsageAnalyzer:
    """에너지 사용량 분석 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_usage_stats(self, user_id: int, days: int = 30) -> EnergyUsageStats:
        """사용자 에너지 사용 통계 조회"""
        try:
            # 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 사용 로그 조회
            result = await self.db.execute(
                select(EnergyUsageLog)
                .where(
                    and_(
                        EnergyUsageLog.user_id == user_id,
                        EnergyUsageLog.created_at >= start_date,
                        EnergyUsageLog.created_at <= end_date
                    )
                )
                .order_by(desc(EnergyUsageLog.created_at))
            )
            usage_logs = list(result.scalars().all())
            
            # 통계 계산
            daily_usage = sum(safe_int(safe_get_attr(log, 'energy_amount'), 0) for log in usage_logs)
            transaction_count = len(usage_logs)
            
            # 시간별 사용량 분석
            hourly_usage = {}
            for log in usage_logs:
                try:
                    hour = log.created_at.hour
                    energy_amount = safe_int(safe_get_attr(log, 'energy_amount'), 0)
                    hourly_usage[hour] = hourly_usage.get(hour, 0) + energy_amount
                except Exception:
                    continue
            
            # 피크 시간 계산
            peak_hour = max(hourly_usage.keys(), key=lambda h: hourly_usage[h]) if hourly_usage else 12
            
            # 효율성 점수 계산
            efficiency_score = self._calculate_efficiency_score(daily_usage, transaction_count)
            
            # 비용 분석
            cost_breakdown = self._calculate_cost_breakdown(usage_logs)
            
            return EnergyUsageStats(
                daily_usage=daily_usage,
                transaction_count=transaction_count,
                efficiency_score=efficiency_score,
                peak_hour=peak_hour,
                cost_breakdown=cost_breakdown
            )
            
        except Exception as e:
            logger.error(f"에너지 사용 통계 조회 실패: {e}")
            return EnergyUsageStats(
                daily_usage=0,
                transaction_count=0,
                efficiency_score=0.0,
                peak_hour=12,
                cost_breakdown={}
            )
    
    def _calculate_efficiency_score(self, daily_usage: int, transaction_count: int) -> float:
        """효율성 점수 계산"""
        if transaction_count == 0:
            return 0.0
        
        # 트랜잭션당 평균 에너지 사용량
        avg_per_transaction = daily_usage / transaction_count
        
        # 효율성 점수 (낮은 에너지 사용량일수록 높은 점수)
        if avg_per_transaction <= 100:
            return 95.0
        elif avg_per_transaction <= 500:
            return 85.0
        elif avg_per_transaction <= 1000:
            return 75.0
        else:
            return 65.0
    
    def _calculate_cost_breakdown(self, usage_logs: List[EnergyUsageLog]) -> Dict[str, float]:
        """비용 분석"""
        cost_breakdown = {
            "transaction_cost": 0.0,
            "energy_cost": 0.0,
            "total_cost": 0.0
        }
        
        try:
            total_energy = sum(safe_int(safe_get_attr(log, 'energy_amount'), 0) for log in usage_logs)
            
            # 가정: 1 에너지 = 0.001 TRX
            energy_cost = total_energy * 0.001
            transaction_cost = len(usage_logs) * 0.01  # 트랜잭션당 0.01 TRX
            
            cost_breakdown["transaction_cost"] = transaction_cost
            cost_breakdown["energy_cost"] = energy_cost
            cost_breakdown["total_cost"] = transaction_cost + energy_cost
            
        except Exception as e:
            logger.error(f"비용 분석 실패: {e}")
        
        return cost_breakdown
    
    async def get_hourly_usage_pattern(self, user_id: int, days: int = 7) -> Dict[int, int]:
        """시간별 사용 패턴 조회"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            result = await self.db.execute(
                select(EnergyUsageLog)
                .where(
                    and_(
                        EnergyUsageLog.user_id == user_id,
                        EnergyUsageLog.created_at >= start_date,
                        EnergyUsageLog.created_at <= end_date
                    )
                )
            )
            usage_logs = list(result.scalars().all())
            
            hourly_pattern = {}
            for log in usage_logs:
                try:
                    hour = log.created_at.hour
                    energy_amount = safe_int(safe_get_attr(log, 'energy_amount'), 0)
                    hourly_pattern[hour] = hourly_pattern.get(hour, 0) + energy_amount
                except Exception:
                    continue
            
            return hourly_pattern
            
        except Exception as e:
            logger.error(f"시간별 사용 패턴 조회 실패: {e}")
            return {}
    
    async def get_daily_usage_trend(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """일별 사용량 트렌드 조회"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            result = await self.db.execute(
                select(EnergyUsageLog)
                .where(
                    and_(
                        EnergyUsageLog.user_id == user_id,
                        EnergyUsageLog.created_at >= start_date,
                        EnergyUsageLog.created_at <= end_date
                    )
                )
                .order_by(EnergyUsageLog.created_at)
            )
            usage_logs = list(result.scalars().all())
            
            daily_usage = {}
            for log in usage_logs:
                try:
                    date = log.created_at.date()
                    energy_amount = safe_int(safe_get_attr(log, 'energy_amount'), 0)
                    daily_usage[date] = daily_usage.get(date, 0) + energy_amount
                except Exception:
                    continue
            
            # 결과 정렬
            trend_data = []
            for date, usage in sorted(daily_usage.items()):
                trend_data.append({
                    "date": date.isoformat(),
                    "usage": usage
                })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"일별 사용량 트렌드 조회 실패: {e}")
            return []
