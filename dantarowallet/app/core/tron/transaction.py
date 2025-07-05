"""
TRON 트랜잭션 조회 및 관리 서비스.
트랜잭션 조회, 블록 스캔 등의 기능을 담당합니다.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.tron.constants import TronConstants
from app.core.tron.network import TronNetworkService

logger = logging.getLogger(__name__)


class TronTransactionService(TronNetworkService):
    """TRON 트랜잭션 서비스"""
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """트랜잭션 정보 조회"""
        try:
            self.ensure_connection()
            tx = self.client.get_transaction(tx_hash)
            return tx
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {e}")
            return None
    
    def get_block_number(self) -> int:
        """현재 블록 번호 조회"""
        try:
            self.ensure_connection()
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
            self.ensure_connection()
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
            self.ensure_connection()
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
