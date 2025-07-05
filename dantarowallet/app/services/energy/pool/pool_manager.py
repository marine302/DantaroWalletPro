"""
에너지 풀 관리자 - 풀 생성 및 기본 관리
"""
import logging
from decimal import Decimal
from typing import Optional

from app.core.tron import TronService
from app.models.energy_pool import EnergyPool
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PoolManager:
    """에너지 풀 생성 및 기본 관리"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron_service = TronService()

    async def get_default_energy_pool(self) -> Optional[EnergyPool]:
        """기본 에너지 풀 조회"""
        result = await self.db.execute(
            select(EnergyPool).filter(
                and_(
                    EnergyPool.is_active == True,
                    EnergyPool.pool_name == "main"
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_default_energy_pool(self, wallet_address: str) -> EnergyPool:
        """기본 에너지 풀 생성"""
        energy_pool = EnergyPool(
            pool_name="main",
            wallet_address=wallet_address,
            total_frozen_trx=Decimal("0"),
            frozen_for_energy=Decimal("0"),
            frozen_for_bandwidth=Decimal("0"),
            available_energy=0,
            available_bandwidth=0,
            daily_energy_consumption=0,
            daily_bandwidth_consumption=0,
            auto_refreeze_enabled=True,
            energy_threshold=100000,  # 10만 에너지 이하 시 알림
            bandwidth_threshold=10000,  # 1만 대역폭 이하 시 알림
            is_active=True,
        )

        self.db.add(energy_pool)
        await self.db.commit()
        await self.db.refresh(energy_pool)

        return energy_pool

    async def create_energy_pool(
        self, 
        pool_name: str, 
        wallet_address: str,
        energy_threshold: int = 100000,
        bandwidth_threshold: int = 10000
    ) -> EnergyPool:
        """새 에너지 풀 생성"""
        # 중복 확인
        existing = await self.db.execute(
            select(EnergyPool).filter(
                EnergyPool.pool_name == pool_name,
                EnergyPool.is_active == True
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError(f"Active pool with name '{pool_name}' already exists")

        energy_pool = EnergyPool(
            pool_name=pool_name,
            wallet_address=wallet_address,
            total_frozen_trx=Decimal("0"),
            frozen_for_energy=Decimal("0"),
            frozen_for_bandwidth=Decimal("0"),
            available_energy=0,
            available_bandwidth=0,
            daily_energy_consumption=0,
            daily_bandwidth_consumption=0,
            auto_refreeze_enabled=True,
            energy_threshold=energy_threshold,
            bandwidth_threshold=bandwidth_threshold,
            is_active=True,
        )

        self.db.add(energy_pool)
        await self.db.commit()
        await self.db.refresh(energy_pool)

        logger.info(f"Created new energy pool: {pool_name} with address {wallet_address}")
        return energy_pool

    async def deactivate_pool(self, pool_id: int) -> bool:
        """에너지 풀 비활성화"""
        result = await self.db.execute(
            select(EnergyPool).filter(EnergyPool.id == pool_id)
        )
        pool = result.scalar_one_or_none()
        
        if not pool:
            return False

        pool.is_active = False
        await self.db.commit()
        
        logger.info(f"Deactivated energy pool: {pool.pool_name}")
        return True

    async def update_pool_thresholds(
        self, 
        pool_id: int, 
        energy_threshold: Optional[int] = None,
        bandwidth_threshold: Optional[int] = None
    ) -> bool:
        """풀 임계값 업데이트"""
        result = await self.db.execute(
            select(EnergyPool).filter(EnergyPool.id == pool_id)
        )
        pool = result.scalar_one_or_none()
        
        if not pool:
            return False

        if energy_threshold is not None:
            pool.energy_threshold = energy_threshold
        if bandwidth_threshold is not None:
            pool.bandwidth_threshold = bandwidth_threshold

        await self.db.commit()
        logger.info(f"Updated thresholds for pool {pool.pool_name}")
        return True
