"""
입금 모니터링 메인 서비스
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.deposit import Deposit
from app.models.wallet import Wallet
from sqlalchemy.ext.asyncio import AsyncSession

from .base_monitor import BaseMonitorService
from .blockchain_service import DepositBlockchainService
from .processing_service import DepositProcessingService
from .query_service import DepositQueryService

logger = logging.getLogger(__name__)


class DepositMonitoringService(BaseMonitorService):
    """입금 모니터링 메인 서비스"""

    def __init__(self):
        super().__init__()
        self.query_service = DepositQueryService()
        self.processing_service = DepositProcessingService()
        self.blockchain_service = DepositBlockchainService()

    async def _monitor_deposits(self):
        """입금 모니터링 수행"""
        try:
            async with AsyncSessionLocal() as db:
                # 최신 블록 번호 조회
                current_block = await self.blockchain_service.get_latest_block_number()
                if not current_block:
                    logger.error("최신 블록 번호를 조회할 수 없습니다")
                    return

                # 첫 실행 시 마지막 확인 블록 설정
                if self.last_checked_block is None:
                    self.last_checked_block = max(
                        1, current_block - settings.BLOCKS_TO_CHECK_ON_START
                    )

                logger.info(f"블록 확인 중: {self.last_checked_block} → {current_block}")

                # 1. 대기 중인 입금 트랜잭션 처리
                await self._process_pending_deposits(db)

                # 2. 새로운 입금 트랜잭션 확인
                await self._check_new_deposits(
                    db, self.last_checked_block, current_block
                )

                # 처리 완료된 블록 업데이트
                self.last_checked_block = current_block

        except Exception as e:
            logger.error(f"입금 모니터링 중 오류 발생: {e}")

    async def _process_pending_deposits(self, db: AsyncSession):
        """대기 중인 입금 트랜잭션 처리"""
        # 최근 24시간 내의 대기 중인 입금 조회
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        pending_deposits = await self.query_service.get_pending_deposits(
            db, cutoff_time
        )

        if not pending_deposits:
            return

        logger.info(f"{len(pending_deposits)}개의 대기 중인 입금 트랜잭션을 처리합니다")

        # 각 입금에 대해 블록체인에서 상태 확인
        confirmed_tx_hashes = []

        for deposit in pending_deposits:
            tx_info = await self.blockchain_service.get_transaction_by_hash(
                deposit.transaction_hash
            )
            if tx_info and tx_info.get("confirmed", False):
                confirmed_tx_hashes.append(deposit.transaction_hash)

        # 확인된 트랜잭션 처리
        if confirmed_tx_hashes:
            processed = await self.processing_service.confirm_pending_deposits(
                db, pending_deposits, confirmed_tx_hashes
            )
            logger.info(f"{processed}개의 대기 중인 입금 트랜잭션을 완료 처리했습니다")
            await db.commit()

    async def _check_new_deposits(
        self, db: AsyncSession, start_block: int, end_block: int
    ):
        """새로운 입금 트랜잭션 확인"""
        # 활성화된 지갑 조회
        active_wallets = await self.query_service.get_active_wallets(db)

        if not active_wallets:
            logger.info("활성화된 지갑이 없습니다")
            return

        logger.info(f"{len(active_wallets)}개의 활성화된 지갑에 대해 새로운 입금을 확인합니다")

        for wallet in active_wallets:
            # 각 지갑 주소에 대한 새로운 트랜잭션 조회
            transactions = await self.blockchain_service.get_transactions_for_address(
                wallet.address, start_block=start_block, end_block=end_block
            )

            if not transactions:
                continue

            logger.info(f"지갑 {wallet.address}에 {len(transactions)}개의 새로운 트랜잭션이 있습니다")

            # 각 트랜잭션 처리
            for tx in transactions:
                # 이미 처리된 트랜잭션인지 확인
                existing_deposits = await self.query_service.get_deposits_by_tx_hash(
                    db, tx.get("txID")
                )
                if existing_deposits:
                    logger.debug(f"트랜잭션 {tx.get('txID')}는 이미 처리되었습니다")
                    continue

                # 트랜잭션이 유효한지 확인
                if tx.get("confirmed", False) and tx.get("to") == wallet.address:
                    amount = tx.get("value", 0)
                    asset = tx.get("token", "TRX")

                    logger.info(f"새로운 입금 발견: {amount} {asset}, 트랜잭션 {tx.get('txID')}")

                    # 입금 처리
                    try:
                        await self.processing_service.process_deposit(
                            db,
                            user_id=wallet.user_id,
                            asset=asset,
                            amount=amount,
                            tx_data=tx,
                        )
                        await db.commit()
                        logger.info(
                            f"입금 처리 완료: {amount} {asset}, 트랜잭션 {tx.get('txID')}"
                        )
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"입금 처리 중 오류 발생: {e}")
                        continue
