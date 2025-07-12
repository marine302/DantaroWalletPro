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
    QUEUED = "queued"  # 배치 대기
    SIGNED = "signed"  # 서명됨
    PENDING_SIGNATURE = "pending_signature"  # 서명 대기


class WithdrawalPriority(str, Enum):
    """출금 우선순위"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class WithdrawalBatchStatus(str, Enum):
    """출금 배치 상태"""

    PENDING = "pending"  # 대기 중
    SCHEDULED = "scheduled"  # 예약됨
    PROCESSING = "processing"  # 처리 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소됨


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

    # Doc #28: 파트너사 출금 정책 관련 필드 추가
    partner_id = Column(String(50), nullable=True, index=True)
    batch_id = Column(String(36), nullable=True, index=True)  # 배치 처리 ID
    auto_approved = Column(Boolean, nullable=False, default=False)  # 자동 승인 여부
    risk_score = Column(Integer, nullable=True)  # 위험 점수
    whitelist_verified = Column(Boolean, nullable=False, default=False)  # 화이트리스트 검증
    policy_applied = Column(String(50), nullable=True)  # 적용된 정책 타입

    # 트랜잭션 정보
    tx_hash = Column(String(66), nullable=True, index=True)  # 트랜잭션 해시
    block_number = Column(Integer, nullable=True)  # 블록 번호
    gas_used = Column(Integer, nullable=True)  # 사용된 가스
    energy_used = Column(Integer, nullable=True)  # 사용된 에너지

    # 추가 메타데이터
    extra_data = Column(Text, nullable=True)  # JSON 형태의 추가 정보
    rejection_reason = Column(String(500), nullable=True)  # 거부 사유
    retry_count = Column(Integer, nullable=False, default=0)  # 재시도 횟수
    notes = Column(Text, nullable=True)  # 관리자 노트

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


class WithdrawalBatch(BaseModel):
    """
    출금 배치 모델.
    여러 출금 요청을 한 번에 처리하기 위한 배치 관리.
    """

    # 배치 정보
    batch_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    partner_id = Column(String(50), nullable=False, index=True)
    
    # 상태 정보
    status = Column(
        SQLEnum(WithdrawalBatchStatus),
        nullable=False,
        default=WithdrawalBatchStatus.PENDING,
        index=True,
    )
    
    # 처리 정보
    withdrawal_count = Column(Integer, nullable=False, default=0)  # 출금 건수
    total_amount = Column(Numeric(precision=28, scale=8), nullable=False, default=0)  # 총 출금 금액
    total_fee = Column(Numeric(precision=28, scale=8), nullable=False, default=0)  # 총 수수료
    
    # 스케줄링 정보
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # 예약 시간
    started_at = Column(DateTime(timezone=True), nullable=True)  # 시작 시간
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 완료 시간
    
    # 결과 정보
    success_count = Column(Integer, nullable=False, default=0)  # 성공 건수
    failed_count = Column(Integer, nullable=False, default=0)  # 실패 건수
    
    # 트랜잭션 정보
    tx_hash = Column(String(66), nullable=True, index=True)  # 배치 트랜잭션 해시
    block_number = Column(Integer, nullable=True)  # 블록 번호
    gas_used = Column(Integer, nullable=True)  # 사용된 가스
    energy_used = Column(Integer, nullable=True)  # 사용된 에너지
    
    # 관리자 정보
    created_by = Column(Integer, nullable=False)
    processed_by = Column(Integer, nullable=True)
    
    # 추가 메타데이터
    extra_data = Column(Text, nullable=True)  # JSON 형태의 추가 정보
    error_message = Column(Text, nullable=True)  # 오류 메시지
    notes = Column(Text, nullable=True)  # 관리자 노트

    def __repr__(self) -> str:
        return f"<WithdrawalBatch(batch_id={self.batch_id}, partner_id={self.partner_id}, status={self.status})>"

    def can_cancel(self) -> bool:
        """취소 가능한지 확인"""
        return str(self.status) in [
            WithdrawalBatchStatus.PENDING,
            WithdrawalBatchStatus.SCHEDULED,
        ]

    def can_process(self) -> bool:
        """처리 가능한지 확인"""
        return str(self.status) in [
            WithdrawalBatchStatus.PENDING,
            WithdrawalBatchStatus.SCHEDULED,
        ]

    @property
    def average_amount(self) -> Decimal:
        """평균 출금 금액"""
        count = getattr(self, 'withdrawal_count', 0)
        if count == 0:
            return Decimal("0")
        total = getattr(self, 'total_amount', 0)
        return Decimal(str(total)) / Decimal(str(count))


# 인덱스 설정
Index("idx_withdrawal_user_status", "user_id", "status")
Index("idx_withdrawal_partner_status", "partner_id", "status")
Index("idx_withdrawal_batch_status", "batch_id", "status")
Index("idx_withdrawal_batch_partner_status", "partner_id", "status")
