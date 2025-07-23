"""에너지 관련 스키마 - Doc #25 업데이트"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Doc #25: 파트너별 에너지 풀 고급 관리 스키마


class EnergyPoolResponse(BaseModel):
    """에너지 풀 상태 응답 (Doc #25)"""

    partner_id: int
    wallet_address: str
    status: str
    total_energy: int
    available_energy: int
    used_energy: int
    energy_percentage: float
    total_bandwidth: int
    available_bandwidth: int
    frozen_trx_total: float
    frozen_trx_energy: float
    frozen_trx_bandwidth: float
    daily_average_usage: float
    peak_usage_hour: Optional[int]
    depletion_estimated_at: Optional[datetime]
    last_checked_at: Optional[datetime]
    warning_threshold: int
    critical_threshold: int

    class Config:
        from_attributes = True


class EnergyAlertResponse(BaseModel):
    """에너지 알림 응답 (Doc #25)"""

    id: int
    type: str
    severity: str
    title: str
    message: str
    energy_percentage: Optional[int]
    available_energy: Optional[int]
    estimated_hours_remaining: Optional[int]
    sent_at: datetime
    acknowledged: bool
    acknowledged_at: Optional[datetime]

    class Config:
        from_attributes = True


class EnergyUsageLogResponse(BaseModel):
    """에너지 사용 로그 응답 (Doc #25)"""

    id: int
    transaction_type: str
    transaction_hash: Optional[str]
    energy_consumed: int
    bandwidth_consumed: int
    energy_unit_price: Optional[float]
    total_cost: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class EnergyMonitoringResponse(BaseModel):
    """에너지 모니터링 응답 (Doc #25)"""

    success: bool
    data: Dict[str, Any] = Field(description="모니터링 데이터")
    timestamp: datetime = Field(description="조회 시간")

    class Config:
        from_attributes = True


class EnergyAnalyticsResponse(BaseModel):
    """에너지 분석 응답 (Doc #25)"""

    success: bool
    analytics: Dict[str, Any] = Field(description="분석 데이터")
    generated_at: datetime = Field(description="생성 시간")

    class Config:
        from_attributes = True


class EnergyAlertListResponse(BaseModel):
    """에너지 알림 목록 응답 (Doc #25)"""

    success: bool
    alerts: List[Dict[str, Any]] = Field(description="알림 목록")
    total_count: int = Field(description="총 알림 수")

    class Config:
        from_attributes = True


class GlobalEnergyAnalyticsResponse(BaseModel):
    """전체 에너지 분석 응답 (Doc #25)"""

    success: bool
    global_analytics: Dict[str, Any] = Field(description="전체 분석 데이터")
    generated_at: datetime = Field(description="생성 시간")

    class Config:
        from_attributes = True


class EnergyDashboardResponse(BaseModel):
    """에너지 대시보드 응답 (Doc #25)"""

    success: bool
    energy_pool: Dict[str, Any] = Field(description="에너지 풀 정보")
    recent_alerts: List[Dict[str, Any]] = Field(description="최근 알림 목록")
    usage_statistics: Dict[str, Any] = Field(description="사용 통계")

    class Config:
        from_attributes = True


class TrendAnalysis(BaseModel):
    """트렌드 분석 (Doc #25)"""

    trend: str = Field(description="트렌드 방향: increasing, decreasing, stable")
    change_percentage: float = Field(description="변화율 (%)")
    first_period_avg: float = Field(description="첫 번째 기간 평균")
    second_period_avg: float = Field(description="두 번째 기간 평균")


class UsagePatterns(BaseModel):
    """사용 패턴 (Doc #25)"""

    daily_usage: Dict[str, Any] = Field(description="일별 사용 패턴")
    hourly_usage: Dict[str, Any] = Field(description="시간별 사용 패턴")
    trend_analysis: TrendAnalysis = Field(description="트렌드 분석")


class EnergyPatternAnalysisResponse(BaseModel):
    """에너지 패턴 분석 응답 (Doc #25)"""

    success: bool
    partner_id: int
    analysis_period: str
    patterns: UsagePatterns

    class Config:
        from_attributes = True


class EnergyThresholdUpdateRequest(BaseModel):
    """에너지 임계값 업데이트 요청 (Doc #25)"""

    warning_threshold: int = Field(ge=1, le=99, description="경고 임계값 (1-99%)")
    critical_threshold: int = Field(ge=1, le=99, description="위험 임계값 (1-99%)")

    class Config:
        validate_assignment = True


class EnergyOverviewResponse(BaseModel):
    """에너지 전체 현황 응답 (Doc #25)"""

    success: bool
    overview: Dict[str, Any] = Field(description="전체 현황")

    class Config:
        from_attributes = True


class AlertAcknowledgeResponse(BaseModel):
    """알림 확인 응답 (Doc #25)"""

    success: bool
    message: str

    class Config:
        from_attributes = True


# 기존 에너지 풀 스키마 (하위 호환성 유지)
class CreateEnergyPoolRequest(BaseModel):
    pool_name: str = Field(..., description="에너지 풀 이름")
    owner_private_key: str = Field(..., description="소유자 프라이빗 키")
    initial_trx_amount: Decimal = Field(..., description="초기 동결할 TRX 금액")


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
