"""
감사 및 컴플라이언스 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric, Boolean, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class AuditEventType(enum.Enum):
    """감사 이벤트 유형"""
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    WALLET_CREATED = "wallet_created"
    WITHDRAWAL_REQUESTED = "withdrawal_requested"
    WITHDRAWAL_APPROVED = "withdrawal_approved"
    DEPOSIT_DETECTED = "deposit_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE_CHECK = "compliance_check"
    USER_ACTION = "user_action"
    SYSTEM_ACTION = "system_action"

class AuditLog(Base):
    """감사 로그"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
    )
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 이벤트 정보
    event_type = Column(Enum(AuditEventType), nullable=False)
    event_category = Column(String(50))  # "transaction", "compliance", "security"
    severity = Column(String(20))  # "info", "warning", "critical"
    
    # 엔티티 정보
    entity_type = Column(String(50))  # "user", "transaction", "wallet"
    entity_id = Column(String(100))
    partner_id = Column(Integer, ForeignKey("partners.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 상세 정보
    event_data = Column(JSON, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # 블록체인 증적
    block_hash = Column(String(64))  # 이전 로그의 해시
    log_hash = Column(String(64))    # 현재 로그의 해시
    blockchain_tx_hash = Column(String(64))  # 블록체인 저장 트랜잭션
    
    # 컴플라이언스
    compliance_flags = Column(JSON)
    risk_score = Column(Integer)
    requires_review = Column(Boolean, default=False)

class ComplianceCheck(Base):
    """컴플라이언스 체크 기록"""
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True)
    check_type = Column(String(50))  # "kyc", "aml", "sanctions", "pep"
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    
    # 체크 결과
    status = Column(String(20))  # "passed", "failed", "pending", "manual_review"
    risk_level = Column(String(20))  # "low", "medium", "high", "critical"
    score = Column(Integer)
    
    # 상세 정보
    check_data = Column(JSON)
    provider_response = Column(JSON)
    manual_review_notes = Column(String(1000))
    
    # 타임스탬프
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))

class SuspiciousActivity(Base):
    """의심스러운 활동 기록"""
    __tablename__ = "suspicious_activities"
    
    id = Column(Integer, primary_key=True)
    detection_type = Column(String(100))  # "pattern", "threshold", "ml_model"
    severity = Column(String(20))
    
    # 관련 엔티티
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_ids = Column(JSON)  # 관련 트랜잭션 ID 목록
    
    # 탐지 정보
    pattern_name = Column(String(100))
    pattern_data = Column(JSON)
    ml_model_name = Column(String(100))
    confidence_score = Column(Numeric(5, 4))
    
    # 대응 조치
    action_taken = Column(String(100))  # "blocked", "flagged", "reported"
    sar_filed = Column(Boolean, default=False)
    sar_reference = Column(String(100))
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(1000))
