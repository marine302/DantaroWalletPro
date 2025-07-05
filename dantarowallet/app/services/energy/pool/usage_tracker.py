"""
에너지 사용량 추적 및 모니터링
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from app.models.energy_pool import EnergyPool, EnergyUsageLog
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UsageTracker:
    """에너지 사용량 추적 및 모니터링"""

    def __init__(self, db: AsyncSession):
        self.db = db

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
        usage_log = EnergyUsageLog(
            energy_pool_id=energy_pool_id,
            transaction_hash=transaction_hash,
            energy_consumed=energy_consumed,
            bandwidth_consumed=bandwidth_consumed,
            fee_paid=fee_paid,
            simulation=simulation,
        )

        self.db.add(usage_log)

        # 실제 사용량인 경우 풀 정보 업데이트
        if not simulation:
            await self._update_pool_consumption(
                energy_pool_id, energy_consumed, bandwidth_consumed
            )

        await self.db.commit()
        await self.db.refresh(usage_log)

        logger.info(f"Recorded energy usage: {energy_consumed} energy, {bandwidth_consumed} bandwidth")
        return usage_log

    async def get_usage_statistics(
        self, 
        energy_pool_id: int, 
        days_back: int = 7
    ) -> Dict[str, any]:
        """사용량 통계 조회"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # 기본 통계
        result = await self.db.execute(
            select(
                func.count(EnergyUsageLog.id).label("total_transactions"),
                func.sum(EnergyUsageLog.energy_consumed).label("total_energy"),
                func.sum(EnergyUsageLog.bandwidth_consumed).label("total_bandwidth"),
                func.avg(EnergyUsageLog.energy_consumed).label("avg_energy"),
                func.sum(EnergyUsageLog.fee_paid).label("total_fees"),
            ).filter(
                and_(
                    EnergyUsageLog.energy_pool_id == energy_pool_id,
                    EnergyUsageLog.created_at >= start_date,
                    EnergyUsageLog.simulation == False,
                )
            )
        )
        
        stats = result.fetchone()
        
        # 일별 사용량
        daily_usage = await self._get_daily_usage(energy_pool_id, start_date, end_date)
        
        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_transactions": stats.total_transactions or 0,
            "total_energy_consumed": stats.total_energy or 0,
            "total_bandwidth_consumed": stats.total_bandwidth or 0,
            "average_energy_per_tx": float(stats.avg_energy or 0),
            "total_fees_paid": float(stats.total_fees or 0),
            "daily_usage": daily_usage,
        }

    async def get_recent_usage(
        self, 
        energy_pool_id: int, 
        limit: int = 20
    ) -> List[Dict[str, any]]:
        """최근 사용 내역 조회"""
        result = await self.db.execute(
            select(EnergyUsageLog)
            .filter(EnergyUsageLog.energy_pool_id == energy_pool_id)
            .order_by(desc(EnergyUsageLog.created_at))
            .limit(limit)
        )
        
        usage_logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "transaction_hash": log.transaction_hash,
                "energy_consumed": log.energy_consumed,
                "bandwidth_consumed": log.bandwidth_consumed,
                "fee_paid": float(log.fee_paid),
                "created_at": log.created_at.isoformat(),
                "is_simulation": log.simulation,
            }
            for log in usage_logs
        ]

    async def check_usage_alerts(self, energy_pool_id: int) -> List[Dict[str, any]]:
        """사용량 알림 확인"""
        alerts = []
        
        # 풀 정보 조회
        result = await self.db.execute(
            select(EnergyPool).filter(EnergyPool.id == energy_pool_id)
        )
        pool = result.scalar_one_or_none()
        
        if not pool:
            return alerts

        # 에너지 부족 확인
        if pool.available_energy < pool.energy_threshold:
            alerts.append({
                "type": "energy_low",
                "message": f"Energy below threshold: {pool.available_energy} < {pool.energy_threshold}",
                "severity": "warning" if pool.available_energy > pool.energy_threshold * 0.5 else "critical",
                "current_value": pool.available_energy,
                "threshold": pool.energy_threshold,
            })

        # 대역폭 부족 확인
        if pool.available_bandwidth < pool.bandwidth_threshold:
            alerts.append({
                "type": "bandwidth_low",
                "message": f"Bandwidth below threshold: {pool.available_bandwidth} < {pool.bandwidth_threshold}",
                "severity": "warning" if pool.available_bandwidth > pool.bandwidth_threshold * 0.5 else "critical",
                "current_value": pool.available_bandwidth,
                "threshold": pool.bandwidth_threshold,
            })

        # 일일 사용량 급증 확인
        today_usage = await self._get_today_usage(energy_pool_id)
        if today_usage > pool.daily_energy_consumption * 1.5:  # 평소의 1.5배 이상
            alerts.append({
                "type": "usage_spike",
                "message": f"Daily usage spike detected: {today_usage} vs normal {pool.daily_energy_consumption}",
                "severity": "info",
                "current_value": today_usage,
                "normal_value": pool.daily_energy_consumption,
            })

        return alerts

    async def _update_pool_consumption(
        self, 
        energy_pool_id: int, 
        energy_consumed: int, 
        bandwidth_consumed: int
    ):
        """풀 소비량 정보 업데이트"""
        result = await self.db.execute(
            select(EnergyPool).filter(EnergyPool.id == energy_pool_id)
        )
        pool = result.scalar_one_or_none()
        
        if pool:
            pool.available_energy = max(0, pool.available_energy - energy_consumed)
            pool.available_bandwidth = max(0, pool.available_bandwidth - bandwidth_consumed)
            
            # 일일 소비량 업데이트 (이동 평균 방식)
            pool.daily_energy_consumption = int(
                (pool.daily_energy_consumption * 0.9) + (energy_consumed * 0.1)
            )
            pool.daily_bandwidth_consumption = int(
                (pool.daily_bandwidth_consumption * 0.9) + (bandwidth_consumed * 0.1)
            )

    async def _get_daily_usage(
        self, 
        energy_pool_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, any]]:
        """일별 사용량 조회"""
        result = await self.db.execute(
            select(
                func.date(EnergyUsageLog.created_at).label("date"),
                func.sum(EnergyUsageLog.energy_consumed).label("energy"),
                func.sum(EnergyUsageLog.bandwidth_consumed).label("bandwidth"),
                func.count(EnergyUsageLog.id).label("transactions"),
            )
            .filter(
                and_(
                    EnergyUsageLog.energy_pool_id == energy_pool_id,
                    EnergyUsageLog.created_at >= start_date,
                    EnergyUsageLog.created_at <= end_date,
                    EnergyUsageLog.simulation == False,
                )
            )
            .group_by(func.date(EnergyUsageLog.created_at))
            .order_by(func.date(EnergyUsageLog.created_at))
        )
        
        return [
            {
                "date": row.date.isoformat(),
                "energy_consumed": row.energy or 0,
                "bandwidth_consumed": row.bandwidth or 0,
                "transaction_count": row.transactions or 0,
            }
            for row in result.fetchall()
        ]

    async def _get_today_usage(self, energy_pool_id: int) -> int:
        """오늘 에너지 사용량 조회"""
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        
        result = await self.db.execute(
            select(func.sum(EnergyUsageLog.energy_consumed))
            .filter(
                and_(
                    EnergyUsageLog.energy_pool_id == energy_pool_id,
                    EnergyUsageLog.created_at >= start_of_day,
                    EnergyUsageLog.simulation == False,
                )
            )
        )
        
        return result.scalar() or 0
