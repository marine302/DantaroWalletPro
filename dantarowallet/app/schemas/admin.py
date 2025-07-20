"""
관리자 패널 스키마 정의.
관리자 전용 API의 요청/응답 모델을 정의합니다.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# 시스템 통계 관련 스키마
class SystemStatsResponse(BaseModel):
    """시스템 전체 통계 응답"""

    model_config = ConfigDict(from_attributes=True)

    total_users: int = Field(description="총 사용자 수")
    active_users: int = Field(description="활성 사용자 수")
    total_wallets: int = Field(description="총 지갑 수")
    total_transactions: int = Field(description="총 거래 수")
    total_balance: Decimal = Field(description="시스템 총 잔고")
    daily_transactions: int = Field(description="일일 거래 수")
    monthly_volume: Decimal = Field(description="월간 거래량")


# 사용자 관리 관련 스키마
class UserListResponse(BaseModel):
    """사용자 목록 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    total_balance: Optional[Decimal] = None
    wallet_count: int = 0


class UserDetailResponse(BaseModel):
    """사용자 상세 정보 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    tron_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 통계 정보
    total_balance: Decimal = Decimal("0")
    wallet_count: int = 0
    transaction_count: int = 0
    last_transaction_date: Optional[datetime] = None
    last_login: Optional[datetime] = None
    total_transactions: int = 0
    total_volume: Decimal = Decimal("0")
    risk_score: int = 0
    risk_level: str = "LOW"


class UserUpdateRequest(BaseModel):
    """사용자 정보 수정 요청"""

    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None


# 거래 모니터링 관련 스키마
class TransactionMonitorResponse(BaseModel):
    """거래 모니터링 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_email: str
    transaction_type: str
    direction: str
    amount: Decimal
    asset: str
    status: str
    created_at: datetime
    tx_hash: Optional[str] = None
    reference_id: Optional[str] = None


class SuspiciousActivityResponse(BaseModel):
    """의심스러운 활동 응답"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_email: str
    activity_type: str
    risk_score: int
    description: str
    detected_at: datetime
    amount: Optional[Decimal] = None
    transaction_count: int = 0


# 시스템 설정 관련 스키마
class SystemConfigResponse(BaseModel):
    """시스템 설정 응답"""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    description: str
    is_sensitive: bool = False
    updated_at: datetime


class SystemConfigUpdateRequest(BaseModel):
    """시스템 설정 수정 요청"""

    value: str


# 로그 모니터링 관련 스키마
class LogEntryResponse(BaseModel):
    """로그 엔트리 응답"""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    level: str
    message: str
    logger_name: str
    request_id: Optional[str] = None
    user_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None


# 백업 관련 스키마
class BackupInfoResponse(BaseModel):
    """백업 정보 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    backup_type: str
    file_path: str
    file_size: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class BackupCreateRequest(BaseModel):
    """백업 생성 요청"""

    backup_type: str = Field(description="백업 타입: 'full', 'incremental', 'schema'")
    description: Optional[str] = None


# 페이지네이션 스키마
class PaginatedResponse(BaseModel):
    """페이지네이션 응답 베이스"""

    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class PaginatedUsersResponse(PaginatedResponse):
    """페이지네이션된 사용자 목록 응답"""

    items: List[UserListResponse]


class PaginatedTransactionsResponse(PaginatedResponse):
    """페이지네이션된 거래 목록 응답"""

    items: List[TransactionMonitorResponse]


class PaginatedLogsResponse(PaginatedResponse):
    """페이지네이션된 로그 목록 응답"""

    items: List[LogEntryResponse]


# 고급 분석(거래 패턴, 리스크 분석) 스키마
class UserRiskAnalysisResponse(BaseModel):
    """사용자별 리스크 분석 결과"""

    model_config = ConfigDict(from_attributes=True)
    user_id: int
    email: str
    risk_score: int
    risk_level: str
    main_reason: str
    recent_large_transactions: int = 0
    high_frequency_periods: int = 0
    last_activity: Optional[datetime] = None


class SystemRiskSummaryResponse(BaseModel):
    """시스템 전체 리스크 요약"""

    model_config = ConfigDict(from_attributes=True)
    high_risk_users: int
    medium_risk_users: int
    low_risk_users: int
    total_users: int
    updated_at: datetime
