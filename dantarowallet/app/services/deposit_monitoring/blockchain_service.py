"""
입금 모니터링 서비스 - 블록체인 트랜잭션 조회
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.tron import TronService

logger = logging.getLogger(__name__)


class DepositBlockchainService:
    """블록체인 트랜잭션 조회 서비스"""

    def __init__(self):
        self.tron = TronService()

    async def get_latest_block_number(self) -> int:
        """
        최신 블록 번호 조회

        Returns:
            최신 블록 번호
        """
        try:
            block_info = await self.tron.get_latest_block()
            return (
                block_info.get("block_header", {}).get("raw_data", {}).get("number", 0)
            )
        except Exception as e:
            logger.error(f"최신 블록 조회 실패: {e}")
            return 0

    async def get_transactions_for_address(
        self,
        address: str,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        주소에 대한 트랜잭션 조회

        Args:
            address: 지갑 주소
            start_block: 시작 블록 번호
            end_block: 종료 블록 번호

        Returns:
            트랜잭션 목록
        """
        try:
            transactions = await self.tron.get_transactions_for_address(
                address, start_block=start_block, end_block=end_block
            )

            # 입금 트랜잭션만 필터링 (to_address가 지정된 주소인 경우)
            incoming_txs = [tx for tx in transactions if tx.get("to") == address]

            return incoming_txs
        except Exception as e:
            logger.error(f"주소 {address}에 대한 트랜잭션 조회 실패: {e}")
            return []

    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        트랜잭션 해시로 트랜잭션 조회

        Args:
            tx_hash: 트랜잭션 해시

        Returns:
            트랜잭션 정보
        """
        try:
            return await self.tron.get_transaction_by_hash(tx_hash)
        except Exception as e:
            logger.error(f"트랜잭션 {tx_hash} 조회 실패: {e}")
            return None
