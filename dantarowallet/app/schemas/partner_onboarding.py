"""
파트너사 온보딩 자동화 스키마 - Doc #29
온보딩 API 요청/응답 스키마를 정의합니다.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.partner_onboarding import (
    ChecklistCategory,
    OnboardingStatus,
    OnboardingStepStatus,
)

# === 기본 스키마 ===


class OnboardingStepInfo(BaseModel):
    """온보딩 단계 정보"""

    step_number: int
    step_name: str
    step_description: Optional[str] = None
    status: OnboardingStepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # 분
    actual_duration: Optional[int] = None  # 분
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ChecklistItemInfo(BaseModel):
    """체크리스트 항목 정보"""

    id: int
    category: ChecklistCategory
    item_name: str
    item_description: Optional[str] = None
    is_required: bool
    is_completed: bool
    is_automated: bool
    verification_method: Optional[str] = None
    notes: Optional[str] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OnboardingLogInfo(BaseModel):
    """온보딩 로그 정보"""

    id: int
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None
    step_number: Optional[int] = None
    action: Optional[str] = None
    actor: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === 요청 스키마 ===


class OnboardingStartRequest(BaseModel):
    """온보딩 시작 요청"""

    company_name: str = Field(..., min_length=2, max_length=200)
    business_type: str = Field(..., min_length=2, max_length=100)
    contact_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=100)

    # 온보딩 설정
    auto_proceed: bool = Field(default=True, description="자동 진행 여부")
    manual_approval_required: bool = Field(default=False, description="수동 승인 필요")
    notification_email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    notification_webhook: Optional[str] = Field(None, max_length=500)

    # 추가 설정
    subscription_plan: Optional[str] = Field(default="basic", max_length=50)
    monthly_limit: Optional[Decimal] = Field(default=Decimal("10000"), ge=0)
    commission_rate: Optional[Decimal] = Field(default=Decimal("0.001"), ge=0, le=1)

    # 브랜딩 설정
    branding: Optional[Dict[str, Any]] = Field(default_factory=dict)
    features: Optional[Dict[str, Any]] = Field(default_factory=dict)
    security: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("contact_email", "notification_email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("유효한 이메일 주소를 입력해주세요")
        return v


class ChecklistUpdateRequest(BaseModel):
    """체크리스트 업데이트 요청"""

    item_id: int = Field(..., description="체크리스트 항목 ID")
    completed: bool = Field(..., description="완료 여부")
    notes: Optional[str] = Field(None, max_length=1000, description="메모")
    completed_by: Optional[str] = Field(None, max_length=100, description="완료자")


class OnboardingRetryRequest(BaseModel):
    """온보딩 재시도 요청"""

    reason: Optional[str] = Field(None, max_length=500, description="재시도 사유")


# === 응답 스키마 ===


class OnboardingStatusResponse(BaseModel):
    """온보딩 상태 응답"""

    id: int
    partner_id: str
    status: OnboardingStatus
    current_step: int
    total_steps: int
    progress_percentage: int

    # 단계별 완료 상태
    registration_completed: bool
    account_setup_completed: bool
    wallet_setup_completed: bool
    system_config_completed: bool
    deployment_completed: bool
    testing_completed: bool

    # 설정 정보
    auto_proceed: bool
    manual_approval_required: bool
    notification_email: Optional[str] = None
    notification_webhook: Optional[str] = None

    # 오류 정보
    retry_count: int
    max_retries: int
    last_error: Optional[str] = None

    # 타임스탬프
    started_at: datetime
    completed_at: Optional[datetime] = None

    # 관련 데이터
    steps: List[OnboardingStepInfo] = []
    checklist: List[ChecklistItemInfo] = []

    class Config:
        from_attributes = True


class OnboardingProgressResponse(BaseModel):
    """온보딩 진행 상황 응답"""

    partner_id: str
    status: OnboardingStatus
    current_step: int
    progress_percentage: int
    estimated_completion: Optional[datetime] = None
    next_action_required: Optional[str] = None

    class Config:
        from_attributes = True


class OnboardingStepResponse(BaseModel):
    """온보딩 단계 응답"""

    onboarding_id: int
    step_info: OnboardingStepInfo
    can_proceed: bool
    blocking_issues: List[str] = []

    class Config:
        from_attributes = True


class ChecklistSummaryResponse(BaseModel):
    """체크리스트 요약 응답"""

    total_items: int
    completed_items: int
    required_items: int
    completed_required_items: int
    completion_percentage: int
    blocking_items: List[ChecklistItemInfo] = []

    class Config:
        from_attributes = True


class OnboardingLogsResponse(BaseModel):
    """온보딩 로그 응답"""

    onboarding_id: int
    logs: List[OnboardingLogInfo] = []
    total_count: int

    class Config:
        from_attributes = True


class OnboardingStatsResponse(BaseModel):
    """온보딩 통계 응답"""

    total_onboardings: int
    completed_onboardings: int
    failed_onboardings: int
    in_progress_onboardings: int
    average_completion_time: Optional[float] = None  # 시간 (시간 단위)
    success_rate: float

    # 단계별 통계
    step_statistics: Dict[str, Dict[str, Any]] = {}

    # 체크리스트 통계
    checklist_statistics: Dict[str, Dict[str, Any]] = {}

    class Config:
        from_attributes = True


# === 목록 응답 스키마 ===


class OnboardingListResponse(BaseModel):
    """온보딩 목록 응답"""

    onboardings: List[OnboardingStatusResponse] = []
    total_count: int
    page: int
    page_size: int
    has_next: bool

    class Config:
        from_attributes = True


# === 에러 응답 스키마 ===


class OnboardingErrorResponse(BaseModel):
    """온보딩 에러 응답"""

    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    retry_possible: bool = False

    class Config:
        from_attributes = True


# === 성공 응답 스키마 ===


class OnboardingSuccessResponse(BaseModel):
    """온보딩 성공 응답"""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
