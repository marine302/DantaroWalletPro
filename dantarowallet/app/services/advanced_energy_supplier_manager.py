"""
고급 에너지 공급원 관리 서비스 - 문서 #40 기반
"""

from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.energy_supplier import EnergySupplier, SupplierType, SupplierStatus
from app.models.energy_allocation import EnergyAllocation, AllocationStatus
from app.models.company_wallet import CompanyWallet, CompanyWalletType
from app.core.tron import TronService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class AdvancedEnergySupplierManager:
    """고급 에너지 공급원 관리자"""

    def __init__(self, db: Session):
        self.db = db
        self.tron_service = TronService()

    async def find_optimal_supplier(
        self,
        energy_needed: int,
        urgency_level: str = "normal",
        target_address: str = None
    ) -> Optional[EnergySupplier]:
        """최적 에너지 공급원 찾기 (고급 알고리즘)"""
        try:
            # 활성화된 공급원을 우선순위 순으로 조회
            suppliers = self.db.query(EnergySupplier).filter(
                EnergySupplier.is_active == True,
                EnergySupplier.status == SupplierStatus.ACTIVE
            ).order_by(EnergySupplier.priority).all()

            # 긴급도에 따른 필터링
            if urgency_level == "critical":
                # 즉시 처리 가능한 공급원만
                suppliers = [s for s in suppliers if s.average_response_time < 60000]  # 1분 이내
            elif urgency_level == "high":
                # 5분 이내 처리 가능한 공급원
                suppliers = [s for s in suppliers if s.average_response_time < 300000]  # 5분 이내

            for supplier in suppliers:
                # 공급원 상태 확인
                if not await self._check_supplier_health(supplier):
                    continue

                # 공급 가능 여부 확인
                if supplier.supplier_type == SupplierType.SELF_STAKING:
                    if await self._check_self_staking_availability(supplier, energy_needed):
                        logger.info(f"자체 스테이킹 사용 선택: {energy_needed} 에너지")
                        return supplier

                elif supplier.min_order_amount <= energy_needed <= (supplier.max_order_amount or float('inf')):
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
                    return supplier.status == SupplierStatus.ACTIVE

            # 실제 상태 확인
            is_healthy = await self._perform_health_check(supplier)

            # 상태 업데이트
            supplier.last_checked_at = datetime.utcnow()
            supplier.status = SupplierStatus.ACTIVE if is_healthy else SupplierStatus.ERROR
            self.db.commit()

            return is_healthy

        except Exception as e:
            logger.error(f"공급원 상태 확인 실패: {e}")
            return False

    async def _perform_health_check(self, supplier: EnergySupplier) -> bool:
        """실제 공급원 상태 확인"""
        try:
            if supplier.supplier_type == SupplierType.SELF_STAKING:
                return await self._check_self_staking_health(supplier)
            else:
                return await self._check_external_supplier_health(supplier)

        except Exception as e:
            logger.error(f"공급원 헬스체크 실패: {e}")
            return False

    async def _check_self_staking_health(self, supplier: EnergySupplier) -> bool:
        """자체 스테이킹 상태 확인"""
        try:
            # 스테이킹 지갑 조회
            staking_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.STAKING
            ).first()

            if not staking_wallet:
                logger.error("스테이킹 지갑을 찾을 수 없습니다")
                return False

            # TRON 네트워크에서 실제 에너지 정보 조회
            account_info = await self.tron_service.get_account_info(staking_wallet.address)
            
            if account_info and 'frozen' in account_info:
                # 사용 가능한 에너지 업데이트
                available_energy = account_info.get('energy_available', 0)
                supplier.available_energy = available_energy
                staking_wallet.available_energy = available_energy
                self.db.commit()

                return available_energy > 10000  # 최소 10K 에너지 필요

            return False

        except Exception as e:
            logger.error(f"자체 스테이킹 헬스체크 실패: {e}")
            return False

    async def _check_external_supplier_health(self, supplier: EnergySupplier) -> bool:
        """외부 공급사 상태 확인"""
        try:
            if supplier.supplier_type == SupplierType.TRONZAP:
                return await self._check_tronzap_health(supplier)
            elif supplier.supplier_type == SupplierType.TRONNRG:
                return await self._check_tronnrg_health(supplier)
            
            return False

        except Exception as e:
            logger.error(f"외부 공급사 헬스체크 실패: {e}")
            return False

    async def _check_tronzap_health(self, supplier: EnergySupplier) -> bool:
        """TronZap API 상태 확인"""
        try:
            # TronZap API ping 또는 balance 조회
            # 실제 구현 시 TronZap API 문서 참조
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{supplier.api_endpoint}/ping",
                    headers={"Authorization": f"Bearer {supplier.api_key}"},
                    timeout=10
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"TronZap 헬스체크 실패: {e}")
            return False

    async def _check_tronnrg_health(self, supplier: EnergySupplier) -> bool:
        """TronNRG API 상태 확인"""
        try:
            # TronNRG API ping 또는 balance 조회
            # 실제 구현 시 TronNRG API 문서 참조
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{supplier.api_endpoint}/status",
                    headers={"X-API-Key": supplier.api_key},
                    timeout=10
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"TronNRG 헬스체크 실패: {e}")
            return False

    async def _check_self_staking_availability(self, supplier: EnergySupplier, energy_needed: int) -> bool:
        """자체 스테이킹 가용성 확인"""
        try:
            return (
                supplier.available_energy >= energy_needed and
                supplier.status == SupplierStatus.ACTIVE
            )

        except Exception as e:
            logger.error(f"자체 스테이킹 가용성 확인 실패: {e}")
            return False

    async def _check_external_supplier_availability(self, supplier: EnergySupplier, energy_needed: int) -> bool:
        """외부 공급사 가용성 확인"""
        try:
            # 최소/최대 주문량 확인
            if energy_needed < supplier.min_order_amount:
                return False
            
            if supplier.max_order_amount and energy_needed > supplier.max_order_amount:
                return False

            # 실제 가용성 확인 (API 호출)
            if supplier.supplier_type == SupplierType.TRONZAP:
                return await self._check_tronzap_availability(supplier, energy_needed)
            elif supplier.supplier_type == SupplierType.TRONNRG:
                return await self._check_tronnrg_availability(supplier, energy_needed)

            return False

        except Exception as e:
            logger.error(f"외부 공급사 가용성 확인 실패: {e}")
            return False

    async def _check_tronzap_availability(self, supplier: EnergySupplier, energy_needed: int) -> bool:
        """TronZap 가용성 확인"""
        # 실제 TronZap API 호출로 구현
        return True  # 임시

    async def _check_tronnrg_availability(self, supplier: EnergySupplier, energy_needed: int) -> bool:
        """TronNRG 가용성 확인"""
        # 실제 TronNRG API 호출로 구현
        return True  # 임시

    async def get_supplier_statistics(self, days: int = 30) -> Dict:
        """공급원별 통계 조회"""
        try:
            from_date = datetime.utcnow() - timedelta(days=days)
            
            # 공급원별 통계 계산
            stats = {}
            suppliers = self.db.query(EnergySupplier).all()
            
            for supplier in suppliers:
                allocations = self.db.query(EnergyAllocation).filter(
                    and_(
                        EnergyAllocation.supplier_id == supplier.id,
                        EnergyAllocation.created_at >= from_date
                    )
                ).all()
                
                total_allocations = len(allocations)
                successful_allocations = len([a for a in allocations if a.status == AllocationStatus.COMPLETED])
                total_energy = sum(a.energy_amount for a in allocations if a.energy_amount)
                total_cost = sum(a.total_cost_trx for a in allocations if a.total_cost_trx)
                
                stats[supplier.supplier_type.value] = {
                    "total_allocations": total_allocations,
                    "successful_allocations": successful_allocations,
                    "success_rate": (successful_allocations / total_allocations * 100) if total_allocations > 0 else 0,
                    "total_energy_supplied": total_energy,
                    "total_cost_trx": float(total_cost) if total_cost else 0,
                    "average_cost_per_energy": float(total_cost / total_energy) if total_energy > 0 else 0,
                    "status": supplier.status.value,
                    "available_energy": supplier.available_energy
                }
            
            return stats

        except Exception as e:
            logger.error(f"공급원 통계 조회 실패: {e}")
            return {}
