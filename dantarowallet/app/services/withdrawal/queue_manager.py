"""
출금 큐 관리 서비스 - 문서 #41 기반
"""

from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.withdrawal_queue import WithdrawalQueue, WithdrawalStatus, WithdrawalType  # type: ignore
from app.models.partner_wallet import PartnerWallet, WalletType
from app.models.partner import Partner
from app.models.energy_allocation import AllocationStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class WithdrawalQueueManager:
    """출금 큐 관리자"""

    def __init__(self, db: Session):
        self.db = db

    async def add_to_queue(
        self,
        partner_id: int,
        user_id: int,
        amount: Decimal,
        to_address: str,
        withdrawal_type: WithdrawalType,
        memo: Optional[str] = None,
        scheduled_for: Optional[datetime] = None
    ) -> WithdrawalQueue:
        """출금 요청을 큐에 추가"""
        try:
            # 우선순위 계산
            priority = self._calculate_priority(withdrawal_type, amount)

            # 출금 큐 생성
            withdrawal = WithdrawalQueue(
                withdrawal_id=self._generate_withdrawal_id(),
                partner_id=partner_id,
                user_id=user_id,
                withdrawal_type=withdrawal_type,
                amount_usdt=amount,
                to_address=to_address,
                memo=memo,
                priority=priority,
                scheduled_for=scheduled_for if withdrawal_type == WithdrawalType.SCHEDULED else None
            )

            # 에너지 필요량 계산
            withdrawal.energy_required = self._calculate_energy_required(amount, to_address)

            self.db.add(withdrawal)
            self.db.commit()
            self.db.refresh(withdrawal)

            logger.info(f"출금 요청 큐 추가: {withdrawal.withdrawal_id}")

            # 즉시 출금인 경우 자동 승인 처리
            if withdrawal_type == WithdrawalType.IMMEDIATE:
                await self.approve_withdrawal(withdrawal.id)  # type: ignore

            return withdrawal

        except Exception as e:
            logger.error(f"출금 큐 추가 실패: {e}")
            self.db.rollback()
            raise

    async def approve_withdrawal(self, withdrawal_id: int) -> bool:
        """출금 승인"""
        try:
            withdrawal = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).first()

            if not withdrawal:
                raise ValueError("출금 요청을 찾을 수 없습니다")

            if withdrawal.status != WithdrawalStatus.PENDING:  # type: ignore
                raise ValueError(f"승인할 수 없는 상태입니다: {withdrawal.status}")

            # UPDATE 쿼리 사용
            self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).update({
                'status': WithdrawalStatus.APPROVED,
                'approved_at': datetime.utcnow()
            })

            self.db.commit()

            logger.info(f"출금 승인: {withdrawal.withdrawal_id}")

            # 자동으로 큐에 등록
            await self.queue_for_processing(withdrawal.id)  # type: ignore

            return True

        except Exception as e:
            logger.error(f"출금 승인 실패: {e}")
            self.db.rollback()
            raise

    async def queue_for_processing(self, withdrawal_id: int) -> bool:
        """처리를 위해 큐에 등록"""
        try:
            withdrawal = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).first()

            if not withdrawal:
                return False

            if withdrawal.status != WithdrawalStatus.APPROVED:  # type: ignore
                raise ValueError("승인된 출금만 큐에 등록할 수 있습니다")

            # UPDATE 쿼리 사용
            self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).update({
                'status': WithdrawalStatus.QUEUED,
                'queued_at': datetime.utcnow()
            })

            self.db.commit()

            logger.info(f"출금 큐 등록: {withdrawal.withdrawal_id}")
            return True

        except Exception as e:
            logger.error(f"출금 큐 등록 실패: {e}")
            self.db.rollback()
            raise

    async def get_pending_withdrawals(
        self, 
        partner_id: Optional[int] = None,
        limit: int = 100
    ) -> List[WithdrawalQueue]:
        """대기 중인 출금 목록 조회"""
        try:
            query = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.status.in_([
                    WithdrawalStatus.PENDING,
                    WithdrawalStatus.APPROVED,
                    WithdrawalStatus.QUEUED
                ])
            )

            if partner_id:
                query = query.filter(WithdrawalQueue.partner_id == partner_id)

            withdrawals = query.order_by(
                WithdrawalQueue.priority.desc(),
                WithdrawalQueue.created_at.asc()
            ).limit(limit).all()

            return withdrawals

        except Exception as e:
            logger.error(f"대기 출금 조회 실패: {e}")
            return []

    def _calculate_priority(self, withdrawal_type: WithdrawalType, amount: Decimal) -> int:
        """출금 우선순위 계산"""
        priority = 0
        
        # 타입별 우선순위
        if withdrawal_type == WithdrawalType.IMMEDIATE:
            priority += 100
        elif withdrawal_type == WithdrawalType.STANDARD:
            priority += 50
        elif withdrawal_type == WithdrawalType.SCHEDULED:
            priority += 10

        # 금액별 우선순위 (큰 금액일수록 높은 우선순위)
        if amount >= 10000:
            priority += 50
        elif amount >= 1000:
            priority += 20
        elif amount >= 100:
            priority += 10

        return priority

    def _calculate_energy_required(self, amount: Decimal, to_address: str) -> int:
        """에너지 필요량 계산"""
        # 기본 에너지 (USDT 전송)
        base_energy = 32000
        
        # 금액별 추가 에너지 (큰 금액일수록 더 많은 에너지)
        if amount >= 10000:
            return base_energy + 10000
        elif amount >= 1000:
            return base_energy + 5000
        else:
            return base_energy

    def _generate_withdrawal_id(self) -> str:
        """출금 ID 생성"""
        import uuid
        return f"WD{uuid.uuid4().hex[:12].upper()}"

    async def cancel_withdrawal(self, withdrawal_id: int, reason: str = "") -> bool:
        """출금 취소"""
        try:
            withdrawal = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).first()

            if not withdrawal:
                return False

            if withdrawal.status in [WithdrawalStatus.PROCESSING, WithdrawalStatus.COMPLETED]:
                raise ValueError("이미 처리 중이거나 완료된 출금은 취소할 수 없습니다")

            # UPDATE 쿼리 사용
            self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).update({
                'status': WithdrawalStatus.CANCELLED,
                'cancelled_at': datetime.utcnow(),
                'cancellation_reason': reason
            })

            self.db.commit()

            logger.info(f"출금 취소: {withdrawal.withdrawal_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"출금 취소 실패: {e}")
            self.db.rollback()
            raise
