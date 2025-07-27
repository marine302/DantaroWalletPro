"""
출금 배치 모델 - 문서 #41 기반
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
import enum

from app.models.base import BaseModel

class BatchStatus(enum.Enum):
    """배치 상태"""
    CREATED = "created"          # 생성됨
    PROCESSING = "processing"    # 처리 중
    COMPLETED = "completed"      # 완료
    PARTIAL = "partial"         # 부분 완료
    FAILED = "failed"           # 실패

class WithdrawalBatch(BaseModel):
    """출금 배치"""
    __tablename__ = "withdrawal_batches"

    batch_id = Column(String(32), unique=True, nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)

    # 배치 정보
    total_withdrawals = Column(Integer, default=0)
    total_amount_usdt = Column(Numeric(20, 6), default=0)
    total_energy_required = Column(Integer, default=0)

    # 에너지 비용
    energy_cost_trx = Column(Numeric(20, 6))
    saas_fee_trx = Column(Numeric(20, 6))
    total_cost_trx = Column(Numeric(20, 6))

    # 처리 정보
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # 상태
    status = Column(Enum(BatchStatus), default=BatchStatus.CREATED)

    # 메타데이터
    metadata = Column(JSON)  # 추가 정보 저장

    # 타임스탬프
    processing_started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # 관계
    partner = relationship("Partner", back_populates="withdrawal_batches")
    withdrawals = relationship("WithdrawalQueue",
                             foreign_keys="[WithdrawalQueue.batch_id]",
                             primaryjoin="WithdrawalQueue.batch_id==WithdrawalBatch.batch_id")

    def __repr__(self):
        return f"<WithdrawalBatch {self.batch_id} status={self.status.value}>"
