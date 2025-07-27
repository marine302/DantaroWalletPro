"""
출금 큐 모델 - 문서 #41 기반
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean, Index
from decimal import Decimal
from datetime import datetime
from app.models.base import BaseModel
import enum

class WithdrawalStatus(enum.Enum):
    """출금 상태"""
    PENDING = "pending"          # 대기 중
    APPROVED = "approved"        # 승인됨
    QUEUED = "queued"           # 큐에 추가됨
    PROCESSING = "processing"    # 처리 중
    COMPLETED = "completed"      # 완료
    FAILED = "failed"           # 실패
    CANCELLED = "cancelled"     # 취소됨

class WithdrawalPriority(enum.Enum):
    """출금 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class WithdrawalQueue(BaseModel):
    """출금 큐 모델"""

    # 식별자
    withdrawal_id = Column(String(32), unique=True, nullable=False)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    batch_id = Column(String(32))

    # 출금 정보
    to_address = Column(String(34), nullable=False)
    amount_usdt = Column(Numeric(20, 6), nullable=False)
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING)
    priority = Column(Enum(WithdrawalPriority), default=WithdrawalPriority.NORMAL)

    # 에너지 정보
    required_energy = Column(Integer)
    energy_allocated = Column(Boolean, default=False)
    energy_allocation_id = Column(String(32))

    # 수수료 정보
    energy_fee_trx = Column(Numeric(20, 6))
    withdrawal_fee_usdt = Column(Numeric(20, 6))
    saas_fee_usdt = Column(Numeric(20, 6))
    total_fee_usdt = Column(Numeric(20, 6))

    # 타임스탬프
    approved_at = Column(DateTime)
    queued_at = Column(DateTime)
    processing_started_at = Column(DateTime)
    completed_at = Column(DateTime)
    scheduled_for = Column(DateTime)  # 정기 출금용

    # 트랜잭션 정보
    funding_tx_hash = Column(String(64))  # 콜드→핫 월렛 이동
    withdrawal_tx_hash = Column(String(64))  # 실제 출금

    # 인덱스
    __table_args__ = (
        Index('idx_partner_status', 'partner_id', 'status'),
        Index('idx_batch_processing', 'batch_id', 'status'),
        Index('idx_scheduled_withdrawals', 'scheduled_for', 'status'),
    )

    def __repr__(self):
        return f"<WithdrawalQueue {self.withdrawal_id} {self.status.value} {self.amount_usdt}>"
