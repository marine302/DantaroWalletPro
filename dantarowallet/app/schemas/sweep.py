"""
Sweep 자동화 관련 Pydantic 스키마
입금 Sweep 자동화 시스템의 요청/응답 스키마를 정의합니다.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class SweepType(str, Enum):
    """Sweep 유형"""
    AUTO = "auto"
    MANUAL = "manual"
    EMERGENCY = "emergency"


class SweepStatus(str, Enum):
    """Sweep 상태"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class QueueType(str, Enum):
    """큐 유형"""
    NORMAL = "normal"
    PRIORITY = "priority"
    EMERGENCY = "emergency"


class QueueStatus(str, Enum):
    """큐 상태"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===== HD Wallet Schemas =====

class HDWalletMasterBase(BaseModel):
    """HD Wallet 마스터 기본 스키마"""
    partner_id: str
    derivation_path: str = "m/44'/195'/0'/0"
    encryption_method: str = "AES-256-GCM"


class HDWalletMasterCreate(HDWalletMasterBase):
    """HD Wallet 마스터 생성 스키마"""
    pass


class HDWalletMasterResponse(HDWalletMasterBase):
    """HD Wallet 마스터 응답 스키마"""
    id: int
    public_key: str
    collection_address: str  # 추가
    last_index: int
    key_version: int
    total_addresses_generated: int
    total_sweep_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ===== User Deposit Address Schemas =====

class UserDepositAddressBase(BaseModel):
    """사용자 입금 주소 기본 스키마"""
    user_id: int
    is_active: bool = True
    is_monitored: bool = True
    min_sweep_amount: Optional[Decimal] = None
    priority_level: int = Field(default=1, ge=1, le=10)


class UserDepositAddressCreate(UserDepositAddressBase):
    """사용자 입금 주소 생성 스키마"""
    partner_id: str


class UserDepositAddressUpdate(BaseModel):
    """사용자 입금 주소 업데이트 스키마"""
    is_active: Optional[bool] = None
    is_monitored: Optional[bool] = None
    min_sweep_amount: Optional[Decimal] = None
    priority_level: Optional[int] = Field(None, ge=1, le=10)


class UserDepositAddressResponse(UserDepositAddressBase):
    """사용자 입금 주소 응답 스키마"""
    id: int
    address: str
    derivation_index: int
    total_received: Decimal
    total_swept: Decimal
    last_deposit_at: Optional[datetime]
    last_sweep_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ===== Sweep Configuration Schemas =====

class SweepConfigurationBase(BaseModel):
    """Sweep 설정 기본 스키마"""
    destination_wallet_id: int
    is_enabled: bool = True
    auto_sweep_enabled: bool = True
    min_sweep_amount: Decimal = Field(default=Decimal("10"), gt=0)
    max_sweep_amount: Optional[Decimal] = Field(None, gt=0)
    sweep_interval_minutes: int = Field(default=60, ge=1, le=1440)
    immediate_threshold: Decimal = Field(default=Decimal("1000"), gt=0)
    daily_sweep_time: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    max_gas_price_sun: Decimal = Field(default=Decimal("1000"), gt=0)
    gas_optimization_enabled: bool = True
    gas_price_multiplier: Decimal = Field(default=Decimal("1.1"), ge=1, le=3)
    batch_enabled: bool = True
    max_batch_size: int = Field(default=20, ge=1, le=100)
    batch_delay_seconds: int = Field(default=5, ge=0, le=60)
    daily_sweep_limit: Optional[Decimal] = Field(None, gt=0)
    monthly_sweep_limit: Optional[Decimal] = Field(None, gt=0)
    consecutive_failure_limit: int = Field(default=3, ge=1, le=10)
    notification_enabled: bool = True
    notification_channels: Optional[Dict[str, Any]] = None
    success_notification: bool = False
    failure_notification: bool = True


class SweepConfigurationCreate(SweepConfigurationBase):
    """Sweep 설정 생성 스키마"""
    partner_id: str


class SweepConfigurationUpdate(BaseModel):
    """Sweep 설정 업데이트 스키마"""
    destination_wallet_id: Optional[int] = None
    is_enabled: Optional[bool] = None
    auto_sweep_enabled: Optional[bool] = None
    min_sweep_amount: Optional[Decimal] = Field(None, gt=0)
    max_sweep_amount: Optional[Decimal] = Field(None, gt=0)
    sweep_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    immediate_threshold: Optional[Decimal] = Field(None, gt=0)
    daily_sweep_time: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    max_gas_price_sun: Optional[Decimal] = Field(None, gt=0)
    gas_optimization_enabled: Optional[bool] = None
    gas_price_multiplier: Optional[Decimal] = Field(None, ge=1, le=3)
    batch_enabled: Optional[bool] = None
    max_batch_size: Optional[int] = Field(None, ge=1, le=100)
    batch_delay_seconds: Optional[int] = Field(None, ge=0, le=60)
    daily_sweep_limit: Optional[Decimal] = Field(None, gt=0)
    monthly_sweep_limit: Optional[Decimal] = Field(None, gt=0)
    consecutive_failure_limit: Optional[int] = Field(None, ge=1, le=10)
    notification_enabled: Optional[bool] = None
    notification_channels: Optional[Dict[str, Any]] = None
    success_notification: Optional[bool] = None
    failure_notification: Optional[bool] = None


class SweepConfigurationResponse(SweepConfigurationBase):
    """Sweep 설정 응답 스키마"""
    id: int
    partner_id: str
    last_sweep_at: Optional[datetime]
    total_sweeps: int
    total_sweep_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ===== Sweep Log Schemas =====

class SweepLogBase(BaseModel):
    """Sweep 로그 기본 스키마"""
    sweep_type: SweepType = SweepType.AUTO
    sweep_amount: Decimal = Field(gt=0)
    from_address: str = Field(min_length=34, max_length=42)
    to_address: str = Field(min_length=34, max_length=42)
    priority: int = Field(default=1, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)


class SweepLogCreate(SweepLogBase):
    """Sweep 로그 생성 스키마"""
    configuration_id: int
    deposit_address_id: int
    balance_before: Optional[Decimal] = None
    gas_limit: Optional[Decimal] = None
    gas_price: Optional[Decimal] = None


class SweepLogUpdate(BaseModel):
    """Sweep 로그 업데이트 스키마"""
    tx_hash: Optional[str] = Field(None, min_length=66, max_length=66)
    balance_after: Optional[Decimal] = None
    gas_used: Optional[Decimal] = None
    gas_fee_trx: Optional[Decimal] = None
    status: Optional[SweepStatus] = None
    error_message: Optional[str] = Field(None, max_length=1000)
    error_code: Optional[str] = Field(None, max_length=50)
    confirmed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class SweepLogResponse(SweepLogBase):
    """Sweep 로그 응답 스키마"""
    id: int
    configuration_id: int
    deposit_address_id: int
    balance_before: Optional[Decimal]
    balance_after: Optional[Decimal]
    tx_hash: Optional[str]
    gas_limit: Optional[Decimal]
    gas_used: Optional[Decimal]
    gas_price: Optional[Decimal]
    gas_fee_trx: Optional[Decimal]
    status: SweepStatus
    error_message: Optional[str]
    error_code: Optional[str]
    retry_count: int
    max_retries: int
    batch_id: Optional[str]
    initiated_at: datetime
    confirmed_at: Optional[datetime]
    failed_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ===== Sweep Queue Schemas =====

class SweepQueueBase(BaseModel):
    """Sweep 큐 기본 스키마"""
    queue_type: QueueType = QueueType.NORMAL
    priority: int = Field(default=1, ge=1, le=10)
    expected_amount: Optional[Decimal] = Field(None, gt=0)
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=200)
    queue_metadata: Optional[Dict[str, Any]] = None


class SweepQueueCreate(SweepQueueBase):
    """Sweep 큐 생성 스키마"""
    deposit_address_id: int


class SweepQueueUpdate(BaseModel):
    """Sweep 큐 업데이트 스키마"""
    queue_type: Optional[QueueType] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[QueueStatus] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=200)
    queue_metadata: Optional[Dict[str, Any]] = None


class SweepQueueResponse(SweepQueueBase):
    """Sweep 큐 응답 스키마"""
    id: int
    deposit_address_id: int
    status: QueueStatus
    attempts: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ===== Manual Sweep Schemas =====

class ManualSweepRequest(BaseModel):
    """수동 Sweep 요청 스키마"""
    address: str = Field(min_length=34, max_length=34, description="TRON 주소")
    amount: Optional[Decimal] = Field(None, ge=0, description="Sweep할 금액 (지정하지 않으면 전액)")
    force: bool = Field(False, description="강제 실행 여부")
    gas_price_multiplier: Optional[Decimal] = Field(None, ge=1, le=3)
    notes: Optional[str] = Field(None, max_length=500)


class ManualSweepResponse(BaseModel):
    """수동 Sweep 응답 스키마"""
    success: bool
    message: str
    queued_addresses: List[int]
    failed_addresses: List[Dict[str, Any]]
    total_expected_amount: Decimal


# ===== Emergency Sweep Schemas =====

class EmergencySweepRequest(BaseModel):
    """긴급 Sweep 요청 스키마"""
    addresses: List[str] = Field(description="긴급 Sweep할 주소 목록")
    reason: str = Field(min_length=10, max_length=200)
    authorized_by: str = Field(min_length=1, max_length=100)
    override_limits: bool = False
    
    @validator('addresses')
    def validate_addresses(cls, v):
        if len(v) < 1 or len(v) > 10:
            raise ValueError('긴급 Sweep 주소는 1-10개 사이여야 합니다')
        return v


class EmergencySweepResponse(BaseModel):
    """긴급 Sweep 응답 스키마"""
    success: bool
    message: str
    emergency_sweep_id: str
    processed_addresses: List[int]
    total_amount: Decimal
    estimated_completion: datetime


# ===== Statistics and Analytics Schemas =====

class SweepStatistics(BaseModel):
    """Sweep 통계 스키마"""
    total_addresses: int
    active_addresses: int
    total_sweep_amount: Decimal
    successful_sweeps: int
    failed_sweeps: int
    success_rate: float
    average_amount: Decimal
    last_24h_sweeps: int
    last_24h_amount: Decimal
    pending_sweeps: int
    queue_length: int


class SweepAnalytics(BaseModel):
    """Sweep 분석 스키마"""
    partner_id: str
    date_range: str
    statistics: SweepStatistics
    gas_analysis: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]


# ===== Batch Operation Schemas =====

class BatchSweepRequest(BaseModel):
    """배치 Sweep 요청 스키마"""
    addresses: List[str] = Field(description="Sweep할 주소 목록")
    force: bool = Field(False, description="강제 실행 여부")
    priority: str = Field("normal", description="우선순위 (normal, high, emergency)")
    filter_criteria: Optional[Dict[str, Any]] = Field(None, description="필터 조건")
    max_addresses: int = Field(default=20, ge=1, le=100)
    min_amount: Optional[Decimal] = Field(None, gt=0)
    
    @validator('addresses')
    def validate_addresses(cls, v):
        if len(v) < 1 or len(v) > 50:
            raise ValueError('주소 개수는 1-50개 사이여야 합니다')
        return v


class BatchSweepResponse(BaseModel):
    """배치 Sweep 응답 스키마"""
    batch_id: str
    total_addresses: int
    total_amount: Decimal
    estimated_gas_cost: Decimal
    estimated_completion: datetime
