"""
입금 처리 서비스
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List

from app.models.balance import Balance
from app.models.deposit import Deposit
from app.services.balance_service import BalanceService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DepositProcessingService:
    """입금 처리 서비스"""

    @staticmethod
    async def process_deposit(
        db: AsyncSession,
        user_id: int,
        asset: str,
        amount: Decimal,
        tx_data: Dict[str, Any],
    ) -> Deposit:
        """
        새로운 입금 처리

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            asset: 자산 유형
            amount: 입금 금액
            tx_data: 트랜잭션 데이터

        Returns:
            처리된 입금 내역
        """
        # 입금 레코드 생성
        deposit = Deposit(
            user_id=user_id,
            asset=asset,
            amount=amount,
            transaction_hash=tx_data.get("txID"),
            block_number=tx_data.get("blockNumber"),
            status="pending",
            raw_data=tx_data,
        )
        db.add(deposit)
        await db.flush()

        try:
            # 잔액 업데이트
            balance_service = BalanceService()
            await balance_service.add_balance(
                db,
                user_id=user_id,
                asset=asset,
                amount=amount,
                reference_id=deposit.id,
                reference_type="deposit",
            )

            # 입금 상태 업데이트
            deposit.status = "completed"
            await db.flush()

            logger.info(
                f"입금 처리 완료: 사용자 {user_id}, {amount} {asset}, 트랜잭션 {tx_data.get('txID')}"
            )

        except Exception as e:
            logger.error(f"입금 처리 중 오류 발생: {e}")
            deposit.status = "failed"
            deposit.error_message = str(e)
            await db.flush()
            raise

        return deposit

    @staticmethod
    async def confirm_pending_deposits(
        db: AsyncSession, deposits: List[Deposit], confirmed_tx_hashes: List[str]
    ) -> int:
        """
        대기 중인 입금 확인 처리

        Args:
            db: 데이터베이스 세션
            deposits: 대기 중인 입금 목록
            confirmed_tx_hashes: 확인된 트랜잭션 해시 목록

        Returns:
            처리된 입금 수
        """
        processed_count = 0
        balance_service = BalanceService()

        for deposit in deposits:
            if deposit.transaction_hash in confirmed_tx_hashes:
                try:
                    # 잔액 업데이트
                    await balance_service.add_balance(
                        db,
                        user_id=deposit.user_id,
                        asset=deposit.asset,
                        amount=deposit.amount,
                        reference_id=deposit.id,
                        reference_type="deposit",
                    )

                    # 입금 상태 업데이트
                    deposit.status = "completed"
                    await db.flush()

                    processed_count += 1
                    logger.info(
                        f"대기 입금 처리 완료: ID {deposit.id}, {deposit.amount} {deposit.asset}"
                    )

                except Exception as e:
                    logger.error(f"대기 입금 처리 중 오류 발생: ID {deposit.id}, 오류: {e}")
                    deposit.status = "failed"
                    deposit.error_message = str(e)
                    await db.flush()

        return processed_count
