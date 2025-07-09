"""
에너지 풀 서비스 - 에너지 풀 매니저
"""
import logging
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func

from app.models.energy_pool import (
    EnergyPoolModel, EnergyPoolStatus, EnergyUsageLog, EnergyPriceHistory
)
from app.core.exceptions import EnergyInsufficientError
from .utils import safe_get_attr, safe_int, safe_decimal, calculate_usage_rate, calculate_efficiency_score
from .models import EnergyPoolStatusInfo, EnergyTransaction

logger = logging.getLogger(__name__)


class EnergyPoolManager:
    """에너지 풀 관리 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_energy_status(self) -> EnergyPoolStatusInfo:
        """현재 에너지 풀 상태를 조회합니다."""
        try:
            # 에너지 풀 정보 조회
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                # 기본 에너지 풀 생성
                energy_pool = await self._create_default_energy_pool()
            
            # 안전하게 속성 가져오기
            total_energy = safe_int(safe_get_attr(energy_pool, 'total_energy'), 1000000)
            available_energy = safe_int(safe_get_attr(energy_pool, 'available_energy'), 1000000)
            used_energy = safe_int(safe_get_attr(energy_pool, 'used_energy'), 0)
            warning_threshold = safe_int(safe_get_attr(energy_pool, 'warning_threshold'), 20)
            critical_threshold = safe_int(safe_get_attr(energy_pool, 'critical_threshold'), 10)
            
            reserved_energy = max(0, total_energy - available_energy - used_energy)
            daily_consumption = used_energy
            usage_rate = calculate_usage_rate(used_energy, total_energy)
            efficiency = calculate_efficiency_score(available_energy, total_energy)
            
            return EnergyPoolStatusInfo(
                total_energy=total_energy,
                available_energy=available_energy,
                reserved_energy=reserved_energy,
                daily_consumption=daily_consumption,
                usage_rate=usage_rate,
                efficiency=efficiency,
                alert_threshold=warning_threshold * total_energy // 100,
                critical_threshold=critical_threshold * total_energy // 100
            )
            
        except Exception as e:
            logger.error(f"에너지 상태 조회 실패: {e}")
            return self._get_default_status_info()
    
    async def _create_default_energy_pool(self) -> EnergyPoolModel:
        """기본 에너지 풀 생성"""
        energy_pool = EnergyPoolModel(
            pool_name="Main Pool",
            owner_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
            total_energy=1000000,
            available_energy=1000000,
            used_energy=0,
            frozen_trx=Decimal('1000'),
            status=EnergyPoolStatus.ACTIVE,
            warning_threshold=20,
            critical_threshold=10
        )
        self.db.add(energy_pool)
        await self.db.commit()
        await self.db.refresh(energy_pool)
        return energy_pool
    
    def _get_default_status_info(self) -> EnergyPoolStatusInfo:
        """기본 상태 정보 반환"""
        return EnergyPoolStatusInfo(
            total_energy=1000000,
            available_energy=1000000,
            reserved_energy=0,
            daily_consumption=0,
            usage_rate=0.0,
            efficiency=95.0,
            alert_threshold=200000,
            critical_threshold=100000
        )
    
    async def consume_energy(
        self, amount: int, transaction_type: str, user_id: int, transaction_id: str
    ) -> bool:
        """에너지를 소모합니다."""
        try:
            # 에너지 풀 조회
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                raise EnergyInsufficientError("에너지 풀을 찾을 수 없습니다.")
            
            # 안전하게 가용 에너지 확인
            available_energy = safe_int(safe_get_attr(energy_pool, 'available_energy'), 0)
            if available_energy < amount:
                raise EnergyInsufficientError(f"에너지 부족: 필요 {amount}, 사용 가능 {available_energy}")
            
            # 에너지 소모
            new_available = available_energy - amount
            current_used = safe_int(safe_get_attr(energy_pool, 'used_energy'), 0)
            new_used = current_used + amount
            
            # 에너지 풀 업데이트
            await self.db.execute(
                update(EnergyPoolModel)
                .where(EnergyPoolModel.id == energy_pool.id)
                .values(
                    available_energy=new_available,
                    used_energy=new_used,
                    last_updated=datetime.utcnow()
                )
            )
            
            # 사용 로그 기록
            await self._log_energy_usage(user_id, amount, transaction_type, transaction_id)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"에너지 소모 실패: {e}")
            raise
    
    async def _log_energy_usage(self, user_id: int, amount: int, transaction_type: str, transaction_id: str):
        """에너지 사용 로그 기록"""
        try:
            usage_log = EnergyUsageLog(
                user_id=user_id,
                energy_amount=amount,
                transaction_type=transaction_type,
                transaction_id=transaction_id,
                created_at=datetime.utcnow()
            )
            self.db.add(usage_log)
        except Exception as e:
            logger.error(f"에너지 사용 로그 기록 실패: {e}")
    
    async def get_energy_pool_by_id(self, pool_id: int) -> Optional[EnergyPoolModel]:
        """ID로 에너지 풀 조회"""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel).where(EnergyPoolModel.id == pool_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"에너지 풀 조회 실패: {e}")
            return None
    
    async def update_energy_pool_status(self, pool_id: int, status: EnergyPoolStatus) -> bool:
        """에너지 풀 상태 업데이트"""
        try:
            await self.db.execute(
                update(EnergyPoolModel)
                .where(EnergyPoolModel.id == pool_id)
                .values(status=status, last_updated=datetime.utcnow())
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"에너지 풀 상태 업데이트 실패: {e}")
            return False
    
    async def get_energy_pools(self, limit: int = 10, offset: int = 0) -> List[EnergyPoolModel]:
        """에너지 풀 목록 조회"""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel)
                .order_by(desc(EnergyPoolModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"에너지 풀 목록 조회 실패: {e}")
            return []
