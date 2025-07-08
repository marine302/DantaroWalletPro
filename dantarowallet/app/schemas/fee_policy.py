"""파트너사 수수료 및 정책 관련 스키마 - Doc #26"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class FeeTypeEnum(str, Enum):
    """수수료 유형"""
    FLAT = "flat"
    PERCENTAGE = "percentage"
    TIERED = "tiered"
    DYNAMIC = "dynamic"


class WithdrawalPolicyEnum(str, Enum):
    """출금 정책"""
    REALTIME = "realtime"
    BATCH = "batch"
    HYBRID = "hybrid"
    MANUAL = "manual"


class EnergyPolicyEnum(str, Enum):
    """에너지 부족 대응 정책"""
    WAIT_QUEUE = "wait_queue"
    TRX_PAYMENT = "trx_payment"
    PRIORITY_QUEUE = "priority_queue"
    REJECT = "reject"


# === 수수료 정책 스키마 ===

class FeeTierCreate(BaseModel):
    """구간별 수수료 생성 요청"""
    min_amount: Decimal = Field(..., ge=0, description="최소 금액")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="최대 금액 (None=무제한)")
    fee_rate: Decimal = Field(..., ge=0, le=1, description="수수료율 (0-1)")
    fixed_fee: Decimal = Field(default=0, ge=0, description="고정 수수료")

    @validator('max_amount')
    def validate_max_amount(cls, v, values):
        if v is not None and 'min_amount' in values and v <= values['min_amount']:
            raise ValueError('최대 금액은 최소 금액보다 커야 합니다')
        return v


class FeeTierResponse(FeeTierCreate):
    """구간별 수수료 응답"""
    id: int
    fee_policy_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PartnerFeePolicyCreate(BaseModel):
    """파트너 수수료 정책 생성 요청"""
    fee_type: FeeTypeEnum = Field(default=FeeTypeEnum.PERCENTAGE, description="수수료 유형")
    base_fee_rate: Decimal = Field(default=0.001, ge=0, le=1, description="기본 수수료율")
    min_fee_amount: Decimal = Field(default=0.1, ge=0, description="최소 수수료")
    max_fee_amount: Optional[Decimal] = Field(None, ge=0, description="최대 수수료")
    withdrawal_fee_rate: Decimal = Field(default=0.001, ge=0, le=1, description="출금 수수료율")
    internal_transfer_fee_rate: Decimal = Field(default=0, ge=0, le=1, description="내부 이체 수수료율")
    vip_discount_rates: Optional[Dict[str, float]] = Field(None, description="VIP 등급별 할인율")
    promotion_active: bool = Field(default=False, description="프로모션 활성화")
    promotion_fee_rate: Optional[Decimal] = Field(None, ge=0, le=1, description="프로모션 수수료율")
    promotion_end_date: Optional[datetime] = Field(None, description="프로모션 종료일")
    platform_share_rate: Decimal = Field(default=0.3, ge=0, le=1, description="플랫폼 수수료 분배율")
    fee_tiers: Optional[List[FeeTierCreate]] = Field(None, description="구간별 수수료 (TIERED 타입인 경우)")


class PartnerFeePolicyUpdate(BaseModel):
    """파트너 수수료 정책 업데이트 요청"""
    fee_type: Optional[FeeTypeEnum] = None
    base_fee_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    min_fee_amount: Optional[Decimal] = Field(None, ge=0)
    max_fee_amount: Optional[Decimal] = Field(None, ge=0)
    withdrawal_fee_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    internal_transfer_fee_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    vip_discount_rates: Optional[Dict[str, float]] = None
    promotion_active: Optional[bool] = None
    promotion_fee_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    promotion_end_date: Optional[datetime] = None
    platform_share_rate: Optional[Decimal] = Field(None, ge=0, le=1)


class PartnerFeePolicyResponse(BaseModel):
    """파트너 수수료 정책 응답"""
    id: int
    partner_id: str
    fee_type: FeeTypeEnum
    base_fee_rate: Decimal
    min_fee_amount: Decimal
    max_fee_amount: Optional[Decimal]
    withdrawal_fee_rate: Decimal
    internal_transfer_fee_rate: Decimal
    vip_discount_rates: Optional[Dict[str, Any]]
    promotion_active: bool
    promotion_fee_rate: Optional[Decimal]
    promotion_end_date: Optional[datetime]
    platform_share_rate: Decimal
    fee_tiers: List[FeeTierResponse] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# === 출금 정책 스키마 ===

class BatchScheduleConfig(BaseModel):
    """일괄 처리 스케줄 설정"""
    enabled: bool = Field(default=True, description="스케줄 활성화")
    times: List[str] = Field(default=["09:00", "15:00", "21:00"], description="처리 시간 (HH:MM)")
    weekdays: List[int] = Field(default=[1,2,3,4,5,6,7], description="처리 요일 (1=월, 7=일)")
    timezone: str = Field(default="Asia/Seoul", description="시간대")


class PartnerWithdrawalPolicyCreate(BaseModel):
    """파트너 출금 정책 생성 요청"""
    policy_type: WithdrawalPolicyEnum = Field(default=WithdrawalPolicyEnum.HYBRID, description="출금 정책")
    realtime_enabled: bool = Field(default=True, description="실시간 출금 활성화")
    realtime_max_amount: Decimal = Field(default=1000, ge=0, description="실시간 최대 금액")
    auto_approve_enabled: bool = Field(default=False, description="자동 승인 활성화")
    auto_approve_max_amount: Decimal = Field(default=100, ge=0, description="자동 승인 최대 금액")
    batch_enabled: bool = Field(default=True, description="일괄 출금 활성화")
    batch_schedule: Optional[BatchScheduleConfig] = Field(None, description="일괄 처리 스케줄")
    batch_min_amount: Decimal = Field(default=10, ge=0, description="일괄 처리 최소 금액")
    daily_limit_per_user: Decimal = Field(default=10000, ge=0, description="사용자별 일일 한도")
    daily_limit_total: Decimal = Field(default=1000000, ge=0, description="전체 일일 한도")
    single_transaction_limit: Decimal = Field(default=5000, ge=0, description="단일 거래 한도")
    whitelist_required: bool = Field(default=False, description="화이트리스트 필수")
    whitelist_addresses: Optional[List[str]] = Field(None, description="화이트리스트 주소 목록")
    require_2fa: bool = Field(default=True, description="2FA 필수")
    confirmation_blocks: int = Field(default=19, ge=1, description="확인 블록 수")


class PartnerWithdrawalPolicyUpdate(BaseModel):
    """파트너 출금 정책 업데이트 요청"""
    policy_type: Optional[WithdrawalPolicyEnum] = None
    realtime_enabled: Optional[bool] = None
    realtime_max_amount: Optional[Decimal] = Field(None, ge=0)
    auto_approve_enabled: Optional[bool] = None
    auto_approve_max_amount: Optional[Decimal] = Field(None, ge=0)
    batch_enabled: Optional[bool] = None
    batch_schedule: Optional[BatchScheduleConfig] = None
    batch_min_amount: Optional[Decimal] = Field(None, ge=0)
    daily_limit_per_user: Optional[Decimal] = Field(None, ge=0)
    daily_limit_total: Optional[Decimal] = Field(None, ge=0)
    single_transaction_limit: Optional[Decimal] = Field(None, ge=0)
    whitelist_required: Optional[bool] = None
    whitelist_addresses: Optional[List[str]] = None
    require_2fa: Optional[bool] = None
    confirmation_blocks: Optional[int] = Field(None, ge=1)


class PartnerWithdrawalPolicyResponse(BaseModel):
    """파트너 출금 정책 응답"""
    id: int
    partner_id: str
    policy_type: WithdrawalPolicyEnum
    realtime_enabled: bool
    realtime_max_amount: Decimal
    auto_approve_enabled: bool
    auto_approve_max_amount: Decimal
    batch_enabled: bool
    batch_schedule: Optional[Dict[str, Any]]
    batch_min_amount: Decimal
    daily_limit_per_user: Decimal
    daily_limit_total: Decimal
    single_transaction_limit: Decimal
    whitelist_required: bool
    whitelist_addresses: Optional[List[str]]
    require_2fa: bool
    confirmation_blocks: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# === 에너지 정책 스키마 ===

class VipPriorityLevel(BaseModel):
    """VIP 우선순위 레벨 설정"""
    tier_name: str = Field(..., description="등급명")
    priority_score: int = Field(..., ge=1, le=10, description="우선순위 점수 (1-10)")
    queue_skip_enabled: bool = Field(default=False, description="대기열 건너뛰기 허용")


class PartnerEnergyPolicyCreate(BaseModel):
    """파트너 에너지 정책 생성 요청"""
    default_policy: EnergyPolicyEnum = Field(default=EnergyPolicyEnum.WAIT_QUEUE, description="기본 대응 정책")
    trx_payment_enabled: bool = Field(default=True, description="TRX 결제 활성화")
    trx_payment_markup: Decimal = Field(default=0.1, ge=0, le=1, description="TRX 결제 마크업")
    trx_payment_max_fee: Decimal = Field(default=20, ge=0, description="최대 TRX 수수료")
    queue_enabled: bool = Field(default=True, description="대기열 활성화")
    queue_max_wait_hours: int = Field(default=24, ge=1, description="최대 대기 시간")
    queue_notification_enabled: bool = Field(default=True, description="대기열 알림")
    priority_queue_enabled: bool = Field(default=True, description="우선순위 큐 활성화")
    vip_priority_levels: Optional[List[VipPriorityLevel]] = Field(None, description="VIP 등급별 우선순위")
    energy_saving_enabled: bool = Field(default=False, description="에너지 절약 모드")
    energy_saving_threshold: int = Field(default=20, ge=1, le=99, description="절약 모드 임계값 (%)")


class PartnerEnergyPolicyUpdate(BaseModel):
    """파트너 에너지 정책 업데이트 요청"""
    default_policy: Optional[EnergyPolicyEnum] = None
    trx_payment_enabled: Optional[bool] = None
    trx_payment_markup: Optional[Decimal] = Field(None, ge=0, le=1)
    trx_payment_max_fee: Optional[Decimal] = Field(None, ge=0)
    queue_enabled: Optional[bool] = None
    queue_max_wait_hours: Optional[int] = Field(None, ge=1)
    queue_notification_enabled: Optional[bool] = None
    priority_queue_enabled: Optional[bool] = None
    vip_priority_levels: Optional[List[VipPriorityLevel]] = None
    energy_saving_enabled: Optional[bool] = None
    energy_saving_threshold: Optional[int] = Field(None, ge=1, le=99)


class PartnerEnergyPolicyResponse(BaseModel):
    """파트너 에너지 정책 응답"""
    id: int
    partner_id: str
    default_policy: EnergyPolicyEnum
    trx_payment_enabled: bool
    trx_payment_markup: Decimal
    trx_payment_max_fee: Decimal
    queue_enabled: bool
    queue_max_wait_hours: int
    queue_notification_enabled: bool
    priority_queue_enabled: bool
    vip_priority_levels: Optional[List[Dict[str, Any]]]
    energy_saving_enabled: bool
    energy_saving_threshold: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# === 사용자 등급 스키마 ===

class UserTierCreate(BaseModel):
    """사용자 등급 생성 요청"""
    tier_name: str = Field(..., max_length=50, description="등급명")
    tier_level: int = Field(..., ge=1, description="등급 레벨")
    min_volume: Decimal = Field(default=0, ge=0, description="최소 거래량")
    fee_discount_rate: Decimal = Field(default=0, ge=0, le=1, description="수수료 할인율")
    withdrawal_limit_multiplier: Decimal = Field(default=1.0, ge=0.1, description="출금 한도 배수")
    benefits: Optional[Dict[str, Any]] = Field(None, description="등급별 혜택")
    upgrade_conditions: Optional[Dict[str, Any]] = Field(None, description="승급 조건")


class UserTierUpdate(BaseModel):
    """사용자 등급 업데이트 요청"""
    tier_name: Optional[str] = Field(None, max_length=50)
    tier_level: Optional[int] = Field(None, ge=1)
    min_volume: Optional[Decimal] = Field(None, ge=0)
    fee_discount_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    withdrawal_limit_multiplier: Optional[Decimal] = Field(None, ge=0.1)
    benefits: Optional[Dict[str, Any]] = None
    upgrade_conditions: Optional[Dict[str, Any]] = None


class UserTierResponse(BaseModel):
    """사용자 등급 응답"""
    id: int
    partner_id: str
    tier_name: str
    tier_level: int
    min_volume: Decimal
    fee_discount_rate: Decimal
    withdrawal_limit_multiplier: Decimal
    benefits: Optional[Dict[str, Any]]
    upgrade_conditions: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# === 수수료 계산 관련 스키마 ===

class FeeCalculationRequest(BaseModel):
    """수수료 계산 요청"""
    amount: Decimal = Field(..., gt=0, description="거래 금액")
    transaction_type: str = Field(..., description="거래 유형 (withdrawal, internal_transfer 등)")
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        allowed_types = ['withdrawal', 'internal_transfer', 'external_transfer']
        if v not in allowed_types:
            raise ValueError(f'허용된 거래 유형: {allowed_types}')
        return v


class FeeCalculationResponse(BaseModel):
    """수수료 계산 응답"""
    original_amount: Decimal
    calculated_fee: Decimal
    discount_amount: Decimal = Decimal('0')
    final_fee: Decimal
    effective_rate: Decimal
    calculation_method: str
    user_tier_applied: Optional[str] = None
    metadata: Dict[str, Any] = {}


class PartnerPolicyCalculationLogResponse(BaseModel):
    """파트너 정책 수수료 계산 로그 응답"""
    id: int
    partner_id: str
    user_id: Optional[int]
    calculation_type: str
    request_data: Dict[str, Any]
    result_data: Dict[str, Any]
    calculated_at: datetime
    admin_id: Optional[int] = None

    class Config:
        from_attributes = True


# === 통합 정책 관리 스키마 ===

class PartnerPolicyOverview(BaseModel):
    """파트너 정책 전체 현황"""
    partner_id: str
    partner_name: str
    fee_policy: Optional[PartnerFeePolicyResponse]
    withdrawal_policy: Optional[PartnerWithdrawalPolicyResponse]
    energy_policy: Optional[PartnerEnergyPolicyResponse]
    user_tiers: List[UserTierResponse]
    is_configured: bool
    last_updated: Optional[datetime]


class PolicyBulkUpdateRequest(BaseModel):
    """정책 일괄 업데이트 요청"""
    fee_policy: Optional[PartnerFeePolicyUpdate] = None
    withdrawal_policy: Optional[PartnerWithdrawalPolicyUpdate] = None
    energy_policy: Optional[PartnerEnergyPolicyUpdate] = None


class MessageResponse(BaseModel):
    """일반 메시지 응답"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
