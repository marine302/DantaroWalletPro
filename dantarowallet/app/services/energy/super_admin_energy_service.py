"""
슈퍼 어드민 에너지 서비스
"""

from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.energy_pool import EnergyPoolModel
from app.schemas.energy import EnergyPoolStatus


class SuperAdminEnergyService:
    """슈퍼 어드민용 에너지 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_total_energy_stats(self) -> Dict:
        """전체 에너지 통계 조회"""
        try:
            # 실제 DB에서 에너지 통계를 가져오는 로직
            total_pools = self.db.query(EnergyPoolModel).count()
            pools = self.db.query(EnergyPoolModel).all()
            total_energy = sum(
                getattr(pool, 'available_energy', 0) or 0
                for pool in pools
            )

            return {
                "total_pools": total_pools,
                "total_energy": total_energy,
                "active_pools": self.db.query(EnergyPoolModel)
                .filter(EnergyPoolModel.status == "ACTIVE")
                .count(),
            }
        except Exception:
            return {
                "total_pools": 0,
                "total_energy": 0,
                "active_pools": 0,
            }

    def get_energy_pool_status(self) -> List[EnergyPoolStatus]:
        """에너지 풀 상태 조회"""
        try:
            pools = self.db.query(EnergyPoolModel).all()
            return [
                EnergyPoolStatus(
                    total_energy=getattr(pool, 'total_energy', 0) or 0,
                    available_energy=getattr(pool, 'available_energy', 0) or 0,
                    reserved_energy=0,
                    allocated_energy=0,
                    daily_consumption=0,
                    alert_threshold=1000,
                    critical_threshold=500,
                    is_sufficient=(getattr(pool, 'available_energy', 0) or 0) > 1000,
                    partner_count=0,
                    last_updated=datetime.now(),
                )
                for pool in pools
            ]
        except Exception:
            return []

    async def get_total_energy_status(self) -> Dict:
        """전체 에너지 상태 조회"""
        try:
            pools = self.db.query(EnergyPoolModel).all()
            total_energy = sum(
                getattr(pool, 'available_energy', 0) or 0
                for pool in pools
            )
            allocated_energy = sum(
                getattr(pool, 'allocated_energy', 0) or 0
                for pool in pools
            )

            return {
                "total_energy": total_energy,
                "allocated_energy": allocated_energy,
                "available_energy": total_energy - allocated_energy,
                "utilization_rate": (allocated_energy / total_energy * 100) if total_energy > 0 else 0,
                "active_pools": len([p for p in pools if getattr(p, 'status', None) == 'ACTIVE']),
                "total_pools": len(pools),
            }
        except Exception:
            return {
                "total_energy": 0,
                "allocated_energy": 0,
                "available_energy": 0,
                "utilization_rate": 0,
                "active_pools": 0,
                "total_pools": 0,
            }

    async def get_energy_statistics(self) -> Dict:
        """에너지 통계 조회"""
        try:
            pools = self.db.query(EnergyPoolModel).all()
            total_energy = sum(
                getattr(pool, 'available_energy', 0) or 0
                for pool in pools
            )

            return {
                "total_energy": total_energy,
                "total_pools": len(pools),
                "avg_pool_size": total_energy / len(pools) if pools else 0,
                "largest_pool": max((getattr(p, 'available_energy', 0) or 0 for p in pools), default=0),
                "smallest_pool": min((getattr(p, 'available_energy', 0) or 0 for p in pools), default=0),
            }
        except Exception:
            return {
                "total_energy": 0,
                "total_pools": 0,
                "avg_pool_size": 0,
                "largest_pool": 0,
                "smallest_pool": 0,
            }
