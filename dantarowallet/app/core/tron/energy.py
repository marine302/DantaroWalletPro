"""
TRON 에너지 및 리소스 관리 서비스.
에너지, 대역폭, 계정 리소스 관리를 담당합니다.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.tron.network import TronNetworkService

logger = logging.getLogger(__name__)


class TronEnergyService(TronNetworkService):
    """TRON 에너지 및 리소스 관리 서비스"""

    async def get_account_resources(self, address: str) -> Dict[str, Any]:
        """계정의 에너지 및 대역폭 정보 조회"""
        try:
            self.ensure_connection()

            # 계정 정보 조회
            account_info = self.client.get_account(address)

            # 에너지 정보 계산
            energy_limit = account_info.get("account_resource", {}).get(
                "energy_limit", 0
            )
            energy_used = account_info.get("account_resource", {}).get("energy_used", 0)
            available_energy = energy_limit - energy_used

            # 대역폭 정보 계산
            net_limit = account_info.get("net_limit", 0)
            net_used = account_info.get("net_used", 0)
            available_bandwidth = net_limit - net_used

            # Frozen 정보
            frozen_v2 = account_info.get("frozenV2", [])
            frozen_for_energy = 0
            frozen_for_bandwidth = 0

            for frozen in frozen_v2:
                if frozen.get("type") == "ENERGY":
                    frozen_for_energy += frozen.get("amount", 0)
                elif frozen.get("type") == "BANDWIDTH":
                    frozen_for_bandwidth += frozen.get("amount", 0)

            # 총 TRX 잔고
            balance = self.client.get_account_balance(address)

            return {
                "address": address,
                "trx_balance": balance / 1_000_000,  # SUN to TRX
                "energy": {
                    "limit": energy_limit,
                    "used": energy_used,
                    "available": available_energy,
                    "frozen_trx": frozen_for_energy / 1_000_000,
                },
                "bandwidth": {
                    "limit": net_limit,
                    "used": net_used,
                    "available": available_bandwidth,
                    "frozen_trx": frozen_for_bandwidth / 1_000_000,
                },
                "total_frozen_trx": (frozen_for_energy + frozen_for_bandwidth)
                / 1_000_000,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting account resources for {address}: {e}")
            return {
                "address": address,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_energy_price_info(self) -> Dict[str, Any]:
        """현재 에너지 가격 정보 조회"""
        try:
            self.ensure_connection()

            # ChainParameters에서 에너지 관련 정보 조회
            chain_params = self.client.get_chain_parameters()

            # 기본 값들 (실제 네트워크에서 동적으로 계산됨)
            energy_fee = 420  # SUN per Energy (기본값)
            bandwidth_fee = 1000  # SUN per Bandwidth (기본값)

            # ChainParameters에서 실제 값 찾기
            for param in chain_params:
                if param.get("key") == "getEnergyFee":
                    energy_fee = param.get("value", energy_fee)
                elif param.get("key") == "getTransactionFee":
                    bandwidth_fee = param.get("value", bandwidth_fee)

            # TRX 당 획득 가능한 에너지/대역폭 계산
            trx_in_sun = 1_000_000
            energy_per_trx = trx_in_sun // energy_fee if energy_fee > 0 else 0
            bandwidth_per_trx = trx_in_sun // bandwidth_fee if bandwidth_fee > 0 else 0

            return {
                "energy_fee_sun": energy_fee,
                "bandwidth_fee_sun": bandwidth_fee,
                "energy_per_trx": energy_per_trx,
                "bandwidth_per_trx": bandwidth_per_trx,
                "trx_per_energy": energy_fee / trx_in_sun,
                "trx_per_bandwidth": bandwidth_fee / trx_in_sun,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting energy price info: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def estimate_transaction_cost(
        self, transaction_type: str = "USDT_TRANSFER"
    ) -> Dict[str, Any]:
        """트랜잭션 타입별 예상 비용 계산"""
        try:
            # 트랜잭션 타입별 평균 에너지 사용량 (실제 네트워크 데이터 기반)
            energy_costs = {
                "USDT_TRANSFER": 13000,  # USDT 전송
                "TRX_TRANSFER": 0,  # TRX 전송 (에너지 사용 안함)
                "CONTRACT_CALL": 10000,  # 일반 컨트랙트 호출
                "CREATE_CONTRACT": 50000,  # 컨트랙트 생성
                "VOTE": 5000,  # 투표
                "FREEZE": 1000,  # Freeze/Unfreeze
                "UNFREEZE": 1000,
            }

            bandwidth_costs = {
                "USDT_TRANSFER": 268,  # 모든 트랜잭션 공통
                "TRX_TRANSFER": 268,
                "CONTRACT_CALL": 268,
                "CREATE_CONTRACT": 500,  # 컨트랙트 생성은 더 큼
                "VOTE": 268,
                "FREEZE": 268,
                "UNFREEZE": 268,
            }

            estimated_energy = energy_costs.get(transaction_type, 0)
            estimated_bandwidth = bandwidth_costs.get(transaction_type, 268)

            # 가격 정보 조회
            price_info = await self.get_energy_price_info()

            if "error" not in price_info:
                energy_cost_trx = estimated_energy * price_info.get("trx_per_energy", 0)
                bandwidth_cost_trx = estimated_bandwidth * price_info.get(
                    "trx_per_bandwidth", 0
                )
                total_cost_trx = energy_cost_trx + bandwidth_cost_trx
            else:
                energy_cost_trx = 0
                bandwidth_cost_trx = 0
                total_cost_trx = 0

            return {
                "transaction_type": transaction_type,
                "estimated_energy": estimated_energy,
                "estimated_bandwidth": estimated_bandwidth,
                "energy_cost_trx": energy_cost_trx,
                "bandwidth_cost_trx": bandwidth_cost_trx,
                "total_cost_trx": total_cost_trx,
                "total_cost_sun": total_cost_trx * 1_000_000,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error estimating transaction cost: {e}")
            return {
                "transaction_type": transaction_type,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_energy_info(self, address: str = "") -> Dict[str, Any]:
        """계정의 에너지 정보 조회"""
        try:
            if not address:
                # 기본 주소 또는 시스템 주소 사용
                address = getattr(
                    settings,
                    "SYSTEM_TRON_ADDRESS",
                    "TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy",
                )

            self.ensure_connection()

            account_info = self.client.get_account(address)

            # 계정 리소스 정보 조회
            account_resources = self.client.get_account_resource(address)

            energy_info = {
                "address": address,
                "energy_limit": account_resources.get("EnergyLimit", 0),
                "energy_used": account_resources.get("EnergyUsed", 0),
                "total_energy_limit": account_resources.get("TotalEnergyLimit", 0),
                "total_energy_weight": account_resources.get("TotalEnergyWeight", 0),
                "net_limit": account_resources.get("NetLimit", 0),
                "net_used": account_resources.get("NetUsed", 0),
                "free_net_limit": account_resources.get("freeNetLimit", 0),
                "free_net_used": account_resources.get("freeNetUsed", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 사용 가능한 에너지 계산
            energy_info["available_energy"] = max(
                0, energy_info["energy_limit"] - energy_info["energy_used"]
            )
            energy_info["available_bandwidth"] = max(
                0, energy_info["net_limit"] - energy_info["net_used"]
            )

            logger.info(f"Energy info retrieved for address: {address}")
            return energy_info

        except Exception as e:
            logger.error(f"Failed to get energy info for {address}: {str(e)}")
            return {
                "address": address or "unknown",
                "energy_limit": 0,
                "energy_used": 0,
                "available_energy": 0,
                "available_bandwidth": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_energy_price(self) -> Dict[str, Any]:
        """현재 에너지 가격 정보 조회"""
        try:
            self.ensure_connection()

            # 체인 파라미터에서 에너지 관련 정보 조회
            chain_parameters = self.client.get_chain_parameters()

            # 에너지 가격 관련 파라미터 추출
            energy_fee = 0
            for param in chain_parameters:
                if param.get("key") == "getEnergyFee":
                    energy_fee = param.get("value", 0)
                    break

            # 추가 에너지 관련 정보
            price_info = {
                "energy_fee": energy_fee,  # sun 단위
                "energy_fee_trx": (
                    energy_fee / 1_000_000 if energy_fee > 0 else 0
                ),  # TRX 단위
                "bandwidth_price": 1000,  # 고정값 (1000 sun)
                "timestamp": datetime.utcnow().isoformat(),
                "source": "tron_network",
            }

            logger.info(f"Energy price retrieved: {energy_fee} sun")
            return price_info

        except Exception as e:
            logger.error(f"Failed to get energy price: {str(e)}")
            return {
                "energy_fee": 420,  # 기본값 (sun)
                "energy_fee_trx": 0.00042,  # 기본값 (TRX)
                "bandwidth_price": 1000,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fallback",
                "error": str(e),
            }

    async def estimate_transaction_energy(
        self,
        contract_address: str,
        function_selector: str,
        parameter: str = "",
        caller_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """트랜잭션에 필요한 에너지 추정"""
        try:
            # caller_address 확인 및 기본값 설정
            if caller_address is None:
                caller_address = getattr(
                    settings,
                    "SYSTEM_TRON_ADDRESS",
                    "TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy",
                )

            # 타입 확인 - 이 지점에서 caller_address는 항상 str
            assert isinstance(caller_address, str), "caller_address must be string"

            self.ensure_connection()

            # 트랜잭션 에너지 추정 (실제 TRON API 호출)
            result = self.client.trigger_constant_contract(
                owner_address=caller_address,
                contract_address=contract_address,
                function_selector=function_selector,
                parameter=parameter,
            )

            energy_estimate = {
                "estimated_energy": result.get("energy_used", 0),
                "estimated_bandwidth": result.get("net_used", 0),
                "success": result.get("result", {}).get("result", False),
                "contract_address": contract_address,
                "function_selector": function_selector,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Energy estimation completed for contract {contract_address}")
            return energy_estimate

        except Exception as e:
            logger.error(
                f"Failed to estimate energy for contract {contract_address}: {str(e)}"
            )
            return {
                "estimated_energy": 15000,  # 기본 추정값
                "estimated_bandwidth": 345,  # 기본 추정값
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
