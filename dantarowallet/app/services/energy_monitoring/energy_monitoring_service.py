"""
에너지 모니터링 서비스 - 메인 클래스 (리팩토링된 버전)
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.energy_pool import PartnerEnergyPool, EnergyPrediction
from .energy_pool_manager import EnergyPoolManager
from .usage_analyzer import UsageAnalyzer
from .prediction_service import EnergyPredictionService
from .utils import (
    safe_decimal_to_int, safe_decimal_to_float, safe_enum_value,
    safe_datetime_isoformat, safe_int_conversion
)

logger = logging.getLogger(__name__)


class EnergyMonitoringService:
    """Doc #25: 에너지 풀 고급 관리 시스템 (모듈화된 버전)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pool_manager = EnergyPoolManager(db)
        self.usage_analyzer = UsageAnalyzer(db)
        self.prediction_service = EnergyPredictionService(db)
    
    async def monitor_partner_energy(self, partner_id: int) -> Dict[str, Any]:
        """파트너 에너지 실시간 모니터링"""
        try:
            # 에너지 풀 조회 또는 생성
            energy_pool = await self.pool_manager.get_or_create_energy_pool(partner_id)
            
            # 실시간 블록체인 데이터로 업데이트
            await self.pool_manager.update_energy_pool_from_blockchain(energy_pool)
            
            # 예측 데이터 조회
            pool_id = safe_int_conversion(energy_pool.id)
            prediction = await self.prediction_service.get_latest_prediction(pool_id)
            
            return {
                "partner_id": partner_id,
                "energy_pool": {
                    "id": energy_pool.id,
                    "wallet_address": energy_pool.wallet_address,
                    "total_energy": safe_decimal_to_int(energy_pool.total_energy),
                    "available_energy": safe_decimal_to_int(energy_pool.available_energy),
                    "used_energy": safe_decimal_to_int(energy_pool.used_energy),
                    "total_bandwidth": safe_decimal_to_int(energy_pool.total_bandwidth),
                    "available_bandwidth": safe_decimal_to_int(energy_pool.available_bandwidth),
                    "daily_average_usage": safe_decimal_to_int(energy_pool.daily_average_usage),
                    "frozen_trx_amount": safe_decimal_to_float(energy_pool.frozen_trx_amount),
                    "status": safe_enum_value(energy_pool.status),
                    "warning_threshold": energy_pool.warning_threshold or 30,
                    "critical_threshold": energy_pool.critical_threshold or 10
                },
                "predictions": {
                    "predicted_usage": safe_decimal_to_int(prediction.predicted_usage) if prediction else 0,
                    "depletion_estimated_at": safe_datetime_isoformat(prediction.predicted_depletion) if prediction else None,
                    "confidence_score": safe_decimal_to_float(prediction.confidence_score) if prediction else 0,
                    "hours_remaining": self.pool_manager.calculate_hours_remaining(energy_pool),
                },
                "last_checked": safe_datetime_isoformat(energy_pool.last_checked_at)
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor partner energy for {partner_id}: {e}")
            raise
    
    async def get_energy_analytics(self, partner_id: int, days: int = 30) -> Dict[str, Any]:
        """에너지 사용 분석 (UsageAnalyzer로 위임)"""
        return await self.usage_analyzer.get_energy_analytics(partner_id, days)
    
    async def monitor_all_partners(self) -> Dict[str, Any]:
        """모든 파트너 모니터링"""
        try:
            # 모든 파트너 에너지 풀 조회
            energy_pools = await self.pool_manager.get_all_energy_pools()
            
            partner_statuses = []
            total_critical = 0
            total_warning = 0
            total_sufficient = 0
            
            for pool in energy_pools:
                status_info = {
                    "partner_id": pool.partner_id,
                    "status": safe_enum_value(pool.status),
                    "available_energy": safe_decimal_to_int(pool.available_energy),
                    "total_energy": safe_decimal_to_int(pool.total_energy),
                    "usage_percentage": 0
                }
                
                total = safe_decimal_to_float(pool.total_energy)
                used = safe_decimal_to_float(pool.used_energy)
                if total > 0:
                    status_info["usage_percentage"] = int((used / total) * 100)
                
                partner_statuses.append(status_info)
                
                # 상태별 카운트
                status_str = safe_enum_value(pool.status)
                if status_str == "critical":
                    total_critical += 1
                elif status_str == "warning":
                    total_warning += 1
                else:
                    total_sufficient += 1
            
            return {
                "success": True,
                "summary": {
                    "total_partners": len(energy_pools),
                    "critical": total_critical,
                    "warning": total_warning,
                    "sufficient": total_sufficient
                },
                "partner_statuses": partner_statuses,
                "monitored_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor all partners: {e}")
            return {
                "success": False,
                "error": str(e),
                "monitored_at": datetime.utcnow().isoformat()
            }
    
    async def generate_partner_prediction(self, partner_id: int) -> Optional[EnergyPrediction]:
        """파트너 에너지 예측 생성"""
        try:
            energy_pool = await self.pool_manager.get_or_create_energy_pool(partner_id)
            pool_id = safe_int_conversion(energy_pool.id)
            return await self.prediction_service.generate_prediction(pool_id)
        except Exception as e:
            logger.error(f"Failed to generate prediction for partner {partner_id}: {e}")
            return None


# 하위 호환성을 위한 별칭
EnergyPredictionService = EnergyPredictionService
