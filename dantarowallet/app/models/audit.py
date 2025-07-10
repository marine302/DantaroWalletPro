"""
감사 로그 모델 - Doc #30
트랜잭션 감사 및 컴플라이언스를 위한 모델들
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric, Boolean, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base


class AuditEventType(enum.Enum):
    """감사 이벤트 타입"""
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    WALLET_CREATED = "wallet_created"
    WITHDRAWAL_REQUESTED = "withdrawal_requested"
    WITHDRAWAL_APPROVED = "withdrawal_approved"
    WITHDRAWAL_REJECTED = "withdrawal_rejected"
    DEPOSIT_DETECTED = "deposit_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE_CHECK = "compliance_check"
    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action"
    SYSTEM_ACTION = "system_action"
    PARTNER_ONBOARDING = "partner_onboarding"
    PARTNER_ACTION = "partner_action"


class ComplianceCheckType(enum.Enum):
    """컴플라이언스 체크 타입"""
    KYC = "kyc"
    AML = "aml"
    SANCTIONS = "sanctions"
    PEP = "pep"
    TRANSACTION_LIMIT = "transaction_limit"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


class ComplianceStatus(enum.Enum):
    """컴플라이언스 상태"""
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


class RiskLevel(enum.Enum):
    """위험도 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """감사 로그"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_partner', 'partner_id'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_severity', 'severity'),
        Index('idx_audit_review', 'requires_review'),
    )
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 이벤트 정보
    event_type = Column(Enum(AuditEventType), nullable=False)
    event_category = Column(String(50))  # "transaction", "compliance", "security", "user", "admin"
    severity = Column(String(20))  # "info", "warning", "error", "critical"
    
    # 엔티티 정보
    entity_type = Column(String(50))  # "user", "transaction", "wallet", "partner"
    entity_id = Column(String(100))
    partner_id = Column(Integer, ForeignKey("partners.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 상세 정보
    event_data = Column(JSON, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # 블록체인 증적
    previous_hash = Column(String(64))  # 이전 로그의 해시
    log_hash = Column(String(64))       # 현재 로그의 해시
    blockchain_tx_hash = Column(String(64))  # 블록체인 저장 트랜잭션
    
    # 컴플라이언스
    compliance_flags = Column(JSON)
    risk_score = Column(Integer, default=0)
    requires_review = Column(Boolean, default=False)
    
    # 관계
    partner = relationship("Partner", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, entity_type={self.entity_type})>"


class ComplianceCheck(Base):
    """컴플라이언스 체크 기록"""
    __tablename__ = "compliance_checks"
    __table_args__ = (
        Index('idx_compliance_entity', 'entity_type', 'entity_id'),
        Index('idx_compliance_status', 'status'),
        Index('idx_compliance_type', 'check_type'),
        Index('idx_compliance_risk', 'risk_level'),
    )
    
    id = Column(Integer, primary_key=True)
    check_type = Column(Enum(ComplianceCheckType), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    
    # 체크 결과
    status = Column(Enum(ComplianceStatus), nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    score = Column(Integer, default=0)
    
    # 상세 정보
    check_data = Column(JSON)
    provider_response = Column(JSON)
    manual_review_notes = Column(String(1000))
    
    # 타임스탬프
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    
    # 관계
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<ComplianceCheck(id={self.id}, check_type={self.check_type}, status={self.status})>"


class SuspiciousActivity(Base):
    """의심스러운 활동 기록"""
    __tablename__ = "suspicious_activities"
    __table_args__ = (
        Index('idx_suspicious_user', 'user_id'),
        Index('idx_suspicious_severity', 'severity'),
        Index('idx_suspicious_detection', 'detection_type'),
        Index('idx_suspicious_detected_at', 'detected_at'),
    )
    
    id = Column(Integer, primary_key=True)
    detection_type = Column(String(100), nullable=False)  # "pattern", "threshold", "ml_model", "manual"
    severity = Column(Enum(RiskLevel), nullable=False)
    
    # 관련 엔티티
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_ids = Column(JSON)  # 관련 트랜잭션 ID 목록
    
    # 탐지 정보
    pattern_name = Column(String(100))
    pattern_data = Column(JSON)
    ml_model_name = Column(String(100))
    ml_model_version = Column(String(50))
    confidence_score = Column(Numeric(5, 4))
    
    # 상세 정보
    description = Column(String(1000))
    additional_data = Column(JSON)
    
    # 대응 조치
    action_taken = Column(String(100))  # "blocked", "flagged", "reported", "none"
    sar_filed = Column(Boolean, default=False)
    sar_reference = Column(String(100))
    
    # 타임스탬프
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(1000))
    resolved_by = Column(Integer, ForeignKey("users.id"))
    
    # 관계
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<SuspiciousActivity(id={self.id}, detection_type={self.detection_type}, severity={self.severity})>"


class AuditReport(Base):
    """감사 보고서"""
    __tablename__ = "audit_reports"
    __table_args__ = (
        Index('idx_audit_report_type', 'report_type'),
        Index('idx_audit_report_period', 'period_start', 'period_end'),
        Index('idx_audit_report_status', 'status'),
    )
    
    id = Column(Integer, primary_key=True)
    report_type = Column(String(50), nullable=False)  # "SAR", "CTR", "daily", "weekly", "monthly"
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    
    # 보고서 기간
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 보고서 상태
    status = Column(String(20), default="draft")  # "draft", "completed", "submitted", "approved"
    
    # 보고서 내용
    report_data = Column(JSON)
    summary = Column(JSON)
    recommendations = Column(JSON)
    
    # 파일 정보
    file_path = Column(String(500))
    file_format = Column(String(20))  # "pdf", "excel", "json"
    file_size = Column(Integer)
    
    # 제출 정보
    submitted_to = Column(String(100))  # 규제 기관명
    submitted_at = Column(DateTime)
    submission_reference = Column(String(100))
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    
    # 관계
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<AuditReport(id={self.id}, report_type={self.report_type}, status={self.status})>"
