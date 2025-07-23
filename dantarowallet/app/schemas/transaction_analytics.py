"""
트랜잭션 분석 및 모니터링 스키마
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.transaction import (
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction_analytics import AlertLevel, AlertType


class TransactionAnalyticsFilter(BaseModel):
    """트랜잭션 분석 필터"""

    user_id: Optional[int] = None
    asset: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    direction: Optional[TransactionDirection] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=1000)


class TransactionStats(BaseModel):
    """트랜잭션 통계"""

    total_count: int
    total_volume: Decimal
    successful_count: int
    successful_volume: Decimal
    failed_count: int
    pending_count: int
    average_amount: Decimal
    total_fees: Decimal


class AssetStats(BaseModel):
    """자산별 통계"""

    asset: str
    transaction_count: int
    total_volume: Decimal
    deposits_count: int
    deposits_volume: Decimal
    withdrawals_count: int
    withdrawals_volume: Decimal
    total_fees: Decimal


class DailyStats(BaseModel):
    """일별 통계"""

    date: date
    transaction_count: int
    total_volume: Decimal
    deposits_count: int
    deposits_volume: Decimal
    withdrawals_count: int
    withdrawals_volume: Decimal


class TransactionAnalyticsResponse(BaseModel):
    """트랜잭션 분석 응답"""

    period: str
    start_date: datetime
    end_date: datetime
    overall_stats: TransactionStats
    asset_breakdown: List[AssetStats]
    daily_breakdown: List[DailyStats]
    top_users: List[Dict[str, Any]]


class AlertRequest(BaseModel):
    """알림 생성 요청"""

    user_id: Optional[int] = None
    transaction_id: Optional[int] = None
    alert_type: str
    level: AlertLevel
    title: str
    description: str
    alert_data: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    """알림 응답"""

    id: int
    user_id: Optional[int]
    transaction_id: Optional[int]
    alert_type: str
    level: str
    title: str
    description: str
    is_resolved: bool
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    created_at: datetime
    alert_data: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class AlertResolveRequest(BaseModel):
    """알림 해결 요청"""

    resolution_notes: str


class SuspiciousPatternAlert(BaseModel):
    """의심스러운 패턴 알림 데이터"""

    pattern_type: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any]
    recommendations: List[str]


class TransactionMonitoringConfig(BaseModel):
    """트랜잭션 모니터링 설정"""

    # 금액 임계값
    large_transaction_threshold_usd: Decimal = Field(default=Decimal("10000"))
    suspicious_amount_multiplier: float = Field(default=5.0, ge=1.0)

    # 빈도 임계값
    max_transactions_per_hour: int = Field(default=10, ge=1)
    max_transactions_per_day: int = Field(default=50, ge=1)

    # 패턴 감지 설정
    enable_pattern_detection: bool = True
    pattern_analysis_window_hours: int = Field(default=24, ge=1)
    minimum_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # 알림 설정
    enable_real_time_alerts: bool = True
    alert_notification_channels: List[str] = ["database", "log"]


class UserTransactionProfile(BaseModel):
    """사용자 트랜잭션 프로필"""

    user_id: int
    total_transactions: int
    total_volume_usd: Decimal
    avg_transaction_amount: Decimal  # 스키마와 서비스 일치시키기
    most_used_asset: str  # 스키마와 서비스 일치시키기
    transaction_frequency: str  # 스키마와 서비스 일치시키기
    risk_score: float = Field(ge=0.0, le=1.0)
    last_transaction_date: Optional[datetime]  # 스키마와 서비스 일치시키기

    # 간단화된 통계
    preferred_transaction_hours: List[int] = []  # 기본값 제공
    monthly_volume_trend: List[Decimal] = []  # 기본값 제공

    model_config = ConfigDict(from_attributes=True)


class TransactionTrendAnalysis(BaseModel):
    """트랜잭션 트렌드 분석"""

    period: str
    asset: Optional[str] = None
    trend_direction: str  # "increasing", "decreasing", "stable"
    growth_rate: float  # 전 기간 대비 증가율
    daily_volume_trend: List[Decimal] = []  # 기본값 제공
    peak_hours: List[int] = []  # 가장 활발한 시간대, 기본값 제공
    seasonal_patterns: List[Dict[str, Any]] = []  # 기본값 제공, Dict가 아닌 List로 수정
    prediction_next_7_days: List[Decimal] = []  # 기본값 제공


class RealTimeTransactionMetrics(BaseModel):
    """실시간 트랜잭션 메트릭"""

    current_tps: float  # Transactions Per Second
    current_volume_per_minute: Decimal
    active_users_last_hour: int
    pending_transactions: int
    failed_transaction_rate: float
    average_processing_time_seconds: float
    system_health_score: float = Field(ge=0.0, le=1.0)


class TransactionSearchRequest(BaseModel):
    """트랜잭션 검색 요청"""

    query: Optional[str] = None  # 자유 텍스트 검색
    user_email: Optional[str] = None
    reference_id: Optional[str] = None
    tx_hash: Optional[str] = None
    amount_range: Optional[tuple[Decimal, Decimal]] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    filters: Optional[TransactionAnalyticsFilter] = None


class TransactionExportRequest(BaseModel):
    """트랜잭션 내보내기 요청"""

    filters: TransactionAnalyticsFilter
    format: str = Field(default="csv", pattern="^(csv|xlsx|json)$")
    include_user_details: bool = False
    include_analytics: bool = False
