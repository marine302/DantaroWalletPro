"""
감사 및 컴플라이언스 스키마
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class AuditEventTypeSchema(str, Enum):
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


class AuditLogResponse(BaseModel):
    """감사 로그 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event_type: str
    event_category: Optional[str] = None
    severity: str
    entity_type: str
    entity_id: str
    partner_id: Optional[int] = None
    user_id: Optional[int] = None
    event_data: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    compliance_flags: Optional[Dict[str, Any]] = None
    risk_score: Optional[int] = None
    requires_review: bool


class ComplianceCheckRequest(BaseModel):
    """컴플라이언스 체크 요청 스키마"""

    user_id: int
    check_data: Dict[str, Any]


class ComplianceCheckResponse(BaseModel):
    """컴플라이언스 체크 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    check_type: str
    entity_type: str
    entity_id: str
    status: str
    risk_level: Optional[str] = None
    score: Optional[int] = None
    check_data: Optional[Dict[str, Any]] = None
    provider_response: Optional[Dict[str, Any]] = None
    manual_review_notes: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None


class SuspiciousActivityResponse(BaseModel):
    """의심스러운 활동 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    detection_type: str
    severity: str
    user_id: Optional[int] = None
    transaction_ids: Optional[List[str]] = None
    pattern_name: Optional[str] = None
    pattern_data: Optional[Dict[str, Any]] = None
    ml_model_name: Optional[str] = None
    confidence_score: Optional[float] = None
    action_taken: Optional[str] = None
    sar_filed: bool
    sar_reference: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AnomalyDetectionRequest(BaseModel):
    """이상 탐지 요청 스키마"""

    user_id: int
    transaction_data: Optional[Dict[str, Any]] = None
    time_window_days: Optional[int] = 30


class AuditStatsResponse(BaseModel):
    """감사 통계 응답 스키마"""

    period_days: int
    total_audit_logs: int
    critical_logs: int
    total_compliance_checks: int
    failed_checks: int
    suspicious_activities: int
    compliance_success_rate: float
