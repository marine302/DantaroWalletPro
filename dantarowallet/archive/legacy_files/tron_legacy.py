"""
TRON 블록체인 관련 유틸리티.
지갑 생성, 잔고 조회, 트랜잭션 조회 등의 기능을 제공합니다.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from tronpy import Tron
from tronpy.keys import PrivateKey

logger = logging.getLogger(__name__)


class TronService:
    """TRON 블록체인 서비스"""

    def __init__(self):
        # 네트워크 설정 (테스트넷: nile, 메인넷: mainnet)
        if settings.TRON_NETWORK == "nile":
            self.client = Tron(network="nile")
        else:
            self.client = Tron()

        logger.info(f"TronService initialized with network: {settings.TRON_NETWORK}")

    def generate_wallet(self) -> Dict[str, str]:
        """새 지갑 생성"""
        # 프라이빗 키 생성
        private_key = PrivateKey.random()

        # 주소 생성
        address = private_key.public_key.to_base58check_address()
        hex_address = private_key.public_key.to_hex_address()

        wallet_info = {
            "address": address,
            "hex_address": hex_address,
            "private_key": private_key.hex(),
            "public_key": private_key.public_key.hex(),
        }

        logger.info(f"New wallet generated: {address}")
        return wallet_info

    async def get_balance(self, address: str, token: str = "USDT") -> Dict[str, Any]:
        """지갑 잔고 조회"""
        try:
            if token == "TRX":
                # TRX 잔고
                balance = self.client.get_account_balance(address)
                return {"token": "TRX", "balance": balance, "decimals": 6}
            else:
                # TRC20 토큰 잔고 (USDT)
                # 테스트넷 USDT 컨트랙트 주소
                if settings.TRON_NETWORK == "nile":
                    contract_address = (
                        "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"  # Nile testnet USDT
                    )
                else:
                    contract_address = (
                        "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Mainnet USDT
                    )

                contract = self.client.get_contract(contract_address)
                balance = contract.functions.balanceOf(address)
                decimals = contract.functions.decimals()

                return {
                    "token": token,
                    "balance": balance,
                    "decimals": decimals,
                    "formatted": balance / (10**decimals),
                }
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return {"token": token, "balance": 0, "decimals": 6, "error": str(e)}

    async def validate_address(self, address: str) -> bool:
        """주소 유효성 검증"""
        try:
            # TRON 주소 형식 검증
            if not address.startswith("T") or len(address) != 34:
                return False

            # Base58 디코딩 시도
            from base58 import b58decode_check

            b58decode_check(address)
            return True
        except Exception:
            return False

    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """트랜잭션 정보 조회"""
        try:
            tx = self.client.get_transaction(tx_hash)
            return tx
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {e}")
            return None

    def get_block_number(self) -> int:
        """현재 블록 번호 조회"""
        try:
            block = self.client.get_latest_block()
            return block["block_header"]["raw_data"]["number"]
        except Exception as e:
            logger.error(f"Error getting block number: {e}")
            return 0

    def get_trx_transactions(
        self, address: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """TRX 트랜잭션 조회"""
        try:
            transactions = []

            # TronGrid API를 사용하여 트랜잭션 조회
            for block_num in range(
                start_block, min(end_block + 1, start_block + 50)
            ):  # 한번에 최대 50블록
                try:
                    block = self.client.get_block(block_num)
                    if not block or "transactions" not in block:
                        continue

                    for tx in block["transactions"]:
                        if "raw_data" not in tx or "contract" not in tx["raw_data"]:
                            continue

                        for contract in tx["raw_data"]["contract"]:
                            if contract["type"] == "TransferContract":
                                param = contract["parameter"]["value"]
                                if param.get("to_address") and param.get("amount"):
                                    # 주소 변환 (hex to base58)
                                    to_addr = self.client.to_base58check_address(
                                        param["to_address"]
                                    )
                                    from_addr = self.client.to_base58check_address(
                                        param["owner_address"]
                                    )

                                    if to_addr == address:  # 수신 트랜잭션만
                                        transactions.append(
                                            {
                                                "hash": tx["txID"],
                                                "from": from_addr,
                                                "to": to_addr,
                                                "value": param["amount"],
                                                "block_number": block_num,
                                                "timestamp": tx["raw_data"][
                                                    "timestamp"
                                                ],
                                                "transaction_index": 0,
                                            }
                                        )
                except Exception as e:
                    logger.warning(f"블록 {block_num} 조회 실패: {e}")
                    continue

            return transactions

        except Exception as e:
            logger.error(f"TRX 트랜잭션 조회 실패: {e}")
            return []

    def get_trc20_transactions(
        self, address: str, contract_address: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """TRC20 토큰 트랜잭션 조회"""
        try:
            transactions = []

            # TRC20 트랜잭션 조회 (간단한 구현)
            for block_num in range(start_block, min(end_block + 1, start_block + 50)):
                try:
                    block = self.client.get_block(block_num)
                    if not block or "transactions" not in block:
                        continue

                    for tx in block["transactions"]:
                        if "raw_data" not in tx or "contract" not in tx["raw_data"]:
                            continue

                        for contract in tx["raw_data"]["contract"]:
                            if contract["type"] == "TriggerSmartContract":
                                param = contract["parameter"]["value"]
                                if param.get("contract_address") == contract_address:
                                    # TRC20 Transfer 이벤트 파싱 (간단한 구현)
                                    data = param.get("data", "")
                                    if (
                                        len(data) >= 136
                                    ):  # transfer(address,uint256) 호출 데이터
                                        try:
                                            # 수신 주소 추출 (24바이트 오프셋 + 20바이트 주소)
                                            to_hex = "41" + data[32:72]
                                            to_addr = (
                                                self.client.to_base58check_address(
                                                    to_hex
                                                )
                                            )

                                            # 금액 추출 (64바이트)
                                            amount_hex = data[72:136]
                                            amount = int(amount_hex, 16)

                                            if to_addr == address and amount > 0:
                                                from_addr = (
                                                    self.client.to_base58check_address(
                                                        param["owner_address"]
                                                    )
                                                )

                                                transactions.append(
                                                    {
                                                        "hash": tx["txID"],
                                                        "from": from_addr,
                                                        "to": to_addr,
                                                        "value": amount,
                                                        "block_number": block_num,
                                                        "timestamp": tx["raw_data"][
                                                            "timestamp"
                                                        ],
                                                        "transaction_index": 0,
                                                    }
                                                )
                                        except:
                                            continue
                except Exception as e:
                    logger.warning(f"블록 {block_num} TRC20 조회 실패: {e}")
                    continue

            return transactions

        except Exception as e:
            logger.error(f"TRC20 트랜잭션 조회 실패: {e}")
            return []

    async def get_account_resources(self, address: str) -> Dict[str, Any]:
        """계정의 에너지 및 대역폭 정보 조회"""
        try:
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

    async def get_energy_info(self, address: Optional[str] = None) -> Dict[str, Any]:
        """계정의 에너지 정보 조회"""
        try:
            if not address:
                # 기본 주소 또는 시스템 주소 사용
                address = getattr(settings, 'SYSTEM_TRON_ADDRESS', 'TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy')
            
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
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 사용 가능한 에너지 계산
            energy_info["available_energy"] = max(0, energy_info["energy_limit"] - energy_info["energy_used"])
            energy_info["available_bandwidth"] = max(0, energy_info["net_limit"] - energy_info["net_used"])
            
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
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_energy_price(self) -> Dict[str, Any]:
        """현재 에너지 가격 정보 조회"""
        try:
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
                "energy_fee_trx": energy_fee / 1_000_000 if energy_fee > 0 else 0,  # TRX 단위
                "bandwidth_price": 1000,  # 고정값 (1000 sun)
                "timestamp": datetime.utcnow().isoformat(),
                "source": "tron_network"
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
                "error": str(e)
            }

    async def estimate_transaction_energy(self, contract_address: str, function_selector: str, 
                                       parameter: str = "", caller_address: str = None) -> Dict[str, Any]:
        """트랜잭션에 필요한 에너지 추정"""
        try:
            if not caller_address:
                caller_address = getattr(settings, 'SYSTEM_TRON_ADDRESS', 'TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy')
            
            # 트랜잭션 에너지 추정 (실제 TRON API 호출)
            result = self.client.trigger_constant_contract(
                owner_address=caller_address,
                contract_address=contract_address,
                function_selector=function_selector,
                parameter=parameter
            )
            
            energy_estimate = {
                "estimated_energy": result.get("energy_used", 0),
                "estimated_bandwidth": result.get("net_used", 0),
                "success": result.get("result", {}).get("result", False),
                "contract_address": contract_address,
                "function_selector": function_selector,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Energy estimation completed for contract {contract_address}")
            return energy_estimate
            
        except Exception as e:
            logger.error(f"Failed to estimate energy for contract {contract_address}: {str(e)}")
            return {
                "estimated_energy": 15000,  # 기본 추정값
                "estimated_bandwidth": 345,  # 기본 추정값
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_network_stats(self) -> Dict[str, Any]:
        """TRON 네트워크 전체 통계 정보"""
        try:
            # 노드 정보
            node_info = self.client.get_node_info()
            
            # 체인 파라미터
            chain_parameters = self.client.get_chain_parameters()
            
            # 최신 블록 정보
            latest_block = self.client.get_latest_block()
            
            network_stats = {
                "block_height": latest_block.get("block_header", {}).get("raw_data", {}).get("number", 0),
                "block_timestamp": latest_block.get("block_header", {}).get("raw_data", {}).get("timestamp", 0),
                "witness_count": len(latest_block.get("block_header", {}).get("raw_data", {}).get("witness_signature", [])),
                "node_version": node_info.get("configNodeInfo", {}).get("codeVersion", "unknown"),
                "total_transaction": node_info.get("machineInfo", {}).get("totalTransactionCount", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "network": settings.TRON_NETWORK
            }
            
            # 에너지 관련 체인 파라미터 추출
            for param in chain_parameters:
                key = param.get("key", "")
                if "Energy" in key or "energy" in key:
                    network_stats[f"param_{key.lower()}"] = param.get("value", 0)
            
            logger.info(f"Network stats retrieved for block #{network_stats['block_height']}")
            return network_stats
            
        except Exception as e:
            logger.error(f"Failed to get network stats: {str(e)}")
            return {
                "block_height": 0,
                "block_timestamp": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "network": settings.TRON_NETWORK
            }
