"""
통합 출금 서비스
모든 출금 관련 기능을 통합한 서비스 클래스입니다.
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority
from app.services.withdrawal.processing_service import WithdrawalProcessingService
from app.services.withdrawal.query_service import WithdrawalQueryService
from app.services.withdrawal.request_service import WithdrawalRequestService
from app.services.withdrawal.validation_service import WithdrawalValidationService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WithdrawalService:
    """통합 출금 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.request_service = WithdrawalRequestService(db)
        self.processing_service = WithdrawalProcessingService(db)
        self.query_service = WithdrawalQueryService(db)
        self.validation_service = WithdrawalValidationService(db)

    # 출금 요청 관련 메서드
    async def create_withdrawal_request(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal,
        asset: str = "USDT",
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Withdrawal:
        """출금 요청 생성"""
        return await self.request_service.create_withdrawal_request(
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            asset=asset,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def cancel_withdrawal(
        self, withdrawal_id: int, user_id: int
    ) -> Withdrawal:
        """출금 요청 취소"""
        return await self.request_service.cancel_withdrawal(
            withdrawal_id=withdrawal_id, user_id=user_id
        )

    # 출금 처리 관련 메서드
    async def review_withdrawal(
        self,
        withdrawal_id: int,
        admin_id: int,
        action: str,  # "approve" or "reject"
        admin_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> Withdrawal:
        """출금 검토 (관리자)"""
        return await self.processing_service.review_withdrawal(
            withdrawal_id=withdrawal_id,
            admin_id=admin_id,
            action=action,
            admin_notes=admin_notes,
            rejection_reason=rejection_reason,
        )

    async def mark_as_processing(
        self, withdrawal_id: int, admin_id: int
    ) -> Withdrawal:
        """처리 중으로 표시"""
        return await self.processing_service.mark_as_processing(
            withdrawal_id=withdrawal_id, admin_id=admin_id
        )

    async def complete_withdrawal(
        self,
        withdrawal_id: int,
        tx_hash: str,
        admin_id: int,
        tx_fee: Optional[Decimal] = None,
    ) -> Withdrawal:
        """출금 완료"""
        return await self.processing_service.complete_withdrawal(
            withdrawal_id=withdrawal_id,
            tx_hash=tx_hash,
            admin_id=admin_id,
            tx_fee=tx_fee,
        )

    async def get_withdrawal_processing_guide(
        self, withdrawal_id: int
    ) -> Dict[str, Any]:
        """출금 처리 가이드 생성"""
        return await self.processing_service.get_withdrawal_processing_guide(
            withdrawal_id=withdrawal_id
        )

    # 출금 조회 관련 메서드
    async def get_pending_withdrawals(
        self,
        status: Optional[WithdrawalStatus] = None,
        priority: Optional[WithdrawalPriority] = None,
    ) -> List[Withdrawal]:
        """대기 중인 출금 목록"""
        return await self.query_service.get_pending_withdrawals(
            status=status, priority=priority
        )

    async def get_user_withdrawals(
        self,
        user_id: int,
        status: Optional[WithdrawalStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Withdrawal], int]:
        """사용자 출금 목록"""
        return await self.query_service.get_user_withdrawals(
            user_id=user_id, status=status, limit=limit, offset=offset
        )

    # 검증 관련 메서드
    async def validate_withdrawal_request(
        self, user_id: int, to_address: str, amount: Decimal, asset: str = "USDT"
    ) -> None:
        """출금 요청 검증"""
        await self.validation_service.validate_withdrawal_request(
            user_id=user_id, to_address=to_address, amount=amount, asset=asset
        )
