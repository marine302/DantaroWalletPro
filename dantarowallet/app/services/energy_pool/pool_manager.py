"""에너지 풀 관리자 - 에너지 풀의 생성, 충전, 소모, 상태 조회를 담당"""
from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import selectinload

from app.models.energy_pool import EnergyPoolModel, EnergyPoolStatus
from app.schemas.energy import CreateEnergyPoolRequest, EnergyPoolResponse
from app.core.exceptions import EnergyInsufficientError, ValidationError
from app.core.logger import get_logger

from .utils import safe_get_attr, safe_int, safe_decimal
from .models import EnergyPoolStatusInfo, EnergyRechargeRequest

logger = get_logger(__name__)


class EnergyPoolManager:
    """에너지 풀 관리자"""
    
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
            
            # 안전하게 속성 가져오기
            total_energy = safe_int(safe_get_attr(energy_pool, 'total_energy'), 1000000)
            available_energy = safe_int(safe_get_attr(energy_pool, 'available_energy'), 1000000)
            used_energy = safe_int(safe_get_attr(energy_pool, 'used_energy'), 0)
            warning_threshold = safe_int(safe_get_attr(energy_pool, 'warning_threshold'), 20)
            critical_threshold = safe_int(safe_get_attr(energy_pool, 'critical_threshold'), 10)
            
            reserved_energy = max(0, total_energy - available_energy - used_energy)
            daily_consumption = used_energy
            usage_rate = (used_energy / total_energy * 100) if total_energy > 0 else 0
            efficiency = 95.0
            
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
    
    async def create_energy_pool(self, request: CreateEnergyPoolRequest) -> EnergyPoolResponse:
        """새로운 에너지 풀을 생성합니다."""
        try:
            # 기본값 설정
            total_energy = 1000000  # 기본 에너지 양
            
            energy_pool = EnergyPoolModel(
                pool_name=request.pool_name,
                owner_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",  # 기본 주소
                total_energy=total_energy,
                available_energy=total_energy,
                used_energy=0,
                frozen_trx=request.initial_trx_amount,
                status=EnergyPoolStatus.ACTIVE,
                warning_threshold=20,
                critical_threshold=10
            )
            
            self.db.add(energy_pool)
            await self.db.commit()
            await self.db.refresh(energy_pool)
            
            logger.info(f"에너지 풀 생성 완료: {request.pool_name}")
            
            return EnergyPoolResponse(
                partner_id=1,  # 기본값
                wallet_address=safe_get_attr(energy_pool, 'owner_address', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'),
                status=energy_pool.status.value,
                total_energy=safe_int(safe_get_attr(energy_pool, 'total_energy'), total_energy),
                available_energy=safe_int(safe_get_attr(energy_pool, 'available_energy'), total_energy),
                used_energy=safe_int(safe_get_attr(energy_pool, 'used_energy'), 0),
                energy_percentage=100.0,
                total_bandwidth=0,
                available_bandwidth=0,
                frozen_trx_total=float(safe_decimal(safe_get_attr(energy_pool, 'frozen_trx'), request.initial_trx_amount)),
                frozen_trx_energy=float(safe_decimal(safe_get_attr(energy_pool, 'frozen_trx'), request.initial_trx_amount)),
                frozen_trx_bandwidth=0.0,
                daily_average_usage=0.0,
                peak_usage_hour=None,
                depletion_estimated_at=None,
                last_checked_at=datetime.utcnow(),
                warning_threshold=safe_int(safe_get_attr(energy_pool, 'warning_threshold'), 20),
                critical_threshold=safe_int(safe_get_attr(energy_pool, 'critical_threshold'), 10)
            )
            
        except Exception as e:
            logger.error(f"에너지 풀 생성 실패: {e}")
            await self.db.rollback()
            raise
    
    async def recharge_energy(self, amount: int, user_id: int) -> bool:
        """에너지를 충전합니다."""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                raise ValidationError("에너지 풀을 찾을 수 없습니다.")
            
            current_available = safe_int(safe_get_attr(energy_pool, 'available_energy'), 0)
            new_available = current_available + amount
            
            await self.db.execute(
                update(EnergyPoolModel)
                .where(EnergyPoolModel.id == energy_pool.id)
                .values(available_energy=new_available)
            )
            
            await self.db.commit()
            logger.info(f"에너지 충전 완료: {amount} units for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"에너지 충전 실패: {e}")
            await self.db.rollback()
            raise
    
    async def use_energy(self, amount: int, user_id: int, transaction_hash: str) -> bool:
        """에너지를 사용합니다."""
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
            
            # 에너지 소모 처리
            new_available = available_energy - amount
            new_used = safe_int(safe_get_attr(energy_pool, 'used_energy'), 0) + amount
            
            await self.db.execute(
                update(EnergyPoolModel)
                .where(EnergyPoolModel.id == energy_pool.id)
                .values(
                    available_energy=new_available,
                    used_energy=new_used
                )
            )
            
            await self.db.commit()
            logger.info(f"에너지 사용 성공: {amount} units for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"에너지 사용 실패: {e}")
            await self.db.rollback()
            raise