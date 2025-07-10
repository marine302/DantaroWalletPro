"""
파트너사 온보딩 자동화 스키마 - Doc #29
온보딩 프로세스 관련 Pydantic 모델들
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.partner_onboarding import (
    OnboardingStatus, OnboardingStepStatus, ChecklistCategory
)


# === 요청 스키마 ===

class OnboardingCreateRequest(BaseModel):
    """온보딩 생성 요청"""
    partner_id: str = Field(..., description="파트너 ID")
    company_name: str = Field(..., description="회사명")
    contact_email: str = Field(..., description="담당자 이메일")
    business_type: str = Field(..., description="사업 유형")
    auto_proceed: bool = Field(True, description="자동 진행 여부")
    notification_email: Optional[str] = Field(None, description="알림 이메일")
    notification_webhook: Optional[str] = Field(None, description="웹훅 URL")
    main_wallet_address: Optional[str] = Field(None, description="메인 지갑 주소")
    brand_color: Optional[str] = Field("#2563eb", description="브랜드 컬러")
    logo_url: Optional[str] = Field(None, description="로고 URL")
    additional_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 설정")

    model_config = ConfigDict(from_attributes=True)


class StepStatusUpdateRequest(BaseModel):
    """단계 상태 업데이트 요청"""
    status: OnboardingStepStatus = Field(..., description="단계 상태")
    result_data: Optional[Dict[str, Any]] = Field(None, description="결과 데이터")
    error_message: Optional[str] = Field(None, description="오류 메시지")

    model_config = ConfigDict(from_attributes=True)


class ProgressUpdateRequest(BaseModel):
    """진행률 업데이트 요청"""
    current_step: int = Field(..., description="현재 단계")
    progress_percentage: int = Field(..., ge=0, le=100, description="진행률 (%)")
    status: Optional[OnboardingStatus] = Field(None, description="온보딩 상태")

    model_config = ConfigDict(from_attributes=True)


class ChecklistUpdateRequest(BaseModel):
    """체크리스트 업데이트 요청"""
    item_name: str = Field(..., description="항목명")
    is_completed: bool = Field(..., description="완료 여부")
    completed_by: Optional[str] = Field(None, description="완료자")
    notes: Optional[str] = Field(None, description="비고")

    model_config = ConfigDict(from_attributes=True)


class OnboardingLogRequest(BaseModel):
    """온보딩 로그 추가 요청"""
    level: str = Field(..., description="로그 레벨 (info, warning, error)")
    message: str = Field(..., description="메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")
    step_number: Optional[int] = Field(None, description="단계 번호")

    model_config = ConfigDict(from_attributes=True)


# === 응답 스키마 ===

class OnboardingStepResponse(BaseModel):
    """온보딩 단계 응답"""
    id: int
    step_number: int
    step_name: str
    step_description: Optional[str]
    status: OnboardingStepStatus
    handler_function: Optional[str]
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    is_automated: bool
    requires_manual_intervention: bool
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class OnboardingChecklistResponse(BaseModel):
    """온보딩 체크리스트 응답"""
    id: int
    category: ChecklistCategory
    item_name: str
    item_description: Optional[str]
    is_required: bool
    is_completed: bool
    is_automated: bool
    verification_method: Optional[str]
    verification_data: Optional[Dict[str, Any]]
    notes: Optional[str]
    completed_by: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class OnboardingLogResponse(BaseModel):
    """온보딩 로그 응답"""
    id: int
    level: str
    message: str
    details: Optional[Dict[str, Any]]
    step_number: Optional[int]
    action: Optional[str]
    actor: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OnboardingResponse(BaseModel):
    """온보딩 기본 응답"""
    id: int
    partner_id: str
    status: OnboardingStatus
    current_step: int
    total_steps: int
    progress_percentage: int
    registration_completed: bool
    account_setup_completed: bool
    wallet_setup_completed: bool
    system_config_completed: bool
    deployment_completed: bool
    testing_completed: bool
    configuration_data: Optional[Dict[str, Any]]
    deployment_info: Optional[Dict[str, Any]]
    test_results: Optional[Dict[str, Any]]
    auto_proceed: bool
    manual_approval_required: bool
    notification_email: Optional[str]
    notification_webhook: Optional[str]
    send_progress_updates: bool
    retry_count: int
    max_retries: int
    last_error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class OnboardingDetailResponse(OnboardingResponse):
    """온보딩 상세 응답 (단계, 체크리스트, 로그 포함)"""
    steps: List[OnboardingStepResponse] = Field(default_factory=list)
    checklist: List[OnboardingChecklistResponse] = Field(default_factory=list)
    logs: List[OnboardingLogResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OnboardingProgressResponse(BaseModel):
    """온보딩 진행률 응답"""
    partner_id: str
    status: OnboardingStatus
    current_step: int
    total_steps: int
    progress_percentage: int
    current_step_name: Optional[str]
    estimated_completion_time: Optional[datetime]
    next_step_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class OnboardingStatsResponse(BaseModel):
    """온보딩 통계 응답"""
    total_onboardings: int
    completed_onboardings: int
    failed_onboardings: int
    in_progress_onboardings: int
    average_completion_time_hours: Optional[float]
    completion_rate_percentage: float
    most_common_failure_step: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# === 성공/오류 응답 ===

class OnboardingSuccessResponse(BaseModel):
    """온보딩 성공 응답"""
    success: bool = True
    message: str
    onboarding_id: Optional[int] = None
    partner_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingErrorResponse(BaseModel):
    """온보딩 오류 응답"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# === 검색 및 필터링 ===

class OnboardingFilterRequest(BaseModel):
    """온보딩 필터링 요청"""
    status: Optional[OnboardingStatus] = Field(None, description="상태별 필터")
    partner_id: Optional[str] = Field(None, description="파트너 ID 필터")
    date_from: Optional[datetime] = Field(None, description="시작일 필터")
    date_to: Optional[datetime] = Field(None, description="종료일 필터")
    limit: int = Field(20, ge=1, le=100, description="결과 수 제한")
    offset: int = Field(0, ge=0, description="결과 오프셋")

    model_config = ConfigDict(from_attributes=True)


class OnboardingListResponse(BaseModel):
    """온보딩 목록 응답"""
    onboardings: List[OnboardingResponse]
    total_count: int
    has_more: bool
    next_offset: Optional[int]

    model_config = ConfigDict(from_attributes=True)
