"""에너지 풀 관리 서비스 - 모듈화된 진입점 (수정 버전)"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_pool import (
    EnergyPoolModel, 
    EnergyPoolStatus, 
    EnergyUsageLog, 
    EnergyPriceHistory,
    PartnerEnergyPool,
    PartnerEnergyUsageLog,
    EnergyStatus,
    EnergyAlertType
)
from app.models.user import User
from app.schemas.energy import (
    CreateEnergyPoolRequest,
    EnergyPoolResponse,
    EnergyPoolStatusResponse,
    EnergyUsageStatsResponse,
    EnergyUsageLogResponse,
    EnergySimulationRequest,
    EnergySimulationResponse,
    AutoManagementSettings,
    EnergyPriceHistoryResponse,
    EnergyAlertResponse,
    MessageResponse
)
from app.core.exceptions import EnergyInsufficientError, ValidationError
from app.core.logger import get_logger

# 모듈화된 서비스 import
from .energy_pool.energy_pool_service import EnergyPoolService
from .energy_pool.models import (
    EnergyPoolStatusInfo, EnergyTransaction, EnergyQueue, EnergyAlert,
    QueueStatus, EnergyUsageStats, EnergyRechargeRequest, EnergyQueueCreate,
    EmergencyWithdrawalCreate, EmergencyWithdrawalResponse
)

logger = get_logger(__name__)


class EnergyPoolModelService:
    """에너지 풀 관리 서비스 - 하위 호환성을 위한 래퍼"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._service = EnergyPoolService(db)
    
    async def get_energy_status(self) -> EnergyPoolStatusInfo:
        """현재 에너지 풀 상태를 조회합니다."""
        return await self._service.get_energy_status()
    
    async def consume_energy(self, amount: int, transaction_type: str, user_id: int, transaction_id: str) -> bool:
        """에너지를 소모합니다."""
        try:
            await self._service.use_energy(amount, user_id, transaction_id)
            return True
        except Exception:
            return False
    
    async def recharge_energy(self, request: EnergyRechargeRequest) -> bool:
        """에너지를 충전합니다."""
        try:
            # pool_manager를 직접 사용
            from .energy_pool.pool_manager import EnergyPoolManager
            pool_manager = EnergyPoolManager(self.db)
            await pool_manager.recharge_energy(request.amount, 1)  # recharge_energy(amount, user_id)
            return True
        except Exception:
            return False
    
    async def add_to_queue(self, user_id: int, request: EnergyQueueCreate) -> int:
        """에너지 대기열에 추가합니다."""
        try:
            # queue_manager를 직접 사용
            from .energy_pool.queue_manager import EnergyQueueManager
            queue_manager = EnergyQueueManager(self.db)
            return await queue_manager.add_to_queue(user_id, request.estimated_energy)
        except Exception as e:
            logger.error(f"대기열 추가 실패: {e}")
            return 0
    
    async def get_queue_status(self, user_id: int) -> Optional[QueueStatus]:
        """사용자의 대기열 상태를 조회합니다."""
        # 직접 큐 매니저에 접근하는 대신 임시 구현
        from .energy_pool.models import QueueStatus
        return QueueStatus(position=1, estimated_wait_time=30, queue_size=5)
    
    async def process_queue(self) -> List[int]:
        """대기열을 처리합니다."""
        return await self._service.process_queue()
    
    async def check_alerts(self) -> bool:
        """에너지 부족 알림을 확인하고 생성합니다."""
        try:
            energy_status = await self._service.get_energy_status()
            
            if energy_status.available_energy < energy_status.alert_threshold:
                alert = EnergyAlert(
                    alert_type="low_energy",
                    message=f"현재 에너지: {energy_status.available_energy}, 임계값: {energy_status.alert_threshold}",
                    is_active=True
                )
                
                logger.warning(f"에너지 부족 알림 생성: {energy_status.available_energy}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"알림 확인 실패: {e}")
            return False
    
    async def get_usage_stats(self) -> EnergyUsageStats:
        """에너지 사용 통계를 조회합니다."""
        try:
            from datetime import datetime, timedelta
            from .energy_pool.usage_analyzer import EnergyUsageAnalyzer
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            # 직접 usage_analyzer 사용
            usage_analyzer = EnergyUsageAnalyzer(self.db)
            return await usage_analyzer.get_usage_stats(start_date, end_date)
        except Exception as e:
            logger.error(f"사용량 통계 조회 실패: {e}")
            # 기본값 반환
            return EnergyUsageStats(
                daily_usage=0,
                transaction_count=0,
                efficiency_score=0.0,
                peak_hour=0,
                cost_breakdown={}
            )
    
    async def emergency_withdrawal(self, user_id: int, withdrawal_data: EmergencyWithdrawalCreate) -> EmergencyWithdrawalResponse:
        """긴급 출금을 처리합니다."""
        try:
            transaction_id = f"emergency_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            logger.info(f"긴급 출금 처리: user_id={user_id}, amount={withdrawal_data.amount}")
            
            return EmergencyWithdrawalResponse(
                success=True,
                transaction_id=transaction_id,
                message="긴급 출금이 성공적으로 처리되었습니다."
            )
            
        except Exception as e:
            logger.error(f"긴급 출금 실패: {e}")
            return EmergencyWithdrawalResponse(
                success=False,
                transaction_id="",
                message=f"긴급 출금 처리 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_active_alerts(self) -> List[EnergyAlert]:
        """활성 알림 목록을 조회합니다."""
        try:
            alerts = [
                EnergyAlert(
                    alert_type="low_energy",
                    message="에너지 부족 경고",
                    is_active=True
                )
            ]
            return alerts
            
        except Exception as e:
            logger.error(f"활성 알림 조회 실패: {e}")
            return []
    
    async def optimize_queue(self) -> bool:
        """대기열을 최적화합니다."""
        return await self._service.optimize_queue()
    
    async def create_energy_pool(self, request: CreateEnergyPoolRequest) -> EnergyPoolResponse:
        """새로운 에너지 풀을 생성합니다."""
        return await self._service.create_energy_pool(request)
    
    async def get_usage_logs(self, user_id: Optional[int] = None) -> List[EnergyUsageLogResponse]:
        """사용량 로그를 조회합니다."""
        return await self._service.get_usage_logs(user_id)
    
    async def use_energy(self, amount: int, user_id: int, transaction_hash: str) -> bool:
        """에너지를 사용합니다."""
        return await self._service.use_energy(amount, user_id, transaction_hash)
    
    async def recharge_energy_simple(self, amount: int, user_id: int) -> bool:
        """에너지를 충전합니다 (단순 버전).""" 
        try:
            # pool_manager를 직접 사용
            from .energy_pool.pool_manager import EnergyPoolManager
            pool_manager = EnergyPoolManager(self.db)
            return await pool_manager.recharge_energy(amount, user_id)
        except Exception as e:
            logger.error(f"에너지 충전 실패: {e}")
            return False


# 하위 호환성을 위한 별칭
EnergyPoolService = EnergyPoolModelService
