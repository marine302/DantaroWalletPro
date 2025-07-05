"""
출금 관리 서비스.
출금 요청 처리, 검토, 승인, 완료 등의 비즈니스 로직을 담당합니다.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import InsufficientBalanceError, NotFoundError, ValidationError
from app.models.balance import Balance
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.user import User
from app.models.withdrawal import Withdrawal, WithdrawalPriority, WithdrawalStatus
from app.services.balance_service import BalanceService
from app.services.fee_service import FeeService
from app.services.wallet_service import WalletService
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class WithdrawalService:
    """출금 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.balance_service = BalanceService(db)
        self.wallet_service = WalletService(db)
        self.fee_service = FeeService(db)

        # 출금 정책
        self.min_withdrawal = Decimal("10.0")  # 최소 출금액
        self.max_withdrawal_per_tx = Decimal("10000.0")  # 1회 최대
        self.max_withdrawal_per_day = Decimal("20000.0")  # 1일 최대

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

        # 1. 금액 검증
        if amount < self.min_withdrawal:
            raise ValidationError(f"최소 출금 금액은 {self.min_withdrawal} {asset}입니다")

        if amount > self.max_withdrawal_per_tx:
            raise ValidationError(
                f"1회 최대 출금 금액은 {self.max_withdrawal_per_tx} {asset}입니다"
            )

        # 2. 주소 검증
        is_valid = await self.wallet_service.validate_withdrawal_address(to_address)
        if not is_valid:
            raise ValidationError("유효하지 않은 출금 주소입니다")

        # 3. 일일 한도 체크
        daily_total = await self._get_daily_withdrawal_total(user_id, asset)
        if daily_total + amount > self.max_withdrawal_per_day:
            remaining = self.max_withdrawal_per_day - daily_total
            raise ValidationError(f"일일 출금 한도를 초과했습니다. 잔여 한도: {remaining} {asset}")

        # 4. 수수료 계산
        withdrawal_fee = await self.fee_service.calculate_fee(
            "withdrawal", amount, asset
        )

        # 5. 잔고 확인
        balance = await self.balance_service.get_balance(user_id, asset)
        total_amount = amount + withdrawal_fee

        if not balance.can_withdraw(total_amount):
            raise InsufficientBalanceError(
                required=float(total_amount), available=float(balance.available_amount)
            )

        # 6. 잔고 잠금
        await self.balance_service.lock_amount(user_id, asset, total_amount)

        # 7. 출금 요청 생성
        withdrawal = Withdrawal(
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            fee=withdrawal_fee,
            net_amount=amount,  # 수신자가 받을 금액
            asset=asset,
            status=WithdrawalStatus.PENDING,
            priority=self._determine_priority(amount),
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(withdrawal)
        await self.db.flush()

        # 8. 트랜잭션 기록
        tx = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL,
            direction=TransactionDirection.OUT,
            status=TransactionStatus.PENDING,
            asset=asset,
            amount=amount,
            fee=withdrawal_fee,
            reference_id=f"WD-{withdrawal.id}",
            description=f"출금 요청: {to_address[:8]}...{to_address[-6:]}",
        )

        self.db.add(tx)
        await self.db.flush()

        logger.info(f"출금 요청 생성: ID {withdrawal.id}, 사용자 {user_id}, 금액 {amount} {asset}")

        return withdrawal

    async def _get_daily_withdrawal_total(self, user_id: int, asset: str) -> Decimal:
        """오늘 출금 총액 조회"""
        today = datetime.utcnow().date()
        result = await self.db.execute(
            select(func.sum(Withdrawal.amount)).filter(
                and_(
                    Withdrawal.user_id == user_id,
                    Withdrawal.asset == asset,
                    Withdrawal.requested_at >= today,
                    Withdrawal.status.notin_(
                        [
                            WithdrawalStatus.REJECTED,
                            WithdrawalStatus.CANCELLED,
                            WithdrawalStatus.FAILED,
                        ]
                    ),
                )
            )
        )
        total = result.scalar() or Decimal("0")
        return total

    def _determine_priority(self, amount: Decimal) -> WithdrawalPriority:
        """금액에 따른 우선순위 결정"""
        if amount >= 5000:
            return WithdrawalPriority.URGENT
        elif amount >= 1000:
            return WithdrawalPriority.HIGH
        elif amount >= 100:
            return WithdrawalPriority.NORMAL
        else:
            return WithdrawalPriority.LOW

    async def cancel_withdrawal(self, withdrawal_id: int, user_id: int) -> Withdrawal:
        """출금 취소 (사용자)"""
        result = await self.db.execute(
            select(Withdrawal).filter(
                and_(Withdrawal.id == withdrawal_id, Withdrawal.user_id == user_id)
            )
        )
        withdrawal = result.scalar_one_or_none()

        if not withdrawal:
            raise NotFoundError("출금 요청을 찾을 수 없습니다")

        if not withdrawal.can_cancel():
            raise ValidationError(f"{withdrawal.status} 상태의 출금은 취소할 수 없습니다")

        # 상태 업데이트
        withdrawal.status = WithdrawalStatus.CANCELLED

        # 잔고 잠금 해제
        await self.balance_service.unlock_amount(
            user_id, withdrawal.asset, withdrawal.total_amount
        )

        # 트랜잭션 상태 업데이트
        await self.db.execute(
            select(Transaction)
            .filter(Transaction.reference_id == f"WD-{withdrawal.id}")
            .update({"status": TransactionStatus.CANCELLED})
        )

        logger.info(f"출금 취소: ID {withdrawal_id}, 사용자 {user_id}")

        return withdrawal

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
            if withdrawal.status != WithdrawalStatus.PENDING:
                raise ValidationError(f"{withdrawal.status} 상태의 출금은 승인할 수 없습니다")

            withdrawal.status = WithdrawalStatus.APPROVED
            withdrawal.approved_at = datetime.utcnow()
            withdrawal.approved_by = admin_id

            logger.info(f"출금 승인: ID {withdrawal_id}, 관리자 {admin_id}")

        elif action == "reject":
            if not rejection_reason:
                raise ValidationError("거부 사유는 필수입니다")

            withdrawal.status = WithdrawalStatus.REJECTED
            withdrawal.rejection_reason = rejection_reason

            # 잔고 잠금 해제
            await self.balance_service.unlock_amount(
                withdrawal.user_id, withdrawal.asset, withdrawal.total_amount
            )

            # 트랜잭션 상태 업데이트
            await self.db.execute(
                select(Transaction)
                .filter(Transaction.reference_id == f"WD-{withdrawal.id}")
                .update({"status": TransactionStatus.FAILED})
            )

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
            raise ValidationError(f"{withdrawal.status} 상태의 출금은 처리할 수 없습니다")

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

        if withdrawal.status != WithdrawalStatus.APPROVED:
            raise ValidationError("승인된 출금만 처리할 수 있습니다")

        withdrawal.status = WithdrawalStatus.PROCESSING
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

        if withdrawal.status != WithdrawalStatus.PROCESSING:
            raise ValidationError(f"{withdrawal.status} 상태의 출금은 완료처리할 수 없습니다")

        # 출금 완료
        withdrawal.status = WithdrawalStatus.COMPLETED
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
        await self.db.execute(
            select(Transaction)
            .filter(Transaction.reference_id == f"WD-{withdrawal.id}")
            .update({"status": TransactionStatus.COMPLETED, "tx_hash": tx_hash})
        )

        logger.info(f"출금 완료: ID {withdrawal_id}, TX {tx_hash}")

        return withdrawal

    async def get_pending_withdrawals(
        self,
        status: Optional[WithdrawalStatus] = None,
        priority: Optional[WithdrawalPriority] = None,
    ) -> List[Withdrawal]:
        """대기 중인 출금 목록 조회"""
        query = select(Withdrawal).options(selectinload(Withdrawal.user))

        if status:
            query = query.filter(Withdrawal.status == status)
        else:
            # 기본적으로 처리가 필요한 상태들
            query = query.filter(
                Withdrawal.status.in_(
                    [
                        WithdrawalStatus.PENDING,
                        WithdrawalStatus.APPROVED,
                        WithdrawalStatus.PROCESSING,
                    ]
                )
            )

        if priority:
            query = query.filter(Withdrawal.priority == priority)

        # 우선순위와 요청 시간 순으로 정렬
        query = query.order_by(
            Withdrawal.priority.desc(), Withdrawal.requested_at.asc()
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_withdrawals(
        self,
        user_id: int,
        status: Optional[WithdrawalStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Withdrawal], int]:
        """사용자 출금 내역 조회"""
        query = select(Withdrawal).filter(Withdrawal.user_id == user_id)

        if status:
            query = query.filter(Withdrawal.status == status)

        # 전체 개수
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 페이지네이션
        query = query.order_by(Withdrawal.requested_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        withdrawals = result.scalars().all()

        return withdrawals, total
