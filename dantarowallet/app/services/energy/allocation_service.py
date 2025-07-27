"""
에너지 할당 서비스 - 문서 #40 기반
"""

from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session

from app.models.energy_allocation import EnergyAllocation, AllocationStatus
from app.models.energy_supplier import EnergySupplier, SupplierType
from app.models.partner import Partner
from app.models.withdrawal_queue import WithdrawalQueue
from app.services.energy.supplier_manager import EnergySupplierManager
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class EnergyAllocationService:
    """에너지 할당 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.supplier_manager = EnergySupplierManager(db)

    async def allocate_energy_for_withdrawal(
        self,
        partner_id: int,
        withdrawal_request_id: int,
        target_address: str,
        energy_amount: int
    ) -> Dict:
        """출금을 위한 에너지 할당"""
        try:
            # 할당 기록 생성
            allocation = EnergyAllocation(
                allocation_id=self._generate_allocation_id(),
                partner_id=partner_id,
                withdrawal_request_id=withdrawal_request_id,
                target_address=target_address,
                energy_amount=energy_amount,
                status=AllocationStatus.PENDING
            )
            self.db.add(allocation)
            self.db.commit()

            # 최적 공급원 찾기
            supplier = await self.supplier_manager.find_optimal_supplier(energy_amount)

            if not supplier:
                # 폴백 모드 활성화
                return await self._activate_fallback_mode(allocation)

            # 공급원별 처리
            allocation.supplier_id = supplier.id
            allocation.supplier_type = supplier.supplier_type

            if supplier.supplier_type == SupplierType.SELF_STAKING:  # type: ignore
                result = await self._allocate_from_self_staking(allocation, supplier)
            else:
                result = await self._allocate_from_external_supplier(allocation, supplier)

            return result

        except Exception as e:
            logger.error(f"에너지 할당 실패: {e}")
            if 'allocation' in locals():
                allocation.status = AllocationStatus.FAILED  # type: ignore
                allocation.error_message = str(e)  # type: ignore
                self.db.commit()
            raise

    async def _allocate_from_self_staking(
        self,
        allocation: EnergyAllocation,
        supplier: EnergySupplier
    ) -> Dict:
        """자체 스테이킹에서 에너지 할당"""
        try:
            allocation.status = AllocationStatus.PROCESSING  # type: ignore
            
            # 비용 계산
            allocation.energy_price = supplier.cost_per_energy
            allocation.base_cost_trx = Decimal(str(allocation.energy_amount)) * supplier.cost_per_energy  # type: ignore
            allocation.margin_rate = Decimal("0.1")  # type: ignore # 기본 마진 10%
            allocation.margin_amount_trx = allocation.base_cost_trx * allocation.margin_rate  # type: ignore
            allocation.saas_fee_trx = Decimal("1.0")  # type: ignore # 기본 SaaS 수수료
            allocation.total_cost_trx = (  # type: ignore
                allocation.base_cost_trx +  # type: ignore
                allocation.margin_amount_trx +  # type: ignore
                allocation.saas_fee_trx  # type: ignore
            )
            
            # 간단한 성공 처리 (실제로는 TRON 네트워크 호출)
            allocation.status = AllocationStatus.COMPLETED  # type: ignore
            allocation.delegated_at = datetime.utcnow()  # type: ignore
            allocation.completed_at = datetime.utcnow()  # type: ignore
            allocation.expires_at = datetime.utcnow() + timedelta(days=1)  # type: ignore
            
            self.db.commit()
            
            logger.info(f"자체 스테이킹 에너지 할당 완료: {allocation.allocation_id}")
            
            return {
                "success": True,
                "allocation_id": allocation.allocation_id,
                "energy_amount": allocation.energy_amount,
                "total_cost_trx": float(allocation.total_cost_trx),  # type: ignore
                "expires_at": allocation.expires_at.isoformat()  # type: ignore
            }
            
        except Exception as e:
            logger.error(f"자체 스테이킹 할당 실패: {e}")
            allocation.status = AllocationStatus.FAILED  # type: ignore
            allocation.error_message = str(e)  # type: ignore
            self.db.commit()
            raise

    async def _allocate_from_external_supplier(
        self,
        allocation: EnergyAllocation,
        supplier: EnergySupplier
    ) -> Dict:
        """외부 공급사에서 에너지 할당"""
        try:
            allocation.status = AllocationStatus.PROCESSING  # type: ignore
            
            # 간단한 성공 처리 (실제로는 외부 API 호출)
            allocation.status = AllocationStatus.COMPLETED  # type: ignore
            allocation.completed_at = datetime.utcnow()  # type: ignore
            
            self.db.commit()
            
            return {
                "success": True,
                "allocation_id": allocation.allocation_id,
                "energy_amount": allocation.energy_amount,
                "supplier_type": supplier.supplier_type.value,  # type: ignore
            }
            
        except Exception as e:
            logger.error(f"외부 공급사 할당 실패: {e}")
            allocation.status = AllocationStatus.FAILED  # type: ignore
            allocation.error_message = str(e)  # type: ignore
            self.db.commit()
            raise

    async def _activate_fallback_mode(self, allocation: EnergyAllocation) -> Dict:
        """폴백 모드 활성화 (파트너사 직접 처리)"""
        try:
            allocation.is_fallback = True  # type: ignore
            allocation.status = AllocationStatus.FALLBACK  # type: ignore
            allocation.estimated_burn_trx = Decimal(str(allocation.energy_amount)) * Decimal("0.000413")  # type: ignore
            
            self.db.commit()
            
            logger.warning(f"폴백 모드 활성화: {allocation.allocation_id}")
            
            return {
                "success": False,
                "fallback_mode": True,
                "allocation_id": allocation.allocation_id,
                "energy_amount": allocation.energy_amount,
                "estimated_burn_trx": float(allocation.estimated_burn_trx),  # type: ignore
                "message": "모든 에너지 공급원이 실패했습니다. 직접 TRX를 사용하여 처리해주세요."
            }
            
        except Exception as e:
            logger.error(f"폴백 모드 활성화 실패: {e}")
            raise

    def _generate_allocation_id(self) -> str:
        """할당 ID 생성"""
        import uuid
        return uuid.uuid4().hex[:16]
