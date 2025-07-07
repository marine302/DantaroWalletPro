"""
TRON 에너지 풀 매니저
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from tronpy import Tron
from tronpy.keys import PrivateKey

from app.models.energy_pool import EnergyPoolModel, EnergyPoolStatus, EnergyUsageLog, EnergyPriceHistory
from app.models.transaction import Transaction
from app.models.user import User
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class EnergyPoolManager:
    def __init__(self, db: AsyncSession, tron_client: Tron, redis_client):
        self.db = db
        self.tron = tron_client
        self.redis = redis_client
        self.ENERGY_PER_TRX = 1000  # 1 TRX = 1000 Energy (대략적인 비율)

    async def create_energy_pool(
        self,
        pool_name: str,
        owner_private_key: str,
        initial_trx_amount: Decimal
    ) -> EnergyPoolModel:
        """새 에너지 풀 생성"""
        try:
            # 프라이빗 키로 주소 생성
            priv_key = PrivateKey(bytes.fromhex(owner_private_key))
            owner_address = priv_key.public_key.to_base58check_address()

            # TRX 동결하여 에너지 획득
            frozen_result = await self.freeze_trx_for_energy(
                owner_address, 
                owner_private_key, 
                initial_trx_amount
            )

            # 에너지 풀 DB 생성
            pool = EnergyPoolModel(
                pool_name=pool_name,
                owner_address=owner_address,
                frozen_trx=initial_trx_amount,
                total_energy=frozen_result['energy_received'],
                available_energy=frozen_result['energy_received'],
                status=EnergyPoolStatus.ACTIVE
            )

            self.db.add(pool)
            await self.db.commit()
            await self.db.refresh(pool)

            # 캐시에 저장
            await self.cache_pool_status(pool)

            logger.info(f"에너지 풀 생성 완료: {pool_name} ({owner_address})")
            return pool

        except Exception as e:
            logger.error(f"에너지 풀 생성 실패: {str(e)}")
            await self.db.rollback()
            raise

    async def freeze_trx_for_energy(
        self,
        owner_address: str,
        private_key: str,
        amount: Decimal
    ) -> Dict:
        """TRX를 동결하여 에너지 획득"""
        try:
            # TRX를 SUN 단위로 변환 (1 TRX = 1,000,000 SUN)
            amount_sun = int(amount * 1_000_000)

            # Stake 2.0 사용 (TRON의 새로운 스테이킹 방식)
            txn = (
                self.tron.transaction_builder.freeze_balance_v2(
                    owner_address=owner_address,
                    frozen_balance=amount_sun,
                    resource="ENERGY"
                )
            )

            # 트랜잭션 서명 및 전송
            txn = txn.sign(PrivateKey(bytes.fromhex(private_key)))
            result = txn.broadcast()

            # 에너지 계산 (대략적인 추정치)
            energy_received = int(amount * self.ENERGY_PER_TRX)

            return {
                "success": True,
                "tx_id": result['txid'],
                "frozen_amount": amount,
                "energy_received": energy_received
            }

        except Exception as e:
            logger.error(f"TRX 동결 실패: {str(e)}")
            raise

    async def check_pool_status(self, pool_id: int) -> Dict:
        """에너지 풀 상태 확인"""
        # 캐시 확인
        cached = await self.redis.get(f"energy_pool:{pool_id}")
        if cached:
            return json.loads(cached)

        pool = await self.db.get(EnergyPoolModel, pool_id)
        if not pool:
            raise ValueError("에너지 풀을 찾을 수 없습니다")

        # TRON 네트워크에서 실제 에너지 확인
        account_resource = self.tron.get_account_resource(pool.owner_address)

        # 사용 가능 에너지 계산
        total_energy = account_resource.get('EnergyLimit', 0)
        used_energy = account_resource.get('EnergyUsed', 0)
        available_energy = total_energy - used_energy

        # 상태 업데이트
        pool.total_energy = total_energy
        pool.used_energy = used_energy
        pool.available_energy = available_energy

        # 상태 판단
        usage_percentage = (used_energy / total_energy * 100) if total_energy > 0 else 100

        if usage_percentage >= 100:
            pool.status = EnergyPoolStatus.DEPLETED
        elif usage_percentage >= 100 - pool.critical_threshold:
            pool.status = EnergyPoolStatus.CRITICAL
        elif usage_percentage >= 100 - pool.low_threshold:
            pool.status = EnergyPoolStatus.LOW
        else:
            pool.status = EnergyPoolStatus.ACTIVE

        pool.last_checked_at = datetime.utcnow()
        await self.db.commit()

        status_data = {
            "pool_id": pool.id,
            "status": pool.status.value,
            "total_energy": total_energy,
            "available_energy": available_energy,
            "used_energy": used_energy,
            "usage_percentage": usage_percentage,
            "frozen_trx": float(pool.frozen_trx),
            "auto_refill": pool.auto_refill,
            "last_checked": pool.last_checked_at.isoformat()
        }

        # 캐시 저장 (5분)
        await self.redis.setex(
            f"energy_pool:{pool_id}",
            300,
            json.dumps(status_data)
        )

        # 자동 충전 확인
        if pool.auto_refill and usage_percentage >= 100 - pool.auto_refill_trigger:
            await self.trigger_auto_refill(pool)

        return status_data

    async def estimate_energy_cost(
        self,
        transaction_type: str,
        token_type: str = "TRC20"
    ) -> Dict:
        """트랜잭션 유형별 에너지 비용 추정"""
        # TRON 트랜잭션별 평균 에너지 소비량
        energy_costs = {
            "TRC20": {
                "transfer": 13_000,      # USDT 전송
                "approve": 12_000,       # 승인
                "transferFrom": 29_000,  # 대리 전송
            },
            "TRX": {
                "transfer": 0,  # TRX 전송은 대역폭만 사용
            }
        }

        base_cost = energy_costs.get(token_type, {}).get(transaction_type, 15_000)

        # 네트워크 혼잡도 반영
        congestion_factor = await self.get_network_congestion()
        adjusted_cost = int(base_cost * (1 + congestion_factor / 100))

        # 현재 에너지 가격 조회
        energy_price = await self.get_current_energy_price()

        return {
            "transaction_type": transaction_type,
            "base_energy_cost": base_cost,
            "adjusted_energy_cost": adjusted_cost,
            "congestion_factor": congestion_factor,
            "energy_price_trx": float(energy_price),
            "estimated_cost_trx": adjusted_cost * float(energy_price),
            "estimated_cost_usd": adjusted_cost * float(energy_price) * await self.get_trx_price()
        }

    async def get_network_congestion(self) -> float:
        """네트워크 혼잡도 조회"""
        try:
            # TRON 네트워크 상태 조회
            chain_parameters = self.tron.get_chain_parameters()
            # 실제 구현에서는 더 정확한 혼잡도 계산 로직 필요
            return 20.0  # 기본값 20%
        except Exception as e:
            logger.warning(f"네트워크 혼잡도 조회 실패: {str(e)}")
            return 20.0

    async def get_current_energy_price(self) -> Decimal:
        """현재 에너지 가격 조회"""
        try:
            # 캐시에서 먼저 조회
            cached_price = await self.redis.get("energy_price:current")
            if cached_price:
                price_data = json.loads(cached_price)
                return Decimal(str(price_data['energy_price_trx']))

            # DB에서 최신 가격 조회
            result = await self.db.execute(
                select(EnergyPriceHistory)
                .order_by(EnergyPriceHistory.recorded_at.desc())
                .limit(1)
            )
            latest_price = result.scalar_one_or_none()

            if latest_price:
                return latest_price.energy_price_trx
            else:
                # 기본값
                return Decimal('0.000065')

        except Exception as e:
            logger.warning(f"에너지 가격 조회 실패: {str(e)}")
            return Decimal('0.000065')

    async def get_trx_price(self) -> float:
        """TRX 가격 조회 (USD)"""
        try:
            # 실제 구현에서는 CoinGecko 등 외부 API 호출
            return 0.08  # 기본값
        except Exception as e:
            logger.warning(f"TRX 가격 조회 실패: {str(e)}")
            return 0.08

    async def trigger_auto_refill(self, pool: EnergyPoolModel):
        """자동 충전 실행"""
        try:
            logger.info(f"자동 충전 시작: Pool {pool.id}")
            # 실제 자동 충전 로직 구현
            # 이 부분은 보안상 중요하므로 별도 보안 처리 필요
            pass
        except Exception as e:
            logger.error(f"자동 충전 실패: {str(e)}")

    async def cache_pool_status(self, pool: EnergyPoolModel):
        """에너지 풀 상태를 캐시에 저장"""
        status_data = {
            "pool_id": pool.id,
            "status": pool.status.value,
            "total_energy": pool.total_energy,
            "available_energy": pool.available_energy,
            "used_energy": pool.used_energy,
            "frozen_trx": float(pool.frozen_trx),
            "auto_refill": pool.auto_refill,
            "last_checked": pool.last_checked_at.isoformat() if pool.last_checked_at else None
        }

        await self.redis.setex(
            f"energy_pool:{pool.id}",
            300,  # 5분
            json.dumps(status_data)
        )

    async def get_all_active_pools(self) -> List[EnergyPoolModel]:
        """모든 활성 에너지 풀 조회"""
        result = await self.db.execute(
            select(EnergyPoolModel).where(
                EnergyPoolModel.status != EnergyPoolStatus.MAINTENANCE
            )
        )
        return result.scalars().all()

    async def simulate_usage(
        self,
        transaction_count: int,
        transaction_types: List[str],
        time_period_hours: int = 24
    ) -> Dict:
        """에너지 사용량 시뮬레이션"""
        total_energy_required = 0
        
        for tx_type in transaction_types:
            cost_estimate = await self.estimate_energy_cost(tx_type)
            total_energy_required += cost_estimate['adjusted_energy_cost'] * transaction_count

        # 현재 풀 용량 확인
        pools = await self.get_all_active_pools()
        total_available = sum(pool.available_energy for pool in pools)
        
        can_handle = total_available >= total_energy_required
        shortage = max(0, total_energy_required - total_available)

        # 비용 계산
        energy_price = await self.get_current_energy_price()
        estimated_cost_trx = total_energy_required * float(energy_price)
        estimated_cost_usd = estimated_cost_trx * await self.get_trx_price()

        recommendations = []
        if not can_handle:
            recommendations.append(f"에너지 부족: {shortage:,} 에너지 추가 필요")
            recommendations.append(f"TRX 동결 권장: {shortage / self.ENERGY_PER_TRX:.2f} TRX")

        return {
            "total_energy_required": total_energy_required,
            "estimated_cost_trx": estimated_cost_trx,
            "estimated_cost_usd": estimated_cost_usd,
            "current_pool_capacity": total_available / total_energy_required if total_energy_required > 0 else 1.0,
            "can_handle": can_handle,
            "shortage_amount": shortage if shortage > 0 else None,
            "recommendations": recommendations
        }
