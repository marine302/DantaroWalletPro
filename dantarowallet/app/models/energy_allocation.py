"""
에너지 할당 모델 - 문서 #40 기반
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class AllocationStatus(enum.Enum):
    """할당 상태"""
    PENDING = "pending"              # 대기 중
    PROCESSING = "processing"        # 처리 중
    COMPLETED = "completed"          # 완료
    FAILED = "failed"               # 실패
    CANCELLED = "cancelled"         # 취소됨
    FALLBACK = "fallback"           # 폴백 모드

class EnergyAllocation(BaseModel):
    """에너지 할당 기록"""

    allocation_id = Column(String(32), unique=True, nullable=False)  # 고유 할당 ID

    # 요청 정보
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False)
    withdrawal_request_id = Column(Integer, nullable=True)
    batch_id = Column(String(32))  # 배치 처리 ID

    # 공급원 정보
    supplier_id = Column(Integer, nullable=True)  # 임시로 FK 제거
    supplier_type = Column(String(20))

    # 할당 정보
    target_address = Column(String(34), nullable=False)  # 에너지 수신 주소
    energy_amount = Column(BigInteger, nullable=False)
    duration_days = Column(Integer, default=1)

    # 비용 정보
    energy_price = Column(Numeric(20, 10))  # 에너지당 가격
    base_cost_trx = Column(Numeric(20, 6))  # 기본 비용
    margin_rate = Column(Numeric(5, 2))  # 마진율
    margin_amount_trx = Column(Numeric(20, 6))  # 마진 금액
    saas_fee_trx = Column(Numeric(20, 6))  # SaaS 수수료
    total_cost_trx = Column(Numeric(20, 6))  # 총 비용

    # 트랜잭션 정보
    payment_tx_hash = Column(String(64))  # TRX 결제 트랜잭션
    delegation_tx_hash = Column(String(64))  # 에너지 위임 트랜잭션

    # 상태 관리
    status = Column(Enum(AllocationStatus), default=AllocationStatus.PENDING)
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)

    # 폴백 정보
    is_fallback = Column(Boolean, default=False)
    estimated_burn_trx = Column(Numeric(20, 6))  # 예상 TRX 소각량
    actual_burn_trx = Column(Numeric(20, 6))  # 실제 TRX 소각량

    # 타임스탬프
    payment_confirmed_at = Column(DateTime)
    delegated_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)

    def __repr__(self):
        return f"<EnergyAllocation {self.allocation_id} {self.status.value} {self.energy_amount}>"
