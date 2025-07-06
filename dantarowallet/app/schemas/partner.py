"""파트너사 관련 스키마"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr


# 파트너 기본 스키마
class PartnerBase(BaseModel):
    """파트너 기본 스키마"""
    name: str = Field(..., max_length=100, description="파트너사명")
    domain: Optional[str] = Field(None, max_length=255, description="도메인")
    webhook_url: Optional[str] = Field(None, max_length=500, description="웹훅 URL")
    commission_rate: Decimal = Field(0, ge=0, le=1, description="수수료율")
    
    # 화이트라벨링 설정
    brand_name: Optional[str] = Field(None, max_length=100, description="브랜드명")
    logo_url: Optional[str] = Field(None, max_length=500, description="로고 URL")
    primary_color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$", description="주요 색상")
    secondary_color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$", description="보조 색상")
    
    # 연락처 정보
    contact_email: Optional[EmailStr] = Field(None, description="연락처 이메일")
    contact_phone: Optional[str] = Field(None, max_length=50, description="연락처 전화번호")
    contact_person: Optional[str] = Field(None, max_length=100, description="담당자명")
    
    # 비즈니스 정보
    business_type: Optional[str] = Field(None, max_length=50, description="비즈니스 유형")
    country: Optional[str] = Field(None, max_length=50, description="국가")
    timezone: Optional[str] = Field("Asia/Seoul", max_length=50, description="타임존")
    language: str = Field("ko", max_length=10, description="기본 언어")


class PartnerCreate(PartnerBase):
    """파트너 생성 요청"""
    # 제한 설정
    daily_transaction_limit: Optional[Decimal] = Field(None, ge=0, description="일일 거래 한도")
    monthly_transaction_limit: Optional[Decimal] = Field(None, ge=0, description="월간 거래 한도")
    max_users: Optional[int] = Field(None, ge=1, description="최대 사용자 수")


class PartnerUpdate(BaseModel):
    """파트너 업데이트 요청"""
    name: Optional[str] = Field(None, max_length=100, description="파트너사명")
    domain: Optional[str] = Field(None, max_length=255, description="도메인")
    webhook_url: Optional[str] = Field(None, max_length=500, description="웹훅 URL")
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=1, description="수수료율")
    
    # 화이트라벨링 설정
    brand_name: Optional[str] = Field(None, max_length=100, description="브랜드명")
    logo_url: Optional[str] = Field(None, max_length=500, description="로고 URL")
    primary_color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$", description="주요 색상")
    secondary_color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$", description="보조 색상")
    
    # 연락처 정보
    contact_email: Optional[EmailStr] = Field(None, description="연락처 이메일")
    contact_phone: Optional[str] = Field(None, max_length=50, description="연락처 전화번호")
    contact_person: Optional[str] = Field(None, max_length=100, description="담당자명")
    
    # 제한 설정
    daily_transaction_limit: Optional[Decimal] = Field(None, ge=0, description="일일 거래 한도")
    monthly_transaction_limit: Optional[Decimal] = Field(None, ge=0, description="월간 거래 한도")
    max_users: Optional[int] = Field(None, ge=1, description="최대 사용자 수")
    
    is_active: Optional[bool] = Field(None, description="활성 상태")


class Partner(PartnerBase):
    """파트너 응답"""
    id: int
    api_key: str
    is_active: bool
    onboarding_status: str
    daily_transaction_limit: Optional[Decimal]
    monthly_transaction_limit: Optional[Decimal]
    max_users: Optional[int]
    last_activity_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PartnerStats(BaseModel):
    """파트너 통계"""
    partner_id: int
    partner_name: str
    
    # 사용자 통계
    total_users: int = Field(..., description="총 사용자 수")
    active_users: int = Field(..., description="활성 사용자 수")
    new_users_today: int = Field(..., description="오늘 신규 사용자 수")
    
    # 거래 통계
    total_transactions: int = Field(..., description="총 거래 수")
    today_transactions: int = Field(..., description="오늘 거래 수")
    transaction_volume: Decimal = Field(..., description="총 거래량")
    today_volume: Decimal = Field(..., description="오늘 거래량")
    
    # 수수료 통계
    total_fee_collected: Decimal = Field(..., description="총 수수료 수집액")
    today_fee_collected: Decimal = Field(..., description="오늘 수수료 수집액")
    
    # API 사용 통계
    api_calls_today: int = Field(..., description="오늘 API 호출 수")
    api_error_rate: float = Field(..., description="API 오류율")


# API 키 관련 스키마
class ApiKeyResponse(BaseModel):
    """API 키 응답"""
    api_key: str = Field(..., description="API 키")
    api_secret: str = Field(..., description="API 시크릿")
    created_at: datetime = Field(..., description="생성 시간")


class ApiKeyRotateRequest(BaseModel):
    """API 키 회전 요청"""
    reason: Optional[str] = Field(None, description="회전 사유")


# 파트너 사용자 관련 스키마
class PartnerUserBase(BaseModel):
    """파트너 사용자 기본 스키마"""
    partner_user_id: Optional[str] = Field(None, description="파트너사 내부 사용자 ID")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="커스텀 데이터")


class PartnerUserCreate(PartnerUserBase):
    """파트너 사용자 생성 요청"""
    user_id: int = Field(..., description="사용자 ID")


class PartnerUser(PartnerUserBase):
    """파트너 사용자 응답"""
    id: int
    partner_id: int
    user_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# 웹훅 관련 스키마
class WebhookConfigBase(BaseModel):
    """웹훅 설정 기본 스키마"""
    event_type: str = Field(..., description="이벤트 유형")
    webhook_url: str = Field(..., description="웹훅 URL")
    secret_key: Optional[str] = Field(None, description="시크릿 키")
    retry_count: int = Field(3, ge=1, le=10, description="재시도 횟수")
    timeout_seconds: int = Field(30, ge=5, le=300, description="타임아웃 (초)")


class WebhookConfigCreate(WebhookConfigBase):
    """웹훅 설정 생성 요청"""
    pass


class WebhookConfig(WebhookConfigBase):
    """웹훅 설정 응답"""
    id: int
    partner_id: int
    is_active: bool
    success_count: int
    failure_count: int
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# 파트너 온보딩 관련 스키마
class OnboardingStatus(BaseModel):
    """온보딩 상태"""
    status: str = Field(..., description="온보딩 상태")
    completed_steps: List[str] = Field(..., description="완료된 단계들")
    next_steps: List[str] = Field(..., description="다음 단계들")
    progress_percentage: float = Field(..., ge=0, le=100, description="진행률")


class OnboardingStepComplete(BaseModel):
    """온보딩 단계 완료 요청"""
    step_name: str = Field(..., description="완료된 단계명")
    step_data: Optional[Dict[str, Any]] = Field(None, description="단계 데이터")


# 파트너 설정 관련 스키마
class PartnerSettings(BaseModel):
    """파트너 설정"""
    # UI 커스터마이징
    custom_css: Optional[str] = Field(None, description="커스텀 CSS")
    logo_url: Optional[str] = Field(None, description="로고 URL")
    primary_color: Optional[str] = Field(None, description="주요 색상")
    secondary_color: Optional[str] = Field(None, description="보조 색상")
    
    # 기능 설정
    features_enabled: Dict[str, bool] = Field(..., description="활성화된 기능들")
    notification_settings: Dict[str, Any] = Field(..., description="알림 설정")
    
    # 제한 설정
    transaction_limits: Dict[str, Decimal] = Field(..., description="거래 한도 설정")


class PartnerSettingsUpdate(BaseModel):
    """파트너 설정 업데이트 요청"""
    custom_css: Optional[str] = Field(None, description="커스텀 CSS")
    logo_url: Optional[str] = Field(None, description="로고 URL")
    primary_color: Optional[str] = Field(None, description="주요 색상")
    secondary_color: Optional[str] = Field(None, description="보조 색상")
    features_enabled: Optional[Dict[str, bool]] = Field(None, description="활성화된 기능들")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="알림 설정")
    transaction_limits: Optional[Dict[str, Decimal]] = Field(None, description="거래 한도 설정")
