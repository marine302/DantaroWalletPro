"""에너지 관련 스키마"""
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

# 에너지 풀 생성 요청
class CreateEnergyPoolRequest(BaseModel):
    pool_name: str = Field(..., description="에너지 풀 이름")
    owner_private_key: str = Field(..., description="소유자 프라이빗 키")
    initial_trx_amount: Decimal = Field(..., description="초기 동결할 TRX 금액")

class EnergyPoolResponse(BaseModel):
    id: int
    pool_name: str
    owner_address: str
    frozen_trx: Decimal
    total_energy: int
    available_energy: int
    used_energy: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class EnergyPoolStatusResponse(BaseModel):
    pool_id: int
    status: str
    total_energy: int
    available_energy: int
    used_energy: int
    usage_percentage: float
    frozen_trx: float
    auto_refill: bool
    last_checked: str
    usage_trend: Dict  # 7일간 사용 추이
    estimated_depletion: Optional[str]  # 예상 소진 시간
    recommendations: List[str]  # 추천 조치사항

class EnergyUsageLogResponse(BaseModel):
    id: int
    transaction_id: int
    energy_consumed: int
    transaction_type: str
    user_id: int
    energy_price: Decimal
    actual_cost: Decimal
    used_at: datetime
    
    class Config:
        from_attributes = True

class EnergyUsageStatsResponse(BaseModel):
    period: Dict[str, str]
    daily_usage: List[Dict]
    by_type: List[Dict]
    hourly_pattern: List[Dict]
    summary: Dict

class EnergySimulationRequest(BaseModel):
    transaction_count: int
    transaction_types: List[str]
    time_period_hours: int = 24

class EnergySimulationResponse(BaseModel):
    total_energy_required: int
    estimated_cost_trx: float
    estimated_cost_usd: float
    current_pool_capacity: float
    can_handle: bool
    shortage_amount: Optional[int]
    recommendations: List[str]

class AutoManagementSettings(BaseModel):
    enabled: bool
    refill_amount: Decimal = Field(..., ge=1000)
    trigger_percentage: int = Field(..., ge=5, le=50)

class EnergyPriceHistoryResponse(BaseModel):
    id: int
    trx_price_usd: Decimal
    energy_price_trx: Decimal
    energy_price_usd: Decimal
    market_demand: str
    network_congestion: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str

# 기존 에너지 관련 스키마 (하위 호환성)
class EnergyPoolStatus(BaseModel):
    """에너지 풀 상태 응답 (기존 호환성용)"""
    total_energy: int = Field(..., description="총 에너지량")
    available_energy: int = Field(..., description="사용 가능한 에너지")
    reserved_energy: int = Field(..., description="예약된 에너지")
    allocated_energy: int = Field(0, description="파트너에게 할당된 에너지")
    daily_consumption: int = Field(..., description="일일 소모량")
    alert_threshold: int = Field(..., description="알림 임계값")
    critical_threshold: int = Field(..., description="위험 임계값")
    is_sufficient: bool = Field(..., description="에너지 충분 여부")
    partner_count: int = Field(0, description="활성 파트너 수")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")

class EnergyQueueCreate(BaseModel):
    """에너지 대기열 생성 요청"""
    transaction_type: str = Field(..., description="거래 유형")

# 에너지 알림 관련 스키마
class EnergyAlert(BaseModel):
    """에너지 알림"""
    alert_type: str
    message: str
    current_energy: int
    threshold: int
    partner_id: Optional[str] = None
    created_at: datetime

class CreateEnergyAlert(BaseModel):
    """에너지 알림 생성 요청"""
    alert_type: str = Field(..., description="알림 유형")
    title: str = Field(..., max_length=200, description="알림 제목")
    message: Optional[str] = Field(None, description="알림 내용")
    severity: str = Field("info", description="심각도")

# 긴급 출금 관련 스키마
class EmergencyWithdrawalCreate(BaseModel):
    """긴급 출금 생성 요청"""
    to_address: str = Field(..., description="목적지 주소")
    amount: Decimal = Field(..., gt=0, description="출금 금액")
    fee_tier: str = Field("high", description="수수료 등급")
    reason: Optional[str] = Field(None, description="긴급 출금 사유")

class EmergencyWithdrawalResponse(BaseModel):
    """긴급 출금 응답"""
    transaction_id: str = Field(..., description="거래 ID")
    status: str = Field(..., description="거래 상태")
    estimated_confirmation_time: int = Field(..., description="예상 확인 시간(분)")
    fee_amount: Decimal = Field(..., description="수수료")
    message: str = Field(..., description="상태 메시지")

# 슈퍼 어드민용 추가 스키마
class EnergyUsage(BaseModel):
    """파트너 에너지 사용량"""
    partner_id: str
    current_balance: int
    daily_usage: int
    monthly_usage: int
    avg_daily_usage: int
    usage_efficiency: float
    last_usage: Optional[datetime] = None

class EnergyHistory(BaseModel):
    """에너지 사용 이력"""
    id: str
    partner_id: str
    partner_name: str
    transaction_type: str
    energy_amount: int
    balance_before: int
    balance_after: int
    transaction_hash: str
    created_at: datetime

class EnergyAllocation(BaseModel):
    """에너지 할당"""
    partner_id: str
    partner_name: str
    allocated_amount: int
    current_balance: int
    allocation_date: datetime
