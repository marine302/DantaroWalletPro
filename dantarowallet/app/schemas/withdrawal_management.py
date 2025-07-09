"""
출금 관리 관련 스키마 - Doc #28
파트너사별 출금 정책 및 배치 처리를 위한 스키마 정의
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import re


class WithdrawalPolicyTypeEnum(str, Enum):
    """출금 정책 유형"""
    REALTIME = "realtime"
    BATCH_DAILY = "batch_daily"
    BATCH_WEEKLY = "batch_weekly"
    BATCH_MONTHLY = "batch_monthly"
    MANUAL = "manual"
    HYBRID = "hybrid"


class ApprovalRuleTypeEnum(str, Enum):
    """승인 규칙 유형"""
    AUTO_APPROVE = "auto_approve"
    WHITELIST_ONLY = "whitelist_only"
    AMOUNT_LIMIT = "amount_limit"
    DAILY_LIMIT = "daily_limit"
    MANUAL_REVIEW = "manual_review"
    TWO_FACTOR = "two_factor"


class BatchExecutionDayEnum(str, Enum):
    """배치 실행 요일"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# === 출금 정책 스키마 ===

class PartnerWithdrawalPolicyCreate(BaseModel):
    """파트너 출금 정책 생성 요청"""
    policy_type: WithdrawalPolicyTypeEnum = Field(default=WithdrawalPolicyTypeEnum.HYBRID)
    
    # 자동 승인 설정
    auto_approve_enabled: bool = Field(default=False)
    auto_approve_max_amount: Optional[Decimal] = Field(None, ge=0)
    auto_approve_daily_limit: Optional[Decimal] = Field(None, ge=0)
    
    # 화이트리스트 설정
    whitelist_enabled: bool = Field(default=False)
    whitelist_only: bool = Field(default=False)
    
    # 금액 제한
    min_withdrawal_amount: Optional[Decimal] = Field(None, ge=0)
    max_withdrawal_amount: Optional[Decimal] = Field(None, ge=0)
    daily_withdrawal_limit: Optional[Decimal] = Field(None, ge=0)
    monthly_withdrawal_limit: Optional[Decimal] = Field(None, ge=0)
    
    # 배치 처리 설정
    batch_enabled: bool = Field(default=False)
    batch_execution_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    batch_execution_days: Optional[List[BatchExecutionDayEnum]] = Field(None)
    batch_min_count: Optional[int] = Field(1, ge=1)
    batch_max_count: Optional[int] = Field(100, ge=1, le=1000)
    
    # TronLink 자동 서명 설정
    auto_sign_enabled: bool = Field(default=False)
    auto_sign_max_amount: Optional[Decimal] = Field(None, ge=0)
    auto_sign_script_path: Optional[str] = Field(None, max_length=500)
    
    # 수수료 최적화 설정
    fee_optimization_enabled: bool = Field(default=True)
    energy_cost_threshold: Optional[Decimal] = Field(None, ge=0)
    optimal_batch_size: Optional[int] = Field(20, ge=1, le=100)
    
    # 보안 설정
    two_factor_required: bool = Field(default=False)
    ip_whitelist_enabled: bool = Field(default=False)
    risk_score_threshold: Optional[int] = Field(50, ge=0, le=100)
    
    # 알림 설정
    notification_enabled: bool = Field(default=True)
    notification_webhook_url: Optional[str] = Field(None, max_length=500)
    notification_email: Optional[str] = Field(None, max_length=255)


class PartnerWithdrawalPolicyUpdate(BaseModel):
    """파트너 출금 정책 업데이트 요청"""
    policy_type: Optional[WithdrawalPolicyTypeEnum] = None
    is_active: Optional[bool] = None
    
    # 자동 승인 설정
    auto_approve_enabled: Optional[bool] = None
    auto_approve_max_amount: Optional[Decimal] = Field(None, ge=0)
    auto_approve_daily_limit: Optional[Decimal] = Field(None, ge=0)
    
    # 화이트리스트 설정
    whitelist_enabled: Optional[bool] = None
    whitelist_only: Optional[bool] = None
    
    # 금액 제한
    min_withdrawal_amount: Optional[Decimal] = Field(None, ge=0)
    max_withdrawal_amount: Optional[Decimal] = Field(None, ge=0)
    daily_withdrawal_limit: Optional[Decimal] = Field(None, ge=0)
    monthly_withdrawal_limit: Optional[Decimal] = Field(None, ge=0)
    
    # 배치 처리 설정
    batch_enabled: Optional[bool] = None
    batch_execution_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    batch_execution_days: Optional[List[BatchExecutionDayEnum]] = None
    batch_min_count: Optional[int] = Field(None, ge=1)
    batch_max_count: Optional[int] = Field(None, ge=1, le=1000)
    
    # 보안 설정
    risk_score_threshold: Optional[int] = Field(None, ge=0, le=100)
    
    # 알림 설정
    notification_enabled: Optional[bool] = None
    notification_webhook_url: Optional[str] = Field(None, max_length=500)
    notification_email: Optional[str] = Field(None, max_length=255)


class PartnerWithdrawalPolicyResponse(PartnerWithdrawalPolicyCreate):
    """파트너 출금 정책 응답"""
    id: int
    partner_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === 승인 규칙 스키마 ===

class WithdrawalApprovalRuleCreate(BaseModel):
    """출금 승인 규칙 생성 요청"""
    rule_type: ApprovalRuleTypeEnum
    priority: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    
    # 조건 설정
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    max_daily_count: Optional[int] = Field(None, ge=1)
    max_daily_amount: Optional[Decimal] = Field(None, ge=0)
    
    # 시간 제한
    time_restrictions: Optional[Dict[str, Any]] = None
    
    # 승인 액션
    auto_approve: bool = Field(default=False)
    require_review: bool = Field(default=True)
    require_two_factor: bool = Field(default=False)
    
    # 추가 설정
    additional_settings: Optional[Dict[str, Any]] = None


class WithdrawalApprovalRuleResponse(WithdrawalApprovalRuleCreate):
    """출금 승인 규칙 응답"""
    id: int
    policy_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === 화이트리스트 스키마 ===

class WithdrawalWhitelistCreate(BaseModel):
    """출금 화이트리스트 생성 요청"""
    address: str = Field(..., min_length=34, max_length=42)
    label: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    
    # 제한 설정
    max_daily_amount: Optional[Decimal] = Field(None, ge=0)
    max_monthly_amount: Optional[Decimal] = Field(None, ge=0)
    
    # 유효 기간
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # 메타데이터
    notes: Optional[str] = Field(None, max_length=500)


class WithdrawalWhitelistResponse(WithdrawalWhitelistCreate):
    """출금 화이트리스트 응답"""
    id: int
    policy_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === 배치 처리 스키마 ===

class WithdrawalBatchCreate(BaseModel):
    """출금 배치 생성 요청"""
    withdrawal_ids: List[int] = Field(..., min_length=1, max_length=1000)
    scheduled_time: Optional[datetime] = None
    batch_type: str = Field(default="manual")


class WithdrawalBatchResponse(BaseModel):
    """출금 배치 응답"""
    id: int
    partner_id: str
    batch_type: str
    total_count: int
    total_amount: Decimal
    total_fee: Decimal
    scheduled_time: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    successful_count: int
    failed_count: int
    error_message: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === 출금 평가 스키마 ===

class WithdrawalEvaluationRequest(BaseModel):
    """출금 평가 요청"""
    withdrawal_id: int
    partner_id: str


class WithdrawalEvaluationResponse(BaseModel):
    """출금 평가 응답"""
    can_auto_approve: bool
    approval_reason: str
    risk_score: int
    required_actions: List[str]
    policy_applied: str
    
    # 상세 분석 결과
    evaluation_details: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


# === 배치 최적화 스키마 ===

class BatchOptimizationRequest(BaseModel):
    """배치 최적화 요청"""
    partner_id: str
    max_batches: Optional[int] = Field(10, ge=1, le=50)


class OptimizedBatchInfo(BaseModel):
    """최적화된 배치 정보"""
    withdrawal_ids: List[int]
    total_amount: Decimal
    total_count: int
    estimated_energy_cost: Decimal
    priority_score: int
    estimated_completion_time: Optional[datetime] = None


class BatchOptimizationResponse(BaseModel):
    """배치 최적화 응답"""
    optimized_batches: List[OptimizedBatchInfo]
    total_pending_withdrawals: int
    total_pending_amount: Decimal
    optimization_summary: Dict[str, Any]


# === 위험 점수 스키마 ===

class WithdrawalRiskScoreResponse(BaseModel):
    """출금 위험 점수 응답"""
    withdrawal_id: int
    total_score: int
    address_score: int
    amount_score: int
    frequency_score: int
    pattern_score: int
    risk_factors: List[str]
    risk_level: str
    recommended_action: str
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


# === 출금 통계 스키마 ===

class WithdrawalStatisticsRequest(BaseModel):
    """출금 통계 요청"""
    partner_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: Optional[str] = Field("day", pattern="^(hour|day|week|month)$")


class WithdrawalStatisticsResponse(BaseModel):
    """출금 통계 응답"""
    partner_id: str
    period: Dict[str, datetime]
    
    # 기본 통계
    total_withdrawals: int
    total_amount: Decimal
    total_fee: Decimal
    
    # 상태별 통계
    status_breakdown: Dict[str, int]
    
    # 자동화 통계
    auto_approved_count: int
    auto_approved_percentage: float
    batch_processed_count: int
    batch_processed_percentage: float
    
    # 성능 지표
    average_processing_time: float  # 분 단위
    success_rate: float
    
    # 시계열 데이터
    daily_stats: Optional[List[Dict[str, Any]]] = None
