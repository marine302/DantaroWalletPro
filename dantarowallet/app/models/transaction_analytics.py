"""
트랜잭션 분석 및 모니터링 모델
"""
from decimal import Decimal
from enum import Enum

from app.models.base import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class AlertLevel(str, Enum):
    """알림 레벨"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """알림 타입"""

    SUSPICIOUS_AMOUNT = "suspicious_amount"  # 의심스러운 금액
    FREQUENT_TRANSACTIONS = "frequent_transactions"  # 빈번한 거래
    UNUSUAL_PATTERN = "unusual_pattern"  # 비정상적인 패턴
    HIGH_VOLUME = "high_volume"  # 대량 거래
    RAPID_SUCCESSION = "rapid_succession"  # 연속 거래
    CROSS_BORDER = "cross_border"  # 국경간 거래 (추후 확장)


class TransactionAlert(BaseModel):
    """트랜잭션 알림 모델"""

    # 기본 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(
        Integer, ForeignKey("transactions.id"), nullable=True, index=True
    )

    # 알림 정보
    alert_type = Column(String(50), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # 상태 정보
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # 메타데이터
    alert_data = Column(Text, nullable=True)  # JSON 형태의 추가 데이터

    # 관계
    user = relationship("User", foreign_keys=[user_id])
    transaction = relationship("Transaction", foreign_keys=[transaction_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    # 인덱스
    __table_args__ = (
        Index("idx_alert_user_created", "user_id", "created_at"),
        Index("idx_alert_level_resolved", "level", "is_resolved"),
        Index("idx_alert_type_created", "alert_type", "created_at"),
    )

    def __repr__(self):
        return f"<TransactionAlert(id={self.id}, type={self.alert_type}, level={self.level})>"


class TransactionSummary(BaseModel):
    """트랜잭션 요약 통계 모델 (일/주/월별)"""

    # 기본 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)

    # TRX 통계
    trx_deposits_count = Column(Integer, default=0, nullable=False)
    trx_deposits_amount = Column(
        Numeric(precision=18, scale=6), default=0, nullable=False
    )
    trx_withdrawals_count = Column(Integer, default=0, nullable=False)
    trx_withdrawals_amount = Column(
        Numeric(precision=18, scale=6), default=0, nullable=False
    )

    # USDT 통계
    usdt_deposits_count = Column(Integer, default=0, nullable=False)
    usdt_deposits_amount = Column(
        Numeric(precision=18, scale=6), default=0, nullable=False
    )
    usdt_withdrawals_count = Column(Integer, default=0, nullable=False)
    usdt_withdrawals_amount = Column(
        Numeric(precision=18, scale=6), default=0, nullable=False
    )

    # 전체 통계
    total_transactions = Column(Integer, default=0, nullable=False)
    total_volume_usd = Column(Numeric(precision=18, scale=6), default=0, nullable=False)

    # 수수료 통계
    total_fees_trx = Column(Numeric(precision=18, scale=6), default=0, nullable=False)
    total_fees_usdt = Column(Numeric(precision=18, scale=6), default=0, nullable=False)

    # 관계
    user = relationship("User")

    # 인덱스
    __table_args__ = (
        Index("idx_summary_user_period", "user_id", "period_type", "period_start"),
        Index("idx_summary_period_type", "period_type", "period_start"),
    )

    def __repr__(self):
        return (
            f"<TransactionSummary(user_id={self.user_id}, period={self.period_type})>"
        )


class SystemTransactionAlert(BaseModel):
    """시스템 트랜잭션 관련 알림 모델"""
    __tablename__ = "system_transaction_alerts"

    # 알림 정보
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)

    # 상태 정보
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # 메타데이터
    alert_data = Column(Text, nullable=True)  # JSON 형태의 추가 데이터

    # 관계
    resolver = relationship("User", foreign_keys=[resolved_by])

    # 인덱스
    __table_args__ = (
        Index("idx_system_alert_active", "is_active", "created_at"),
        Index("idx_system_alert_level", "level", "is_resolved"),
    )

    def __repr__(self):
        return (
            f"<SystemTransactionAlert(id={self.id}, type={self.alert_type}, level={self.level})>"
        )
