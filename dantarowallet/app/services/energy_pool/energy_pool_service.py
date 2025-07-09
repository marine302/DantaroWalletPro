"""
에너지 풀 관리 서비스 - 모듈화된 메인 서비스
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_pool import EnergyPoolModel, EnergyPoolStatus
from app.models.user import User
from app.schemas.energy import (
    CreateEnergyPoolRequest, EnergyPoolResponse, EnergyPoolStatusResponse,
    EnergyUsageStatsResponse, EnergyUsageLogResponse, EnergySimulationRequest,
    EnergySimulationResponse, AutoManagementSettings, EnergyPriceHistoryResponse,
    EnergyAlertResponse, MessageResponse
)
from app.core.exceptions import EnergyInsufficientError, ValidationError

from .pool_manager import EnergyPoolManager
from .usage_analyzer import EnergyUsageAnalyzer
from .queue_manager import EnergyQueueManager
from .models import (
    EnergyPoolStatusInfo, EnergyTransaction, EnergyQueue, EnergyAlert,
    EnergyUsageStats, EnergyRechargeRequest, EnergyQueueCreate,
    EmergencyWithdrawalCreate, EmergencyWithdrawalResponse
)

logger = logging.getLogger(__name__)


class EnergyPoolModelService:
    """에너지 풀 관리 서비스 (모듈화된 버전)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pool_manager = EnergyPoolManager(db)
        self.usage_analyzer = EnergyUsageAnalyzer(db)
        self.queue_manager = EnergyQueueManager(db)
    
    async def get_energy_status(self) -> EnergyPoolStatusInfo:
        """현재 에너지 풀 상태를 조회합니다."""
        return await self.pool_manager.get_energy_status()
    
    async def consume_energy(
        self, amount: int, transaction_type: str, user_id: int, transaction_id: str
    ) -> bool:
        """에너지를 소모합니다."""
        return await self.pool_manager.consume_energy(amount, transaction_type, user_id, transaction_id)
    
    async def get_usage_stats(self, user_id: int) -> EnergyUsageStats:
        """사용자 에너지 사용 통계를 조회합니다."""
        return await self.usage_analyzer.get_usage_stats(user_id)
    
    async def add_to_queue(self, user_id: int, queue_data: EnergyQueueCreate) -> EnergyQueue:
        """대기열에 추가합니다."""
        return await self.queue_manager.add_to_queue(user_id, queue_data)
    
    async def get_queue_status(self, user_id: int) -> Optional[Any]:
        """사용자의 대기열 상태를 조회합니다."""
        return await self.queue_manager.get_queue_status(user_id)
    
    async def create_energy_pool(self, request: CreateEnergyPoolRequest) -> EnergyPoolModel:
        """새로운 에너지 풀을 생성합니다."""
        try:
            # 안전하게 속성 접근
            pool_name = getattr(request, 'pool_name', 'Default Pool')
            owner_address = getattr(request, 'owner_address', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
            total_energy = getattr(request, 'total_energy', 1000000)
            frozen_trx = getattr(request, 'frozen_trx', Decimal('1000'))
            warning_threshold = getattr(request, 'warning_threshold', 20) or 20
            critical_threshold = getattr(request, 'critical_threshold', 10) or 10
            
            energy_pool = EnergyPoolModel(
                pool_name=pool_name,
                owner_address=owner_address,
                total_energy=total_energy,
                available_energy=total_energy,
                used_energy=0,
                frozen_trx=frozen_trx,
                status=EnergyPoolStatus.ACTIVE,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                created_at=datetime.utcnow()
            )
            
            self.db.add(energy_pool)
            await self.db.commit()
            await self.db.refresh(energy_pool)
            
            logger.info(f"에너지 풀 생성 완료: {energy_pool.pool_name}")
            return energy_pool
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"에너지 풀 생성 실패: {e}")
            raise
    
    async def get_energy_pool_by_id(self, pool_id: int) -> Optional[EnergyPoolModel]:
        """ID로 에너지 풀을 조회합니다."""
        return await self.pool_manager.get_energy_pool_by_id(pool_id)
    
    async def update_energy_pool_status(self, pool_id: int, status: EnergyPoolStatus) -> bool:
        """에너지 풀 상태를 업데이트합니다."""
        return await self.pool_manager.update_energy_pool_status(pool_id, status)
    
    async def get_energy_pools(self, limit: int = 10, offset: int = 0) -> List[EnergyPoolModel]:
        """에너지 풀 목록을 조회합니다."""
        return await self.pool_manager.get_energy_pools(limit, offset)
    
    async def recharge_energy(self, user_id: int, request: EnergyRechargeRequest) -> bool:
        """에너지를 충전합니다."""
        try:
            # 충전 로직 구현
            # 실제로는 TRX 결제 처리 후 에너지 추가
            
            logger.info(f"사용자 {user_id} 에너지 충전: {request.amount}")
            return True
            
        except Exception as e:
            logger.error(f"에너지 충전 실패: {e}")
            return False
    
    async def simulate_energy_usage(self, request: EnergySimulationRequest) -> Dict[str, Any]:
        """에너지 사용 시뮬레이션"""
        try:
            # 현재 상태 조회
            current_status = await self.get_energy_status()
            
            # 안전하게 속성 접근
            estimated_usage = getattr(request, 'estimated_usage', 0)
            
            # 시뮬레이션 계산
            available_after = current_status.available_energy - estimated_usage
            total_used = current_status.total_energy - current_status.available_energy + estimated_usage
            usage_rate_after = (total_used / current_status.total_energy * 100) if current_status.total_energy > 0 else 0
            
            # 예상 결과
            simulation_result = {
                "success": available_after >= 0,
                "available_energy_after": max(0, available_after),
                "usage_rate_after": usage_rate_after,
                "estimated_cost": estimated_usage * 0.001,  # 가정: 1 에너지 = 0.001 TRX
                "recommended_action": self._get_recommendation(usage_rate_after)
            }
            
            return simulation_result
            
        except Exception as e:
            logger.error(f"에너지 사용 시뮬레이션 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_recommendation(self, usage_rate: float) -> str:
        """사용률에 따른 추천 사항"""
        if usage_rate < 50:
            return "충분한 에너지가 있습니다."
        elif usage_rate < 80:
            return "에너지 사용량을 모니터링하세요."
        elif usage_rate < 95:
            return "에너지 충전을 고려하세요."
        else:
            return "즉시 에너지 충전이 필요합니다."
    
    async def get_alerts(self, user_id: int) -> List[EnergyAlert]:
        """사용자 알림 조회"""
        try:
            # 현재 상태 기반 알림 생성
            status = await self.get_energy_status()
            alerts = []
            
            if status.usage_rate > 90:
                alerts.append(EnergyAlert(
                    alert_type="CRITICAL",
                    message="에너지 사용률이 90%를 초과했습니다. 즉시 충전하세요.",
                    is_active=True
                ))
            elif status.usage_rate > 80:
                alerts.append(EnergyAlert(
                    alert_type="WARNING",
                    message="에너지 사용률이 80%를 초과했습니다. 충전을 고려하세요.",
                    is_active=True
                ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"알림 조회 실패: {e}")
            return []
    
    async def emergency_withdrawal(self, user_id: int, request: EmergencyWithdrawalCreate) -> EmergencyWithdrawalResponse:
        """긴급 출금 처리"""
        try:
            # 긴급 출금 로직 구현
            # 실제로는 관리자 승인 후 처리
            
            transaction_id = f"emergency_{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"긴급 출금 요청: 사용자 {user_id}, 금액 {request.amount}")
            
            return EmergencyWithdrawalResponse(
                success=True,
                transaction_id=transaction_id,
                message="긴급 출금 요청이 접수되었습니다. 관리자 승인 후 처리됩니다."
            )
            
        except Exception as e:
            logger.error(f"긴급 출금 처리 실패: {e}")
            return EmergencyWithdrawalResponse(
                success=False,
                transaction_id="",
                message=f"긴급 출금 처리 실패: {str(e)}"
            )
    
    async def get_hourly_usage_pattern(self, user_id: int) -> Dict[int, int]:
        """시간별 사용 패턴 조회"""
        return await self.usage_analyzer.get_hourly_usage_pattern(user_id)
    
    async def get_daily_usage_trend(self, user_id: int) -> List[Dict[str, Any]]:
        """일별 사용량 트렌드 조회"""
        return await self.usage_analyzer.get_daily_usage_trend(user_id)
    
    async def get_queue_statistics(self) -> dict:
        """대기열 통계"""
        return await self.queue_manager.get_queue_statistics()
    
    async def cleanup_old_queue_items(self) -> int:
        """오래된 대기열 항목 정리"""
        return await self.queue_manager.cleanup_old_queue_items()
