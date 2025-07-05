"""
출금 관련 모델.
사용자의 출금 요청과 처리 상태를 관리합니다.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.models.base import BaseModel
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text


class WithdrawalStatus(str, Enum):
    """출금 상태"""

    PENDING = "pending"  # 대기 중
    REVIEWING = "reviewing"  # 검토 중
    APPROVED = "approved"  # 승인됨
    PROCESSING = "processing"  # 처리 중
    COMPLETED = "completed"  # 완료
    REJECTED = "rejected"  # 거부됨
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소됨


class WithdrawalPriority(str, Enum):
    """출금 우선순위"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Withdrawal(BaseModel):
    """
    출금 요청 모델.
    사용자의 출금 요청과 처리 과정을 관리합니다.
    """

    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 출금 정보
    to_address = Column(String(42), nullable=False, index=True)  # 수신 주소
    amount = Column(Numeric(precision=28, scale=8), nullable=False)  # 출금 금액
    fee = Column(Numeric(precision=28, scale=8), nullable=False)  # 출금 수수료
    net_amount = Column(Numeric(precision=28, scale=8), nullable=False)  # 실제 받을 금액
    asset = Column(String(10), nullable=False, default="USDT")  # 자산 종류

    # 상태 정보
    status = Column(
        SQLEnum(WithdrawalStatus),
        nullable=False,
        default=WithdrawalStatus.PENDING,
        index=True,
    )
    priority = Column(
        SQLEnum(WithdrawalPriority), nullable=False, default=WithdrawalPriority.NORMAL
    )

    # 처리 정보
    requested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 관리자 정보
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Withdrawal(user_id={self.user_id}, to_address={self.to_address}, amount={self.amount}, status={self.status})>"

    @property
    def total_amount(self) -> Decimal:
        """총 차감 금액 (출금액 + 수수료)"""
        return Decimal(str(self.amount)) + Decimal(str(self.fee))

    def can_cancel(self) -> bool:
        """취소 가능한지 확인"""
        return str(self.status) in [
            WithdrawalStatus.PENDING,
            WithdrawalStatus.REVIEWING,
        ]

    def can_approve(self) -> bool:
        """승인 가능한지 확인"""
        return str(self.status) == WithdrawalStatus.REVIEWING

    def can_process(self) -> bool:
        """처리 가능한지 확인"""
        return str(self.status) == WithdrawalStatus.APPROVED
