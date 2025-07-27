"""
본사 에너지 풀 관리 서비스
문서 40번 4.5절 멀티 에너지 공급원 관리 구현
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.energy_pool import EnergyPool, EnergySourceType, EnergySourceStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnergyPoolService:
    """에너지 풀 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def get_optimal_energy_source(
        self, required_energy: Decimal
    ) -> Optional[EnergyPool]:
        """
        최적 에너지 공급원 선택
        우선순위: 자체 스테이킹 > TronZap > TronNRG
        """
        logger.info(f"최적 에너지 공급원 탐색: 필요 에너지 {required_energy}")

        # 우선순위 순서로 공급원 확인
        priority_sources = [
            EnergySourceType.SELF_STAKING,
            EnergySourceType.TRONZAP,
            EnergySourceType.TRONNRG,
        ]

        for source_type in priority_sources:
            source = self._get_available_source(source_type, required_energy)
            if source:
                logger.info(f"선택된 공급원: {source_type.value}")
                return source

        logger.warning("사용 가능한 에너지 공급원 없음")
        return None

    def _get_available_source(
        self, source_type: EnergySourceType, required_energy: Decimal
    ) -> Optional[EnergyPool]:
        """특정 타입의 사용 가능한 에너지 공급원 조회"""
        return (
            self.db.query(EnergyPool)
            .filter(
                and_(
                    EnergyPool.source_type == source_type,
                    EnergyPool.is_active == True,
                    EnergyPool.status == EnergySourceStatus.ACTIVE,
                    EnergyPool.available_energy >= required_energy,
                )
            )
            .order_by(desc(EnergyPool.available_energy))
            .first()
        )

    async def allocate_energy(
        self, source_id: int, amount: Decimal, partner_wallet: str
    ) -> bool:
        """에너지 할당 처리"""
        try:
            # 트랜잭션으로 에너지 차감
            result = self.db.query(EnergyPool).filter(
                and_(
                    EnergyPool.id == source_id,
                    EnergyPool.available_energy >= amount
                )
            ).update({
                "available_energy": EnergyPool.available_energy - amount
            })
            
            if result == 0:
                logger.error(f"에너지 할당 실패: 공급원 없음 또는 에너지 부족 (ID: {source_id}, 필요: {amount})")
                return False

            self.db.commit()
            logger.info(f"에너지 할당 완료: {amount} -> {partner_wallet}")
            return True

        except Exception as e:
            logger.error(f"에너지 할당 실패: {e}")
            self.db.rollback()
            return False

    async def update_energy_status(self, source_id: int, status: EnergySourceStatus) -> bool:
        """에너지 공급원 상태 업데이트"""
        try:
            source = self.db.query(EnergyPool).filter(EnergyPool.id == source_id).first()
            if not source:
                return False

            self.db.query(EnergyPool).filter(EnergyPool.id == source_id).update({
                "status": status
            })
            self.db.commit()
            logger.info(f"에너지 공급원 상태 업데이트: {source_id} -> {status.value}")
            return True

        except Exception as e:
            logger.error(f"상태 업데이트 실패: {e}")
            self.db.rollback()
            return False

    async def get_energy_pool_summary(self) -> Dict[str, Any]:
        """에너지 풀 현황 요약"""
        pools = self.db.query(EnergyPool).filter(EnergyPool.is_active == True).all()

        summary = {
            "total_pools": len(pools),
            "total_energy": sum(pool.total_energy for pool in pools),
            "available_energy": sum(pool.available_energy for pool in pools),
            "by_source": {},
        }

        for pool in pools:
            source_type = pool.source_type.value
            if source_type not in summary["by_source"]:
                summary["by_source"][source_type] = {
                    "count": 0,
                    "total_energy": Decimal("0"),
                    "available_energy": Decimal("0"),
                }

            summary["by_source"][source_type]["count"] += 1
            summary["by_source"][source_type]["total_energy"] += pool.total_energy
            summary["by_source"][source_type]["available_energy"] += pool.available_energy

        return summary

    async def calculate_energy_cost(
        self, energy_amount: Decimal, source_type: EnergySourceType
    ) -> Decimal:
        """에너지 비용 계산 (마진 포함)"""
        # 기본 에너지 단가 (현재 시세)
        base_rate = await self._get_current_energy_rate(source_type)
        
        # 마진 적용 (15-20%)
        margin_rate = Decimal("0.175")  # 17.5% 평균
        
        total_cost = energy_amount * base_rate * (1 + margin_rate)
        
        logger.info(f"에너지 비용 계산: {energy_amount} * {base_rate} * {1 + margin_rate} = {total_cost}")
        return total_cost

    async def _get_current_energy_rate(self, source_type: EnergySourceType) -> Decimal:
        """현재 에너지 단가 조회"""
        # 실제로는 외부 API나 설정에서 가져옴
        base_rates = {
            EnergySourceType.SELF_STAKING: Decimal("0.0001"),  # 가장 저렴
            EnergySourceType.TRONZAP: Decimal("0.00012"),
            EnergySourceType.TRONNRG: Decimal("0.00015"),
        }
        return base_rates.get(source_type, Decimal("0.0002"))
