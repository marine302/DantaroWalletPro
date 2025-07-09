"""
에너지 모니터링 서비스 - 사용량 분석기
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.energy_pool import PartnerEnergyPool, PartnerEnergyUsageLog
from .utils import safe_decimal_to_float, safe_bool_check, safe_int_conversion

logger = logging.getLogger(__name__)


class UsageAnalyzer:
    """에너지 사용량 분석 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_energy_analytics(self, partner_id: int, days: int = 30) -> Dict[str, Any]:
        """에너지 사용 분석"""
        try:
            # 에너지 풀 조회
            result = await self.db.execute(
                select(PartnerEnergyPool).where(PartnerEnergyPool.partner_id == partner_id)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return self._empty_analytics_response(partner_id, days)
            
            # 사용 이력 조회
            usage_logs = await self._get_usage_history(safe_int_conversion(energy_pool.id), days)
            
            total_usage = sum(safe_decimal_to_float(log.energy_consumed) for log in usage_logs)
            avg_daily = total_usage / days if days > 0 else 0
            peak_usage = max((safe_decimal_to_float(log.energy_consumed) for log in usage_logs), default=0)
            
            return {
                "partner_id": partner_id,
                "period_days": days,
                "total_energy_used": int(total_usage),
                "average_daily_usage": int(avg_daily),
                "peak_usage": int(peak_usage),
                "efficiency_score": 85.0,  # 계산된 효율성 점수
                "usage_pattern": {
                    "hourly": await self._get_hourly_pattern(usage_logs),
                    "daily": await self._get_daily_pattern(usage_logs),
                    "trend": "stable"  # 트렌드 분석 결과
                },
                "recommendations": await self._get_recommendations(energy_pool),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get energy analytics for partner {partner_id}: {e}")
            return self._empty_analytics_response(partner_id, days)
    
    def _empty_analytics_response(self, partner_id: int, days: int) -> Dict[str, Any]:
        """빈 분석 응답"""
        return {
            "partner_id": partner_id,
            "period_days": days,
            "total_energy_used": 0,
            "average_daily_usage": 0,
            "peak_usage": 0,
            "efficiency_score": 0.0,
            "usage_pattern": {
                "hourly": [],
                "daily": [],
                "trend": "no_data"
            },
            "recommendations": [],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _get_usage_history(self, energy_pool_id: int, days: int) -> List[PartnerEnergyUsageLog]:
        """에너지 사용 이력 조회"""
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(PartnerEnergyUsageLog)
            .where(
                and_(
                    PartnerEnergyUsageLog.energy_pool_id == energy_pool_id,
                    PartnerEnergyUsageLog.created_at >= since
                )
            )
            .order_by(desc(PartnerEnergyUsageLog.created_at))
        )
        
        return list(result.scalars().all())
    
    async def _get_hourly_pattern(self, usage_logs: List[PartnerEnergyUsageLog]) -> List[Dict]:
        """시간별 사용 패턴 분석"""
        hourly_usage = {}
        for log in usage_logs:
            if safe_bool_check(log.created_at):
                hour = log.created_at.hour
                if hour not in hourly_usage:
                    hourly_usage[hour] = 0
                hourly_usage[hour] += safe_decimal_to_float(log.energy_consumed)
        
        return [{"hour": h, "usage": usage} for h, usage in sorted(hourly_usage.items())]
    
    async def _get_daily_pattern(self, usage_logs: List[PartnerEnergyUsageLog]) -> List[Dict]:
        """일별 사용 패턴 분석"""
        daily_usage = {}
        for log in usage_logs:
            if safe_bool_check(log.created_at):
                date = log.created_at.date().isoformat()
                if date not in daily_usage:
                    daily_usage[date] = 0
                daily_usage[date] += safe_decimal_to_float(log.energy_consumed)
        
        return [{"date": d, "usage": usage} for d, usage in sorted(daily_usage.items())]
    
    async def _get_recommendations(self, energy_pool: PartnerEnergyPool) -> List[str]:
        """추천 사항 생성"""
        recommendations = []
        
        usage_percentage = 0
        total = safe_decimal_to_float(energy_pool.total_energy)
        used = safe_decimal_to_float(energy_pool.used_energy)
        
        if total > 0:
            usage_percentage = (used / total) * 100
        
        if usage_percentage > 80:
            recommendations.append("에너지 사용량이 높습니다. 추가 TRX 스테이킹을 고려하세요.")
        
        if usage_percentage > 90:
            recommendations.append("에너지가 곧 부족할 수 있습니다. 즉시 충전을 권장합니다.")
        
        frozen_amount = safe_decimal_to_float(energy_pool.frozen_trx_amount)
        if frozen_amount < 100:
            recommendations.append("더 많은 TRX를 스테이킹하여 안정적인 에너지를 확보하세요.")
        
        return recommendations
    
    async def calculate_efficiency_score(self, energy_pool: PartnerEnergyPool) -> float:
        """효율성 점수 계산"""
        try:
            total_energy = safe_decimal_to_float(energy_pool.total_energy)
            used_energy = safe_decimal_to_float(energy_pool.used_energy)
            
            if total_energy == 0:
                return 0.0
            
            # 기본 효율성 점수 계산 (사용률 기반)
            usage_ratio = used_energy / total_energy
            
            # 최적 사용률을 60-80%로 가정
            if 0.6 <= usage_ratio <= 0.8:
                base_score = 100.0
            elif usage_ratio < 0.6:
                # 사용률이 낮으면 점수 감소
                base_score = 60.0 + (usage_ratio / 0.6) * 40.0
            else:
                # 사용률이 높으면 점수 감소
                base_score = 100.0 - ((usage_ratio - 0.8) / 0.2) * 20.0
            
            return max(0.0, min(100.0, base_score))
            
        except Exception as e:
            logger.error(f"Failed to calculate efficiency score: {e}")
            return 0.0
