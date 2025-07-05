"""
잔고 관리 서비스.
사용자 잔고 조회, 내부 이체, 잔고 조정 등 모든 잔고 관련 비즈니스 로직을 처리합니다.
"""
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.exceptions import InsufficientBalanceError, NotFoundError, ValidationError
from app.models.balance import Balance
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.user import User
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class BalanceService:
    """잔고 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: int, asset: str = "USDT") -> Balance:
        """사용자 잔고 조회"""
        result = await self.db.execute(
            select(Balance).filter(
                and_(Balance.user_id == user_id, Balance.asset == asset)
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            raise NotFoundError(f"Balance for asset {asset}")

        return balance

    async def get_or_create_balance(self, user_id: int, asset: str = "USDT") -> Balance:
        """잔고 조회 또는 생성"""
        try:
            return await self.get_balance(user_id, asset)
        except NotFoundError:
            # 잔고가 없으면 생성
            balance = Balance(
                user_id=user_id,
                asset=asset,
                amount=Decimal("0.000000"),
                locked_amount=Decimal("0.000000"),
            )
            self.db.add(balance)
            await self.db.flush()
            return balance

    async def internal_transfer(
        self,
        sender_id: int,
        receiver_id: int,
        amount: Decimal,
        description: Optional[str] = None,
        asset: str = "USDT",
    ) -> Dict[str, Any]:
        """내부 이체 처리"""

        # 금액 검증
        if amount <= 0:
            raise ValidationError("Transfer amount must be positive")

        # 최소 금액 체크 (0.000001 USDT)
        if amount < Decimal("0.000001"):
            raise ValidationError("Amount too small")

        # 자기 자신에게 이체 방지
        if sender_id == receiver_id:
            raise ValidationError("Cannot transfer to yourself")

        # 트랜잭션 시작
        async with self.db.begin_nested():
            # 발신자 잔고 조회 (FOR UPDATE로 락)
            sender_balance = await self.db.execute(
                select(Balance)
                .filter(and_(Balance.user_id == sender_id, Balance.asset == asset))
                .with_for_update()
            )
            sender_balance = sender_balance.scalar_one_or_none()

            if not sender_balance:
                raise NotFoundError(f"Sender balance for {asset}")

            # 잔고 충분한지 확인
            if not sender_balance.can_withdraw(amount):
                raise InsufficientBalanceError(
                    required=float(amount),
                    available=float(sender_balance.available_amount),
                )

            # 수신자 잔고 조회 또는 생성
            receiver_balance = await self.get_or_create_balance(receiver_id, asset)

            # 잔고 업데이트
            sender_balance.amount -= amount
            receiver_balance.amount += amount

            # 트랜잭션 기록 생성
            reference_id = f"INT-{datetime.utcnow().timestamp()}"

            # 발신자 트랜잭션
            sender_tx = Transaction(
                user_id=sender_id,
                type=TransactionType.TRANSFER,
                direction=TransactionDirection.OUT,
                status=TransactionStatus.COMPLETED,
                asset=asset,
                amount=amount,
                fee=Decimal("0"),  # 내부 이체는 수수료 없음
                reference_id=f"{reference_id}-OUT",
                description=description or "Internal transfer",
            )

            # 수신자 트랜잭션
            receiver_tx = Transaction(
                user_id=receiver_id,
                type=TransactionType.TRANSFER,
                direction=TransactionDirection.IN,
                status=TransactionStatus.COMPLETED,
                asset=asset,
                amount=amount,
                fee=Decimal("0"),
                reference_id=f"{reference_id}-IN",
                description=description or "Internal transfer received",
            )

            self.db.add(sender_tx)
            self.db.add(receiver_tx)

            await self.db.flush()

        # 커밋은 상위 레벨에서 처리
        logger.info(
            f"Internal transfer completed: {sender_id} -> {receiver_id}, "
            f"amount: {amount} {asset}"
        )

        return {
            "sender_balance": sender_balance.amount,
            "receiver_balance": receiver_balance.amount,
            "transaction_id": sender_tx.id,
            "reference_id": reference_id,
        }

    async def adjust_balance(
        self,
        user_id: int,
        amount: Decimal,
        adjustment_type: str,
        description: str,
        admin_id: int,
        asset: str = "USDT",
    ) -> Balance:
        """관리자에 의한 잔고 조정 (입금 시뮬레이션, 보너스 등)"""

        balance = await self.get_or_create_balance(user_id, asset)

        # 금액 적용
        if amount > 0:
            balance.amount += amount
            direction = TransactionDirection.IN
        else:
            if balance.available_amount < abs(amount):
                raise InsufficientBalanceError(
                    required=float(abs(amount)),
                    available=float(balance.available_amount),
                )
            balance.amount += amount  # amount가 음수
            direction = TransactionDirection.OUT

        # 트랜잭션 기록
        tx = Transaction(
            user_id=user_id,
            type=TransactionType.ADJUSTMENT,
            direction=direction,
            status=TransactionStatus.COMPLETED,
            asset=asset,
            amount=abs(amount),
            fee=Decimal("0"),
            description=description,
            metadata=json.dumps(
                {
                    "adjustment_type": adjustment_type,
                    "admin_id": admin_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        )

        self.db.add(tx)
        await self.db.flush()

        logger.info(
            f"Balance adjustment: user={user_id}, amount={amount}, "
            f"type={adjustment_type}, admin={admin_id}"
        )

        return balance

    async def lock_amount(
        self, user_id: int, amount: Decimal, asset: str = "USDT"
    ) -> bool:
        """금액 잠금 (출금 준비 등)"""
        balance = await self.get_balance(user_id, asset)

        if balance.lock(amount):
            await self.db.flush()
            return True

        raise InsufficientBalanceError(
            required=float(amount), available=float(balance.available_amount)
        )

    async def unlock_amount(
        self, user_id: int, amount: Decimal, asset: str = "USDT"
    ) -> bool:
        """금액 잠금 해제"""
        balance = await self.get_balance(user_id, asset)

        if balance.unlock(amount):
            await self.db.flush()
            return True

        raise ValidationError(f"Cannot unlock {amount} {asset}")

    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        tx_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> List[Transaction]:
        """트랜잭션 내역 조회"""
        query = select(Transaction).filter(Transaction.user_id == user_id)

        if tx_type:
            query = query.filter(Transaction.type == tx_type)

        if status:
            query = query.filter(Transaction.status == status)

        query = query.order_by(Transaction.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_balance_summary(self, user_id: int) -> Dict[str, Any]:
        """잔고 요약 정보"""
        # 모든 잔고 조회
        result = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id)
        )
        balances = result.scalars().all()

        # 최근 트랜잭션
        recent_txs = await self.get_transaction_history(user_id, limit=10)

        # 통계 계산
        total_in = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.direction == TransactionDirection.IN,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        total_in = total_in.scalar() or Decimal("0")

        total_out = await self.db.execute(
            select(func.sum(Transaction.amount + Transaction.fee)).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.direction == TransactionDirection.OUT,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        total_out = total_out.scalar() or Decimal("0")

        return {
            "balances": [
                {
                    "asset": b.asset,
                    "amount": str(b.amount),
                    "locked_amount": str(b.locked_amount),
                    "available_amount": str(b.available_amount),
                }
                for b in balances
            ],
            "recent_transactions": recent_txs,
            "statistics": {
                "total_received": str(total_in),
                "total_sent": str(total_out),
                "net_flow": str(total_in - total_out),
            },
        }

    async def add_balance(
        self,
        user_id: int,
        asset: str,
        amount: Decimal,
        transaction_type: str = "deposit",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """잔고 증가 처리"""

        # 금액 검증
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        # 트랜잭션 시작
        async with self.db.begin_nested():
            # 사용자 잔고 조회 또는 생성
            balance = await self.get_or_create_balance(user_id, asset)

            # 잔고 업데이트 (FOR UPDATE로 락)
            balance_result = await self.db.execute(
                select(Balance)
                .filter(and_(Balance.user_id == user_id, Balance.asset == asset))
                .with_for_update()
            )
            balance = balance_result.scalar_one()

            # 이전 잔고
            previous_amount = balance.amount

            # 잔고 증가 (update 쿼리 사용)
            await self.db.execute(
                balance.__class__.__table__.update()
                .where(and_(Balance.user_id == user_id, Balance.asset == asset))
                .values(amount=Balance.amount + amount, updated_at=func.now())
            )

            # 새 잔고 조회
            new_balance_result = await self.db.execute(
                select(Balance).filter(
                    and_(Balance.user_id == user_id, Balance.asset == asset)
                )
            )
            new_balance = new_balance_result.scalar_one()

            # 트랜잭션 기록 생성
            transaction = Transaction(
                user_id=user_id,
                type=TransactionType.DEPOSIT
                if transaction_type == "deposit"
                else TransactionType.BONUS,
                direction=TransactionDirection.IN,
                asset=asset,
                amount=amount,
                status=TransactionStatus.COMPLETED,
                description=description
                or f"{transaction_type.title()}: {amount} {asset}",
                transaction_metadata=json.dumps(
                    {
                        "previous_balance": str(previous_amount),
                        "new_balance": str(new_balance.amount),
                        "transaction_type": transaction_type,
                    }
                ),
            )

            self.db.add(transaction)

            # 변경사항 플러시
            await self.db.flush()

            logger.info(f"잔고 증가: 사용자 {user_id}, {amount} {asset}")

            return {
                "user_id": user_id,
                "asset": asset,
                "amount": str(amount),
                "previous_balance": str(previous_amount),
                "new_balance": str(new_balance.amount),
                "transaction_id": transaction.id,
            }
