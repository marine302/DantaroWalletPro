"""
TRON Energy Pool 관리 서비스 (통합 인터페이스)

기존 441줄의 EnergyPoolService를 기능별로 분할:
- pool/pool_manager.py: 풀 생성 및 기본 관리
- pool/usage_tracker.py: 사용량 추적 및 모니터링

이 파일은 백워드 호환성을 위한 통합 인터페이스입니다.
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.energy_pool import EnergyPool, EnergyUsageLog
from sqlalchemy.ext.asyncio import AsyncSession

from .pool import get_pool_manager, get_usage_tracker

logger = logging.getLogger(__name__)


class EnergyPoolService:
    """TRON Energy Pool 관리 서비스 (통합 인터페이스)"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pool_manager = get_pool_manager(db)
        self.usage_tracker = get_usage_tracker(db)

    # Pool Manager 메소드들
    async def get_default_energy_pool(self) -> Optional[EnergyPool]:
        """기본 에너지 풀 조회"""
        return await self.pool_manager.get_default_energy_pool()

    async def create_default_energy_pool(self, wallet_address: str) -> EnergyPool:
        """기본 에너지 풀 생성"""
        return await self.pool_manager.create_default_energy_pool(wallet_address)

    async def create_energy_pool(
        self, 
        pool_name: str, 
        wallet_address: str,
        energy_threshold: int = 100000,
        bandwidth_threshold: int = 10000
    ) -> EnergyPool:
        """새 에너지 풀 생성"""
        return await self.pool_manager.create_energy_pool(
            pool_name, wallet_address, energy_threshold, bandwidth_threshold
        )

    async def deactivate_pool(self, pool_id: int) -> bool:
        """에너지 풀 비활성화"""
        return await self.pool_manager.deactivate_pool(pool_id)

    # Usage Tracker 메소드들
    async def record_energy_usage(
        self,
        energy_pool_id: int,
        transaction_hash: str,
        energy_consumed: int,
        bandwidth_consumed: int = 0,
        fee_paid: Decimal = Decimal("0"),
        simulation: bool = False,
    ) -> EnergyUsageLog:
        """에너지 사용량 기록"""
        return await self.usage_tracker.record_energy_usage(
            energy_pool_id, transaction_hash, energy_consumed, 
            bandwidth_consumed, fee_paid, simulation
        )

    async def get_usage_statistics(
        self, 
        energy_pool_id: int, 
        days_back: int = 7
    ) -> Dict[str, Any]:
        """사용량 통계 조회"""
        return await self.usage_tracker.get_usage_statistics(energy_pool_id, days_back)

    async def get_recent_usage(
        self, 
        energy_pool_id: int, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """최근 사용 내역 조회"""
        return await self.usage_tracker.get_recent_usage(energy_pool_id, limit)

    async def check_usage_alerts(self, energy_pool_id: int) -> List[Dict[str, Any]]:
        """사용량 알림 확인"""
        return await self.usage_tracker.check_usage_alerts(energy_pool_id)

    # 통합 서비스 메소드들
    async def check_refreeze_needed(self) -> bool:
        """재동결 필요 여부 확인"""
        try:
            pool = await self.get_default_energy_pool()
            if not pool:
                return False

            # 임계값 이하인 경우 재동결 필요
            if pool.available_energy < pool.energy_threshold:
                return True
            
            if pool.available_bandwidth < pool.bandwidth_threshold:
                return True

            return False

        except Exception as e:
            logger.error(f"재동결 확인 실패: {str(e)}")
            return False

    async def get_pool_status(self, pool_id: Optional[int] = None) -> Dict[str, Any]:
        """풀 상태 정보 조회"""
        try:
            if pool_id:
                # 특정 풀 조회 (구현 필요)
                pool = await self.get_default_energy_pool()
            else:
                pool = await self.get_default_energy_pool()

            if not pool:
                return {"status": "no_pool", "message": "No active energy pool"}

            # 최근 사용량 통계
            usage_stats = await self.get_usage_statistics(pool.id, 1)  # 1일
            
            # 알림 확인
            alerts = await self.check_usage_alerts(pool.id)

            return {
                "status": "active",
                "pool_info": {
                    "id": pool.id,
                    "name": pool.pool_name,
                    "wallet_address": pool.wallet_address,
                    "available_energy": pool.available_energy,
                    "available_bandwidth": pool.available_bandwidth,
                    "total_frozen_trx": float(pool.total_frozen_trx),
                    "energy_threshold": pool.energy_threshold,
                    "bandwidth_threshold": pool.bandwidth_threshold,
                    "auto_refreeze_enabled": pool.auto_refreeze_enabled,
                },
                "daily_usage": usage_stats,
                "alerts": alerts,
                "needs_refreeze": await self.check_refreeze_needed(),
            }

        except Exception as e:
            logger.error(f"풀 상태 조회 실패: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def simulate_energy_usage(
        self, 
        energy_amount: int, 
        pool_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """에너지 사용 시뮬레이션"""
        try:
            pool = await self.get_default_energy_pool()
            if not pool:
                return {"error": "No active energy pool"}

            # 시뮬레이션 로그 생성
            simulation_hash = f"SIM_{int(datetime.utcnow().timestamp())}"
            
            usage_log = await self.record_energy_usage(
                energy_pool_id=pool.id,
                transaction_hash=simulation_hash,
                energy_consumed=energy_amount,
                bandwidth_consumed=0,
                fee_paid=Decimal("0"),
                simulation=True,
            )

            return {
                "status": "success",
                "simulation_id": usage_log.id,
                "energy_used": energy_amount,
                "remaining_energy": pool.available_energy - energy_amount,
                "message": "Energy usage simulation completed",
            }

        except Exception as e:
            logger.error(f"에너지 사용 시뮬레이션 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
