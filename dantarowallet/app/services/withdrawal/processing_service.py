"""
출금 처리 서비스
출금 요청 처리, 승인, 거부, 완료 등의 기능을 제공합니다.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import Transaction, TransactionStatus
from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.services.withdrawal.base_service import BaseWithdrawalService

logger = logging.getLogger(__name__)


class WithdrawalProcessingService(BaseWithdrawalService):
    """출금 처리 서비스"""

    async def review_withdrawal(
        self,
        withdrawal_id: int,
        admin_id: int,
        action: str,  # "approve" or "reject"
        admin_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> Withdrawal:
        """출금 검토 (관리자)"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()

        if not withdrawal:
            raise NotFoundError("출금 요청을 찾을 수 없습니다")

        # 상태 변경
        withdrawal.reviewed_at = datetime.utcnow()
        withdrawal.reviewed_by = admin_id

        if admin_notes:
            withdrawal.admin_notes = admin_notes

        if action == "approve":
            if withdrawal.status != WithdrawalStatus.PENDING.value:
                raise ValidationError(
                    f"{withdrawal.status} 상태의 출금은 승인할 수 없습니다"
                )

            withdrawal.status = WithdrawalStatus.APPROVED.value
            withdrawal.approved_at = datetime.utcnow()
            withdrawal.approved_by = admin_id

            logger.info(f"출금 승인: ID {withdrawal_id}, 관리자 {admin_id}")

        elif action == "reject":
            if not rejection_reason:
                raise ValidationError("거부 사유는 필수입니다")

            withdrawal.status = WithdrawalStatus.REJECTED.value
            withdrawal.rejection_reason = rejection_reason

            # 잔고 잠금 해제
            asset_str = (
                str(withdrawal.asset)
                if hasattr(withdrawal.asset, "value")
                else withdrawal.asset
            )
            total_amount = Decimal(str(withdrawal.total_amount))

            await self.balance_service.unlock_amount(
                user_id=withdrawal.user_id, asset=asset_str, amount=total_amount
            )

            # 트랜잭션 상태 업데이트
            tx_query = select(Transaction).filter(
                Transaction.reference_id == f"WD-{withdrawal.id}"
            )
            tx_result = await self.db.execute(tx_query)
            transaction = tx_result.scalar_one_or_none()
            if transaction:
                transaction.status = TransactionStatus.FAILED.value

            logger.info(
                f"출금 거부: ID {withdrawal_id}, 관리자 {admin_id}, 사유: {rejection_reason}"
            )

        return withdrawal

    async def get_withdrawal_processing_guide(
        self, withdrawal_id: int
    ) -> Dict[str, Any]:
        """출금 처리 가이드 생성 (수동 처리용)"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()

        if not withdrawal:
            raise NotFoundError("출금 요청을 찾을 수 없습니다")

        if not withdrawal.can_process():
            raise ValidationError(
                f"{withdrawal.status} 상태의 출금은 처리할 수 없습니다"
            )

        # 처리 가이드 생성
        guide = {
            "withdrawal_id": withdrawal.id,
            "status": withdrawal.status,
            "amount": str(withdrawal.amount),
            "fee": str(withdrawal.fee),
            "to_address": withdrawal.to_address,
            "asset": withdrawal.asset,
            "instructions": [
                "1. TRON 지갑 애플리케이션을 엽니다",
                f"2. {withdrawal.asset} 토큰을 선택합니다",
                "3. Send/Transfer 버튼을 클릭합니다",
                f"4. 수신 주소를 입력합니다: {withdrawal.to_address}",
                f"5. 금액을 입력합니다: {withdrawal.amount} {withdrawal.asset}",
                "6. 트랜잭션 세부 정보를 주의 깊게 검토합니다",
                "7. 트랜잭션을 확인하고 전송합니다",
                "8. 트랜잭션 확인을 기다립니다",
                "9. 트랜잭션 해시를 복사합니다",
                "10. 트랜잭션 해시로 출금 상태를 업데이트합니다",
            ],
            "warnings": [
                "⚠️ 수신 주소를 다시 한 번 확인하세요",
                f"⚠️ 회사 지갑에 충분한 {withdrawal.asset} 잔고가 있는지 확인하세요",
                "⚠️ 가스비용으로 충분한 TRX가 있는지 확인하세요",
                "⚠️ 절대 개인키를 공유하지 마세요",
            ],
            "checklist": [
                "□ 수신 주소 확인됨",
                "□ 금액 확인됨",
                "□ 회사 지갑 잔고 충분함",
                "□ 회사 지갑 TRX(가스비) 충분함",
                "□ 의심스러운 활동 없음",
            ],
        }

        return guide

    async def mark_as_processing(self, withdrawal_id: int, admin_id: int) -> Withdrawal:
        """처리 중으로 표시"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()

        if not withdrawal:
            raise NotFoundError("출금 요청을 찾을 수 없습니다")

        if withdrawal.status != WithdrawalStatus.APPROVED.value:
            raise ValidationError("승인된 출금만 처리할 수 있습니다")

        withdrawal.status = WithdrawalStatus.PROCESSING.value
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.processed_by = admin_id

        await self.db.flush()

        return withdrawal

    async def complete_withdrawal(
        self,
        withdrawal_id: int,
        tx_hash: str,
        admin_id: int,
        tx_fee: Optional[Decimal] = None,
    ) -> Withdrawal:
        """출금 완료 처리"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()

        if not withdrawal:
            raise NotFoundError("출금 요청을 찾을 수 없습니다")

        if withdrawal.status != WithdrawalStatus.PROCESSING.value:
            raise ValidationError(
                f"{withdrawal.status} 상태의 출금은 완료처리할 수 없습니다"
            )

        # 출금 완료
        withdrawal.status = WithdrawalStatus.COMPLETED.value
        withdrawal.completed_at = datetime.utcnow()
        withdrawal.tx_hash = tx_hash
        if tx_fee:
            withdrawal.tx_fee = tx_fee

        # 잔고 차감 (잠금에서 실제 차감으로)
        balance = await self.balance_service.get_balance(
            withdrawal.user_id, withdrawal.asset
        )
        balance.amount -= withdrawal.total_amount
        balance.locked_amount -= withdrawal.total_amount

        # 트랜잭션 완료
        tx_query = select(Transaction).filter(
            Transaction.reference_id == f"WD-{withdrawal.id}"
        )
        tx_result = await self.db.execute(tx_query)
        transaction = tx_result.scalar_one_or_none()
        if transaction:
            transaction.status = TransactionStatus.COMPLETED.value
            transaction.tx_hash = tx_hash

        logger.info(f"출금 완료: ID {withdrawal_id}, TX {tx_hash}")

        return withdrawal
