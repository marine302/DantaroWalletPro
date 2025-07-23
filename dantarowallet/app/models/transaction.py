"""
트랜잭션 모델 정의.
내부 트랜잭션, 입출금 등 모든 금액 이동을 기록합니다.
"""

from decimal import Decimal
from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class TransactionType(str, Enum):
    """트랜잭션 타입"""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    BONUS = "bonus"
    FEE = "fee"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    """트랜잭션 상태"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionDirection(str, Enum):
    """트랜잭션 방향"""

    IN = "in"
    OUT = "out"
    INTERNAL = "internal"


class Transaction(BaseModel):
    """
    트랜잭션 모델
    """

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    direction = Column(SQLEnum(TransactionDirection), nullable=False)
    status = Column(
        SQLEnum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
    )
    asset = Column(String(10), nullable=False, default="USDT")
    amount = Column(Numeric(precision=18, scale=6), nullable=False)
    fee = Column(
        Numeric(precision=18, scale=6), nullable=False, default=Decimal("0.000000")
    )
    reference_id = Column(
        String(100), unique=True, nullable=True, index=True
    )  # 외부 참조 ID
    tx_hash = Column(String(100), nullable=True, index=True)  # 블록체인 트랜잭션 해시
    description = Column(Text, nullable=True)
    transaction_metadata = Column(Text, nullable=True)  # JSON 형태의 추가 데이터

    # 인덱스
    __table_args__ = (
        Index("idx_tx_user_created", "user_id", "created_at"),
        Index("idx_tx_status_type", "status", "type"),
        Index("idx_tx_reference", "reference_id"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(user_id={self.user_id}, type={self.type}, amount={self.amount}, status={self.status})>"

    @property
    def net_amount(self) -> Decimal:
        """수수료를 제외한 순 금액"""
        if self.direction == TransactionDirection.OUT:
            return self.amount + self.fee
        return self.amount - self.fee
