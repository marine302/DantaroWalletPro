"""
고급 에너지 공급원 관리자 서비스
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.energy_supplier import EnergySupplier, SupplierType, SupplierStatus
from app.core.tron import TronService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AdvancedEnergySupplierManager:
    """고급 에너지 공급원 관리자"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron_service = TronService()

    async def find_optimal_supplier(
        self,
        energy_needed: int,
        urgency_level: str = "normal",
        target_address: Optional[str] = None
    ) -> Optional[EnergySupplier]:
        """최적 에너지 공급원 찾기 (고급 알고리즘)"""
        try:
            # 활성화된 공급원을 우선순위 순으로 조회
            query = select(EnergySupplier).where(
                and_(
                    EnergySupplier.is_active == True,
                    EnergySupplier.status == SupplierStatus.ACTIVE.value
                )
            ).order_by(EnergySupplier.priority)
            
            result = await self.db.execute(query)
            suppliers = result.scalars().all()

            # 긴급도에 따른 필터링
            if urgency_level == "critical":
                # 즉시 처리 가능한 공급원만
                suppliers = [s for s in suppliers if s.average_response_time and s.average_response_time < 60000]  # type: ignore # 1분 이내
            elif urgency_level == "high":
                # 5분 이내 처리 가능한 공급원
                suppliers = [s for s in suppliers if s.average_response_time and s.average_response_time < 300000]  # type: ignore # 5분 이내

            for supplier in suppliers:
                # 공급원 상태 확인
                if not await self._check_supplier_health(supplier):
                    continue

                # 공급 가능 여부 확인
                if supplier.supplier_type == SupplierType.SELF_STAKING.value:  # type: ignore
                    if await self._check_self_staking_availability(supplier, energy_needed):
                        logger.info(f"자체 스테이킹 사용 선택: {energy_needed} 에너지")
                        return supplier

                elif supplier.min_order_amount <= energy_needed <= (supplier.max_order_amount or float('inf')):  # type: ignore
                    if await self._check_external_supplier_availability(supplier, energy_needed):
                        logger.info(f"{supplier.name} 사용 선택: {energy_needed} 에너지")
                        return supplier

            # 모든 공급원 실패 시
            logger.warning(f"모든 공급원 실패, 폴백 모드 활성화")
            return None

        except Exception as e:
            logger.error(f"최적 공급원 검색 실패: {e}")
            return None

    async def _check_supplier_health(self, supplier: EnergySupplier) -> bool:
        """공급원 상태 확인"""
        try:
            # 마지막 확인 시간 체크
            if supplier.last_checked_at:  # type: ignore
                time_since_check = datetime.utcnow() - supplier.last_checked_at
                if time_since_check < timedelta(minutes=5):  # type: ignore
                    return supplier.status == SupplierStatus.ACTIVE.value  # type: ignore

            # 실제 상태 확인
            is_healthy = await self._perform_health_check(supplier)

            # 상태 업데이트
            await self.db.execute(
                update(EnergySupplier)
                .where(EnergySupplier.id == supplier.id)
                .values(
                    last_checked_at=datetime.utcnow(),
                    status=SupplierStatus.ACTIVE.value if is_healthy else SupplierStatus.ERROR.value
                )
            )
            await self.db.commit()

            return is_healthy

        except Exception as e:
            logger.error(f"공급원 상태 확인 실패: {e}")
            return False

    async def _perform_health_check(self, supplier: EnergySupplier) -> bool:
        """실제 상태 확인 수행"""
        try:
            if supplier.supplier_type == SupplierType.SELF_STAKING.value:  # type: ignore
                # 자체 스테이킹 상태 확인
                return await self._check_staking_wallet_health(supplier)
            else:
                # 외부 API 상태 확인
                return await self._check_external_api_health(supplier)

        except Exception as e:
            logger.error(f"상태 확인 수행 실패: {e}")
            return False

    async def _check_staking_wallet_health(self, supplier: EnergySupplier) -> bool:
        """스테이킹 지갑 상태 확인"""
        try:
            if not supplier.wallet_address:
                return False
                
            # TronService에 실제 존재하는 메소드 사용
            return True  # 임시로 True 반환 (실제 구현에서는 지갑 상태 확인)

        except Exception as e:
            logger.error(f"스테이킹 지갑 상태 확인 실패: {e}")
            return False

    async def _check_external_api_health(self, supplier: EnergySupplier) -> bool:
        """외부 API 상태 확인"""
        try:
            # 간단한 ping 또는 상태 확인 API 호출
            # 실제 구현에서는 각 공급원별 API에 맞는 헬스체크 수행
            return True  # 임시로 True 반환

        except Exception as e:
            logger.error(f"외부 API 상태 확인 실패: {e}")
            return False

    async def _check_self_staking_availability(self, supplier: EnergySupplier, energy_needed: int) -> bool:
        """자체 스테이킹 가용성 확인"""
        try:
            if not supplier.wallet_address:
                return False

            # 임시로 True 반환 (실제 구현에서는 에너지 잔액 확인)
            return True

        except Exception as e:
            logger.error(f"자체 스테이킹 가용성 확인 실패: {e}")
            return False

    async def _check_external_supplier_availability(self, supplier: EnergySupplier, energy_needed: int) -> bool:
        """외부 공급원 가용성 확인"""
        try:
            # 최소/최대 주문량 확인
            if energy_needed < supplier.min_order_amount:  # type: ignore
                return False
                
            if supplier.max_order_amount and energy_needed > supplier.max_order_amount:  # type: ignore
                return False

            # 일일 한도 확인
            if supplier.daily_limit:
                today_usage = await self._get_today_usage(supplier.id)  # type: ignore
                if today_usage + energy_needed > supplier.daily_limit:
                    return False

            # 시간당 한도 확인
            if supplier.hourly_limit:
                hour_usage = await self._get_hour_usage(supplier.id)  # type: ignore
                if hour_usage + energy_needed > supplier.hourly_limit:
                    return False

            return True

        except Exception as e:
            logger.error(f"외부 공급원 가용성 확인 실패: {e}")
            return False

    async def _get_today_usage(self, supplier_id: str) -> int:
        """오늘 사용량 조회"""
        try:
            from app.models.energy_allocation import EnergyAllocation
            
            today = datetime.utcnow().date()
            
            query = select(EnergyAllocation).where(
                and_(
                    EnergyAllocation.supplier_id == supplier_id,
                    EnergyAllocation.created_at >= datetime.combine(today, datetime.min.time()),
                    EnergyAllocation.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time())
                )
            )
            
            result = await self.db.execute(query)
            allocations = result.scalars().all()
            
            return sum(allocation.energy_amount for allocation in allocations)  # type: ignore

        except Exception as e:
            logger.error(f"오늘 사용량 조회 실패: {e}")
            return 0

    async def _get_hour_usage(self, supplier_id: str) -> int:
        """시간당 사용량 조회"""
        try:
            from app.models.energy_allocation import EnergyAllocation
            
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            query = select(EnergyAllocation).where(
                and_(
                    EnergyAllocation.supplier_id == supplier_id,
                    EnergyAllocation.created_at >= hour_ago
                )
            )
            
            result = await self.db.execute(query)
            allocations = result.scalars().all()
            
            return sum(allocation.energy_amount for allocation in allocations)  # type: ignore

        except Exception as e:
            logger.error(f"시간당 사용량 조회 실패: {e}")
            return 0

    async def calculate_dynamic_pricing(self, supplier: EnergySupplier, energy_amount: int) -> Decimal:
        """동적 가격 계산"""
        try:
            base_price = supplier.base_price_per_energy or Decimal('0.0001')
            
            # 사용량 기반 할인
            if energy_amount >= 1000000:  # 100만 에너지 이상
                discount = Decimal('0.1')  # 10% 할인
            elif energy_amount >= 500000:  # 50만 에너지 이상
                discount = Decimal('0.05')  # 5% 할인
            else:
                discount = Decimal('0')

            # 공급원 로드 기반 조정
            load_multiplier = await self._calculate_load_multiplier(supplier)
            
            final_price = base_price * (1 - discount) * load_multiplier
            
            return final_price

        except Exception as e:
            logger.error(f"동적 가격 계산 실패: {e}")
            return supplier.base_price_per_energy or Decimal('0.0001')

    async def _calculate_load_multiplier(self, supplier: EnergySupplier) -> Decimal:
        """공급원 로드 기반 승수 계산"""
        try:
            from app.models.energy_allocation import EnergyAllocation
            
            # 최근 1시간 내 주문 수 확인
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            query = select(EnergyAllocation).where(
                and_(
                    EnergyAllocation.supplier_id == supplier.id,
                    EnergyAllocation.created_at >= hour_ago
                )
            )
            
            result = await self.db.execute(query)
            recent_orders = len(result.scalars().all())
            
            # 로드에 따른 가격 조정
            if recent_orders >= 50:  # 고부하
                return Decimal('1.2')  # 20% 할증
            elif recent_orders >= 20:  # 중부하
                return Decimal('1.1')  # 10% 할증
            else:  # 저부하
                return Decimal('0.95')  # 5% 할인

        except Exception as e:
            logger.error(f"로드 승수 계산 실패: {e}")
            return Decimal('1.0')
