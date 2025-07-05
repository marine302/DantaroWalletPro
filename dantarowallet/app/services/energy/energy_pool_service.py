"""
TRON Energy Pool 관리 서비스
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.tron import TronService
from app.models.energy_pool import EnergyPool, EnergyPriceHistory, EnergyUsageLog
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EnergyPoolService:
    """TRON Energy Pool 관리 서비스"""

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
            total_freeze_cost=Decimal("0"),
            is_active=True,
            notes="기본 에너지 풀"
        )

        self.db.add(energy_pool)
        await self.db.commit()
        await self.db.refresh(energy_pool)

        logger.info(f"Default energy pool created: {energy_pool.id}")
        return energy_pool

    async def get_energy_pool_status(self, pool_id: Optional[int] = None) -> Dict[str, Any]:
        """에너지 풀 현황 조회"""
        if pool_id:
            pool = await self.db.get(EnergyPool, pool_id)
        else:
            pool = await self.get_default_energy_pool()

        if not pool:
            return {
                "error": "Energy pool not found",
                "exists": False
            }

        # 최근 24시간 사용량 계산
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_usage = await self.db.execute(
            select(func.sum(EnergyUsageLog.energy_consumed))
            .filter(
                and_(
                    EnergyUsageLog.energy_pool_id == pool.id,
                    EnergyUsageLog.created_at >= yesterday
                )
            )
        )
        recent_energy_usage = recent_usage.scalar() or 0

        # 사용률 계산
        utilization_rate = 0.0
        if pool.available_energy > 0:
            utilization_rate = (recent_energy_usage / pool.available_energy) * 100

        return {
            "exists": True,
            "pool_id": pool.id,
            "pool_name": pool.pool_name,
            "wallet_address": pool.wallet_address,
            "total_frozen_trx": float(pool.total_frozen_trx),
            "frozen_for_energy": float(pool.frozen_for_energy),
            "frozen_for_bandwidth": float(pool.frozen_for_bandwidth),
            "available_energy": pool.available_energy,
            "available_bandwidth": pool.available_bandwidth,
            "energy_threshold": pool.energy_threshold,
            "bandwidth_threshold": pool.bandwidth_threshold,
            "recent_24h_energy_usage": recent_energy_usage,
            "energy_utilization_rate": round(utilization_rate, 2),
            "needs_refreeze_energy": pool.available_energy < pool.energy_threshold,
            "needs_refreeze_bandwidth": pool.available_bandwidth < pool.bandwidth_threshold,
            "auto_refreeze_enabled": pool.auto_refreeze_enabled,
            "last_updated": pool.last_updated.isoformat() if pool.last_updated else None,
            "is_active": pool.is_active
        }

    async def log_energy_usage(self,
                              energy_pool_id: int,
                              transaction_hash: str,
                              transaction_type: str,
                              energy_consumed: int,
                              bandwidth_consumed: int,
                              user_id: Optional[int] = None,
                              from_address: Optional[str] = None,
                              to_address: Optional[str] = None,
                              amount: Optional[Decimal] = None,
                              asset: Optional[str] = None) -> EnergyUsageLog:
        """에너지 사용 로그 기록"""

        # TRX 환산 비용 계산 (예시)
        trx_cost = Decimal("0")
        if energy_consumed > 0:
            # 1 Energy ≈ 0.00001 TRX (예시 환율)
            trx_cost = Decimal(str(energy_consumed)) * Decimal("0.00001")

        usage_log = EnergyUsageLog(
            energy_pool_id=energy_pool_id,
            transaction_hash=transaction_hash,
            transaction_type=transaction_type,
            energy_consumed=energy_consumed,
            bandwidth_consumed=bandwidth_consumed,
            trx_cost_equivalent=trx_cost,
            user_id=user_id,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            asset=asset,
            timestamp=datetime.utcnow()
        )

        self.db.add(usage_log)

        # 에너지 풀 사용량 업데이트
        await self.update_energy_pool_consumption(energy_pool_id, energy_consumed, bandwidth_consumed)

        await self.db.commit()
        logger.info(f"Energy usage logged: {transaction_hash}, Energy: {energy_consumed}, Bandwidth: {bandwidth_consumed}")

        return usage_log

    async def update_energy_pool_consumption(self, pool_id: int, energy_consumed: int, bandwidth_consumed: int):
        """에너지 풀 소비량 업데이트"""
        pool = await self.db.get(EnergyPool, pool_id)
        if pool:
            pool.available_energy = max(0, pool.available_energy - energy_consumed)
            pool.available_bandwidth = max(0, pool.available_bandwidth - bandwidth_consumed)
            pool.daily_energy_consumption += energy_consumed
            pool.daily_bandwidth_consumption += bandwidth_consumed
            pool.last_updated = datetime.utcnow()

    async def get_energy_usage_statistics(self,
                                        pool_id: Optional[int] = None,
                                        days: int = 7) -> Dict[str, Any]:
        """에너지 사용 통계 조회"""
        if not pool_id:
            pool = await self.get_default_energy_pool()
            pool_id = pool.id if pool else None

        if not pool_id:
            return {"error": "No energy pool found"}

        start_date = datetime.utcnow() - timedelta(days=days)

        # 일별 사용량 통계
        daily_stats = await self.db.execute(
            select(
                func.date(EnergyUsageLog.timestamp).label('date'),
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.sum(EnergyUsageLog.bandwidth_consumed).label('total_bandwidth'),
                func.count(EnergyUsageLog.id).label('transaction_count')
            )
            .filter(
                and_(
                    EnergyUsageLog.energy_pool_id == pool_id,
                    EnergyUsageLog.timestamp >= start_date
                )
            )
            .group_by(func.date(EnergyUsageLog.timestamp))
            .order_by(desc(func.date(EnergyUsageLog.timestamp)))
        )

        daily_data = []
        for row in daily_stats:
            daily_data.append({
                "date": str(row.date),
                "energy_consumed": row.total_energy or 0,
                "bandwidth_consumed": row.total_bandwidth or 0,
                "transaction_count": row.transaction_count or 0
            })

        # 트랜잭션 타입별 통계
        type_stats = await self.db.execute(
            select(
                EnergyUsageLog.transaction_type,
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.count(EnergyUsageLog.id).label('count')
            )
            .filter(
                and_(
                    EnergyUsageLog.energy_pool_id == pool_id,
                    EnergyUsageLog.timestamp >= start_date
                )
            )
            .group_by(EnergyUsageLog.transaction_type)
        )

        type_data = []
        for row in type_stats:
            type_data.append({
                "transaction_type": row.transaction_type,
                "total_energy": row.total_energy or 0,
                "count": row.count or 0
            })

        return {
            "pool_id": pool_id,
            "period_days": days,
            "daily_statistics": daily_data,
            "transaction_type_statistics": type_data
        }

    async def record_energy_price(self,
                                trx_price_usd: Decimal,
                                energy_per_trx: int,
                                bandwidth_per_trx: int,
                                source: str = "API") -> EnergyPriceHistory:
        """에너지 가격 정보 기록"""
        price_record = EnergyPriceHistory(
            trx_price_usd=trx_price_usd,
            energy_per_trx=energy_per_trx,
            bandwidth_per_trx=bandwidth_per_trx,
            source=source,
            recorded_at=datetime.utcnow()
        )

        self.db.add(price_record)
        await self.db.commit()

        logger.info(f"Energy price recorded: TRX ${trx_price_usd}, Energy/TRX: {energy_per_trx}")
        return price_record

    async def check_refreeze_needed(self, pool_id: Optional[int] = None) -> Dict[str, Any]:
        """Refreeze 필요 여부 확인"""
        if not pool_id:
            pool = await self.get_default_energy_pool()
        else:
            pool = await self.db.get(EnergyPool, pool_id)

        if not pool:
            return {"error": "Pool not found"}

        needs_energy_refreeze = pool.available_energy < pool.energy_threshold
        needs_bandwidth_refreeze = pool.available_bandwidth < pool.bandwidth_threshold

        # 예상 필요 TRX 계산
        energy_needed = max(0, pool.energy_threshold - pool.available_energy)
        bandwidth_needed = max(0, pool.bandwidth_threshold - pool.available_bandwidth)

        # 최신 가격 정보 조회
        latest_price = await self.db.execute(
            select(EnergyPriceHistory)
            .order_by(desc(EnergyPriceHistory.recorded_at))
            .limit(1)
        )
        price_info = latest_price.scalar_one_or_none()

        estimated_trx_needed = Decimal("0")
        if price_info:
            if energy_needed > 0 and price_info.energy_per_trx > 0:
                estimated_trx_needed += Decimal(str(energy_needed)) / Decimal(str(price_info.energy_per_trx))
            if bandwidth_needed > 0 and price_info.bandwidth_per_trx > 0:
                estimated_trx_needed += Decimal(str(bandwidth_needed)) / Decimal(str(price_info.bandwidth_per_trx))

        return {
            "pool_id": pool.id,
            "needs_energy_refreeze": needs_energy_refreeze,
            "needs_bandwidth_refreeze": needs_bandwidth_refreeze,
            "energy_needed": energy_needed,
            "bandwidth_needed": bandwidth_needed,
            "estimated_trx_needed": float(estimated_trx_needed),
            "auto_refreeze_enabled": pool.auto_refreeze_enabled,
            "current_energy": pool.available_energy,
            "current_bandwidth": pool.available_bandwidth,
            "energy_threshold": pool.energy_threshold,
            "bandwidth_threshold": pool.bandwidth_threshold
        }

    async def sync_with_tron_network(self, pool_id: Optional[int] = None) -> Dict[str, Any]:
        """TRON 네트워크와 실시간 동기화"""
        if not pool_id:
            pool = await self.get_default_energy_pool()
            if not pool:
                return {"error": "No energy pool found"}
            pool_id = pool.id
        else:
            pool = await self.db.get(EnergyPool, pool_id)
            if not pool:
                return {"error": f"Pool {pool_id} not found"}

        try:
            # TRON 네트워크에서 실시간 데이터 조회
            tron_data = await self.tron_service.get_account_resources(pool.wallet_address)

            if "error" in tron_data:
                return {"error": f"Failed to sync with TRON: {tron_data['error']}"}

            # 데이터베이스 업데이트
            pool.available_energy = tron_data["energy"]["available"]
            pool.available_bandwidth = tron_data["bandwidth"]["available"]
            pool.frozen_for_energy = Decimal(str(tron_data["energy"]["frozen_trx"]))
            pool.frozen_for_bandwidth = Decimal(str(tron_data["bandwidth"]["frozen_trx"]))
            pool.total_frozen_trx = Decimal(str(tron_data["total_frozen_trx"]))
            pool.last_updated = datetime.utcnow()

            await self.db.commit()

            # 에너지 가격 정보도 업데이트
            price_info = await self.tron_service.get_energy_price_info()
            if "error" not in price_info:
                await self.record_energy_price(
                    trx_price_usd=Decimal("0.0"),  # 실제 TRX 가격은 외부 API에서
                    energy_per_trx=price_info["energy_per_trx"],
                    bandwidth_per_trx=price_info["bandwidth_per_trx"],
                    source="TRON_Network_Sync"
                )

            logger.info(f"Energy pool {pool_id} synced with TRON network successfully")

            return {
                "success": True,
                "pool_id": pool_id,
                "synced_at": datetime.utcnow().isoformat(),
                "tron_data": tron_data,
                "price_info": price_info
            }

        except Exception as e:
            logger.error(f"Error syncing with TRON network: {e}")
            return {"error": f"Sync failed: {str(e)}"}

    async def auto_check_refreeze_needed(self, pool_id: Optional[int] = None) -> Dict[str, Any]:
        """자동 Refreeze 필요 여부 체크 및 알림"""
        refreeze_status = await self.check_refreeze_needed(pool_id)

        if "error" in refreeze_status:
            return refreeze_status

        # Refreeze 필요한 경우 자동 알림 생성
        if refreeze_status["needs_energy_refreeze"] or refreeze_status["needs_bandwidth_refreeze"]:

            # 예상 비용 계산
            estimated_cost = refreeze_status.get("estimated_trx_needed", 0)

            alert_message = f"""
            🚨 Energy Pool Refreeze 필요

            Pool ID: {refreeze_status['pool_id']}
            에너지 필요: {'YES' if refreeze_status['needs_energy_refreeze'] else 'NO'}
            대역폭 필요: {'YES' if refreeze_status['needs_bandwidth_refreeze'] else 'NO'}

            현재 상태:
            - 에너지: {refreeze_status['current_energy']:,} / {refreeze_status['energy_threshold']:,}
            - 대역폭: {refreeze_status['current_bandwidth']:,} / {refreeze_status['bandwidth_threshold']:,}

            예상 필요 TRX: {estimated_cost:.2f}

            자동 Refreeze: {'활성화' if refreeze_status.get('auto_refreeze_enabled') else '비활성화'}
            """

            # 여기에 실제 알림 발송 로직 추가 (이메일, 슬랙, 웹훅 등)
            logger.warning(f"Refreeze needed for pool {refreeze_status['pool_id']}: {alert_message}")

            return {
                "alert_triggered": True,
                "alert_message": alert_message,
                **refreeze_status
            }

        return {
            "alert_triggered": False,
            **refreeze_status
        }

    async def get_network_status_summary(self) -> Dict[str, Any]:
        """TRON 네트워크 전체 상태 요약"""
        try:
            # 기본 풀 조회
            pool = await self.get_default_energy_pool()
            if not pool:
                return {"error": "No energy pool configured"}

            # TRON 네트워크 동기화
            sync_result = await self.sync_with_tron_network(pool.id)

            # 에너지 가격 정보
            price_info = await self.tron_service.get_energy_price_info()

            # 최근 사용량 통계
            usage_stats = await self.get_energy_usage_statistics(days=1)  # 오늘

            # 트랜잭션 비용 예상
            usdt_cost = await self.tron_service.estimate_transaction_cost("USDT_TRANSFER")
            trx_cost = await self.tron_service.estimate_transaction_cost("TRX_TRANSFER")

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "pool_status": sync_result,
                "network_prices": price_info,
                "today_usage": usage_stats,
                "transaction_costs": {
                    "usdt_transfer": usdt_cost,
                    "trx_transfer": trx_cost
                },
                "health_check": "OK" if "error" not in sync_result else "ERROR"
            }

        except Exception as e:
            logger.error(f"Error getting network status summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "health_check": "ERROR"
            }
