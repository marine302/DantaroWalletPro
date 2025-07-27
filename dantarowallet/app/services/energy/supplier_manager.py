"""
에너지 공급원 관리 서비스 - 문서 #40 기반 (타입 오류 무시)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.energy_supplier import EnergySupplier, SupplierType, SupplierStatus
from app.core.logging import get_logger
from app.core.tron import TronService

logger = get_logger(__name__)


class EnergySupplierManager:
    """에너지 공급원 관리자"""

    def __init__(self, db: Session):
        self.db = db
        self.tron_service = TronService()

    async def find_optimal_supplier(
        self,
        energy_needed: int,
        urgency_level: str = "normal"
    ) -> Optional[EnergySupplier]:
        """최적 에너지 공급원 찾기"""
        try:
            # 활성화된 공급원을 우선순위 순으로 조회
            suppliers = self.db.query(EnergySupplier).filter(
                EnergySupplier.is_active == True,
                EnergySupplier.status == SupplierStatus.ACTIVE
            ).order_by(EnergySupplier.priority).all()

            for supplier in suppliers:
                # 공급원 상태 확인
                if not await self._check_supplier_health(supplier):
                    continue

                # 공급 가능 여부 확인
                if supplier.supplier_type == SupplierType.SELF_STAKING:  # type: ignore
                    if await self._check_self_staking_availability(supplier, energy_needed):
                        logger.info(f"자체 스테이킹 사용 선택: {energy_needed} 에너지")
                        return supplier

                elif supplier.min_order_amount <= energy_needed:  # type: ignore
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
            if supplier.last_checked_at:
                time_since_check = datetime.utcnow() - supplier.last_checked_at
                if time_since_check < timedelta(minutes=5):
                    return supplier.status == SupplierStatus.ACTIVE  # type: ignore

            # 실제 상태 확인
            is_healthy = await self._perform_health_check(supplier)

            # 상태 업데이트 (UPDATE 쿼리 사용)
            self.db.query(EnergySupplier).filter(
                EnergySupplier.id == supplier.id
            ).update({
                'last_checked_at': datetime.utcnow(),
                'status': SupplierStatus.ACTIVE if is_healthy else SupplierStatus.ERROR
            })
            self.db.commit()

            return is_healthy

        except Exception as e:
            logger.error(f"공급원 상태 확인 실패: {e}")
            return False

    async def _perform_health_check(self, supplier: EnergySupplier) -> bool:
        """실제 헬스체크 수행"""
        if supplier.supplier_type == SupplierType.SELF_STAKING:  # type: ignore
            return await self._check_self_staking_health()
        else:
            return await self._check_external_api_health(supplier)

    async def _check_self_staking_health(self) -> bool:
        """자체 스테이킹 상태 확인"""
        try:
            # 스테이킹 지갑 상태 확인
            # 실제 구현에서는 TronService를 통해 확인
            return True
        except Exception:
            return False

    async def _check_external_api_health(self, supplier: EnergySupplier) -> bool:
        """외부 API 상태 확인"""
        try:
            # 외부 API 엔드포인트 상태 확인
            # 실제 구현에서는 HTTP 요청으로 확인
            return True
        except Exception:
            return False

    async def _check_self_staking_availability(
        self, 
        supplier: EnergySupplier, 
        energy_needed: int
    ) -> bool:
        """자체 스테이킹 가용성 확인"""
        try:
            # 사용 가능한 에너지 확인
            return supplier.available_energy >= energy_needed  # type: ignore
        except Exception:
            return False

    async def _check_external_supplier_availability(
        self, 
        supplier: EnergySupplier, 
        energy_needed: int
    ) -> bool:
        """외부 공급사 가용성 확인"""
        try:
            # 최소/최대 주문량 확인
            if energy_needed < supplier.min_order_amount:  # type: ignore
                return False
            if supplier.max_order_amount and energy_needed > supplier.max_order_amount:  # type: ignore
                return False
            
            # 실제 API 확인은 생략 (실제 구현에서는 API 호출)
            return True
        except Exception:
            return False

    async def update_supplier_stats(
        self, 
        supplier_id: int, 
        energy_supplied: int, 
        success: bool
    ):
        """공급원 통계 업데이트"""
        try:
            # UPDATE 쿼리 사용
            self.db.query(EnergySupplier).filter(
                EnergySupplier.id == supplier_id
            ).update({
                'total_orders': EnergySupplier.total_orders + 1,
                'total_energy_supplied': EnergySupplier.total_energy_supplied + (energy_supplied if success else 0)
            })
            
            self.db.commit()
                
        except Exception as e:
            logger.error(f"공급원 통계 업데이트 실패: {e}")
            self.db.rollback()

    async def get_supplier_recommendations(self) -> List[Dict[str, Any]]:
        """공급원 추천 리스트"""
        try:
            suppliers = self.db.query(EnergySupplier).filter(
                EnergySupplier.is_active == True
            ).order_by(EnergySupplier.priority).all()

            recommendations = []
            for supplier in suppliers:
                recommendations.append({
                    "id": supplier.id,
                    "type": supplier.supplier_type.value,  # type: ignore
                    "name": supplier.name,
                    "priority": supplier.priority,
                    "status": supplier.status.value,  # type: ignore
                    "available_energy": supplier.available_energy,
                    "cost_per_energy": float(supplier.cost_per_energy),  # type: ignore
                    "success_rate": float(supplier.success_rate),  # type: ignore
                    "avg_response_time": supplier.average_response_time
                })

            return recommendations

        except Exception as e:
            logger.error(f"공급원 추천 리스트 생성 실패: {e}")
            return []
