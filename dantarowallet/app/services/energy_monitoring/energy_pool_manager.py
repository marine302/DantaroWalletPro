"""
에너지 모니터링 서비스 - 에너지 풀 매니저
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.energy_pool import EnergyStatus, PartnerEnergyPool
from app.models.partner import Partner

from .utils import safe_decimal_to_float, safe_int_conversion

# TRON 관련 import
try:
    from tronpy import Tron
    from tronpy.exceptions import BadSignature as TronError

    TRON_AVAILABLE = True
except ImportError:
    Tron = None
    TronError = Exception
    TRON_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnergyPoolManager:
    """에너지 풀 관리 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        if TRON_AVAILABLE and Tron:
            network = getattr(settings, "TRON_NETWORK", "nile")
            self.tron = Tron(network="mainnet" if network == "mainnet" else "nile")
        else:
            self.tron = None

    async def get_or_create_energy_pool(self, partner_id: int) -> PartnerEnergyPool:
        """파트너 에너지 풀 조회 또는 생성"""
        # 기존 에너지 풀 조회
        result = await self.db.execute(
            select(PartnerEnergyPool).where(PartnerEnergyPool.partner_id == partner_id)
        )
        energy_pool = result.scalar_one_or_none()

        if not energy_pool:
            # 에너지 풀 초기화
            energy_pool = await self._initialize_partner_energy_pool(partner_id)
            await self.db.commit()
            await self.db.refresh(energy_pool)

        return energy_pool

    async def _initialize_partner_energy_pool(
        self, partner_id: int
    ) -> PartnerEnergyPool:
        """파트너 에너지 풀 초기화"""
        # 파트너 정보 조회
        result = await self.db.execute(select(Partner).where(Partner.id == partner_id))
        partner = result.scalar_one_or_none()

        if not partner:
            raise ValueError(f"Partner {partner_id} not found")

        # 기본 지갑 주소 설정
        wallet_address = getattr(
            partner, "wallet_address", f"TPartner{partner_id}DefaultWallet"
        )

        energy_pool = PartnerEnergyPool(
            partner_id=partner_id,
            wallet_address=wallet_address,
            total_energy=Decimal("0"),
            available_energy=Decimal("0"),
            used_energy=Decimal("0"),
            energy_limit=Decimal("0"),
            total_bandwidth=Decimal("0"),
            available_bandwidth=Decimal("0"),
            frozen_trx_amount=Decimal("0"),
            frozen_for_energy=Decimal("0"),
            frozen_for_bandwidth=Decimal("0"),
            status=EnergyStatus.SUFFICIENT,
            daily_average_usage=Decimal("0"),
            warning_threshold=30,
            critical_threshold=10,
            auto_response_enabled=True,
            last_checked_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        self.db.add(energy_pool)
        await self.db.flush()

        logger.info(f"Initialized energy pool for partner {partner_id}")
        return energy_pool

    async def update_energy_pool_from_blockchain(self, energy_pool: PartnerEnergyPool):
        """블록체인에서 에너지 풀 정보 업데이트"""
        if not self.tron:
            logger.warning("TRON client not available, using mock data")
            await self._update_with_mock_data(energy_pool)
            return

        try:
            # 지갑 주소를 문자열로 변환
            wallet_address = str(energy_pool.wallet_address)

            # 계정 리소스 정보 조회
            account_info = self.tron.get_account_resource(wallet_address)

            # 에너지 정보 추출
            total_energy = account_info.get("EnergyLimit", 0)
            used_energy = account_info.get("EnergyUsed", 0)
            available_energy = max(0, total_energy - used_energy)

            # 대역폭 정보 조회
            account_detail = self.tron.get_account(wallet_address)

            # 대역폭 정보 추출
            total_bandwidth = account_detail.get("bandwidth", {}).get("net_limit", 0)
            used_bandwidth = account_detail.get("bandwidth", {}).get("net_used", 0)

            # 동결 정보 조회
            frozen_info = await self._get_frozen_info(account_detail)

            # DB 업데이트
            await self.db.execute(
                update(PartnerEnergyPool)
                .where(PartnerEnergyPool.id == energy_pool.id)
                .values(
                    total_energy=Decimal(str(total_energy)),
                    available_energy=Decimal(str(available_energy)),
                    used_energy=Decimal(str(used_energy)),
                    total_bandwidth=Decimal(str(total_bandwidth)),
                    available_bandwidth=Decimal(
                        str(max(0, total_bandwidth - used_bandwidth))
                    ),
                    frozen_for_energy=frozen_info["energy"],
                    frozen_for_bandwidth=frozen_info["bandwidth"],
                    frozen_trx_amount=frozen_info["energy"] + frozen_info["bandwidth"],
                    last_checked_at=datetime.utcnow(),
                )
            )

            # 상태 업데이트
            pool_id = safe_int_conversion(energy_pool.id)
            await self._update_energy_status(pool_id, available_energy, total_energy)

        except Exception as e:
            logger.error(f"Failed to update energy pool from blockchain: {e}")
            await self._update_with_mock_data(energy_pool)

    async def _update_with_mock_data(self, energy_pool: PartnerEnergyPool):
        """테스트용 목 데이터로 업데이트"""
        await self.db.execute(
            update(PartnerEnergyPool)
            .where(PartnerEnergyPool.id == energy_pool.id)
            .values(
                total_energy=Decimal("10000"),
                used_energy=Decimal("3000"),
                available_energy=Decimal("7000"),
                total_bandwidth=Decimal("5000"),
                available_bandwidth=Decimal("4000"),
                frozen_trx_amount=Decimal("100"),
                frozen_for_energy=Decimal("80"),
                frozen_for_bandwidth=Decimal("20"),
                last_checked_at=datetime.utcnow(),
            )
        )

    async def _update_energy_status(
        self, energy_pool_id: int, available_energy: int, total_energy: int
    ):
        """에너지 상태 업데이트"""
        if total_energy == 0:
            usage_percentage = 0
            status = EnergyStatus.SUFFICIENT
        else:
            usage_percentage = ((total_energy - available_energy) / total_energy) * 100

            if usage_percentage >= 90:  # critical_threshold
                status = EnergyStatus.CRITICAL
            elif usage_percentage >= 70:  # warning_threshold
                status = EnergyStatus.WARNING
            else:
                status = EnergyStatus.SUFFICIENT

        await self.db.execute(
            update(PartnerEnergyPool)
            .where(PartnerEnergyPool.id == energy_pool_id)
            .values(status=status)
        )

    async def _get_frozen_info(self, account_info: Dict) -> Dict[str, Decimal]:
        """TRX 동결 정보 파싱"""
        frozen_info = {"energy": Decimal("0"), "bandwidth": Decimal("0")}

        try:
            # 동결 정보 추출
            if "frozen" in account_info:
                for frozen in account_info["frozen"]:
                    frozen_balance = Decimal(str(frozen.get("frozen_balance", 0) / 1e6))
                    resource_type = frozen.get("resource", "BANDWIDTH")

                    if resource_type == "ENERGY":
                        frozen_info["energy"] = frozen_balance
                    else:  # BANDWIDTH
                        frozen_info["bandwidth"] = frozen_balance

            return frozen_info

        except Exception as e:
            logger.error(f"Failed to parse frozen info: {e}")
            return frozen_info

    def calculate_hours_remaining(
        self, energy_pool: PartnerEnergyPool
    ) -> Optional[int]:
        """잔여 시간 계산"""
        available = safe_decimal_to_float(energy_pool.available_energy)
        daily_avg = safe_decimal_to_float(energy_pool.daily_average_usage)

        if daily_avg > 0 and available > 0:
            hours_remaining = (available / daily_avg) * 24
            return int(hours_remaining)
        return None

    async def get_all_energy_pools(self) -> List[PartnerEnergyPool]:
        """모든 에너지 풀 조회"""
        result = await self.db.execute(
            select(PartnerEnergyPool).order_by(PartnerEnergyPool.partner_id)
        )
        return list(result.scalars().all())
