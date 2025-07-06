"""파트너사 관련 스키마"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr


# 파트너 기본 스키마
class PartnerBase(BaseModel):
    """파트너 기본 스키마"""
    name: str = Field(..., max_length=100, description="파트너사명")
    display_name: Optional[str] = Field(None, max_length=100, description="표시명")
    domain: Optional[str] = Field(None, max_length=255, description="도메인")
    contact_email: EmailStr = Field(..., description="연락처 이메일")
    contact_phone: Optional[str] = Field(None, max_length=50, description="연락처 전화번호")
    business_type: str = Field(..., max_length=50, description="비즈니스 유형")
    commission_rate: Decimal = Field(0, ge=0, le=1, description="수수료율")
    
    # 구독 및 제한
    subscription_plan: str = Field("basic", description="구독 플랜")
    monthly_limit: Optional[Decimal] = Field(None, ge=0, description="월간 한도")
    
    # 설정
    settings: Dict[str, Any] = Field(default_factory=dict, description="파트너 설정")


class PartnerCreate(PartnerBase):
    """파트너 생성 요청"""
    pass


class PartnerUpdate(BaseModel):
    """파트너 업데이트 요청"""
    name: Optional[str] = Field(None, max_length=100, description="파트너사명")
    display_name: Optional[str] = Field(None, max_length=100, description="표시명")
    domain: Optional[str] = Field(None, max_length=255, description="도메인")
    contact_email: Optional[EmailStr] = Field(None, description="연락처 이메일")
    contact_phone: Optional[str] = Field(None, max_length=50, description="연락처 전화번호")
    business_type: Optional[str] = Field(None, max_length=50, description="비즈니스 유형")
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=1, description="수수료율")
    subscription_plan: Optional[str] = Field(None, description="구독 플랜")
    monthly_limit: Optional[Decimal] = Field(None, ge=0, description="월간 한도")
    settings: Optional[Dict[str, Any]] = Field(None, description="파트너 설정")


class PartnerResponse(PartnerBase):
    """파트너 응답"""
    id: str
    api_key: str
    status: str
    onboarding_status: str
    created_at: datetime
    updated_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    activated_at: Optional[datetime]
    suspended_at: Optional[datetime]

    class Config:
        from_attributes = True


class PartnerStats(BaseModel):
    """파트너 통계"""
    partner_id: str
    total_users: int = Field(0, description="총 사용자 수")
    total_wallets: int = Field(0, description="총 지갑 수")
    total_transactions: int = Field(0, description="총 거래 수")
    total_volume: Decimal = Field(Decimal("0.00"), description="총 거래량")
    total_fees: Decimal = Field(Decimal("0.00"), description="총 수수료")
    energy_used: int = Field(0, description="사용된 에너지")
    energy_remaining: int = Field(0, description="남은 에너지")
    success_rate: float = Field(100.0, description="성공률")
    last_active: Optional[datetime] = Field(None, description="마지막 활동")
    status: str = Field(..., description="파트너 상태")


# API 키 관련 스키마
class ApiKeyResponse(BaseModel):
    """API 키 응답"""
    api_key: str
    api_secret: str
    created_at: datetime


# 파트너 관련 상수들
class PartnerStatus:
    """파트너 상태"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class OnboardingStatus:
    """온보딩 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionPlan:
    """구독 플랜"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
