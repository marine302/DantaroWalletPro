"""에너지 관련 스키마"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

# 에너지 풀 관련 스키마
class EnergyPoolStatus(BaseModel):
    """에너지 풀 상태 응답"""
    total_energy: int = Field(..., description="총 에너지량")
    available_energy: int = Field(..., description="사용 가능한 에너지")
    reserved_energy: int = Field(..., description="예약된 에너지")
    daily_consumption: int = Field(..., description="일일 소모량")
    energy_sufficient: bool = Field(..., description="에너지 충분 여부")
    alert_threshold: int = Field(..., description="알림 임계값")
    is_emergency_mode: bool = Field(..., description="긴급 모드 여부")
    last_recharge_at: Optional[datetime] = Field(None, description="마지막 충전 시간")

class EnergyRechargeRequest(BaseModel):
    """에너지 충전 요청"""
    amount: int = Field(..., gt=0, description="충전할 에너지량")
    reason: Optional[str] = Field(None, description="충전 사유")

# 에너지 거래 관련 스키마
class EnergyTransaction(BaseModel):
    """에너지 거래 내역"""
    id: int
    transaction_type: str = Field(..., description="거래 유형")
    energy_amount: int = Field(..., description="사용된 에너지량")
    transaction_id: Optional[str] = Field(None, description="연관된 거래 ID")
    user_id: Optional[int] = Field(None, description="사용자 ID")
    status: str = Field(..., description="상태")
    created_at: datetime

    class Config:
        from_attributes = True

class EnergyUsageStats(BaseModel):
    """에너지 사용 통계"""
    total_used_today: int = Field(..., description="오늘 사용된 총 에너지")
    average_per_transaction: float = Field(..., description="거래당 평균 에너지")
    peak_hour_usage: int = Field(..., description="피크 시간 사용량")
    transactions_count: int = Field(..., description="총 거래 수")

# 에너지 대기열 관련 스키마
class EnergyQueueCreate(BaseModel):
    """에너지 대기열 생성 요청"""
    transaction_type: str = Field(..., description="거래 유형")
    amount: Decimal = Field(..., gt=0, description="거래 금액")
    to_address: str = Field(..., description="목적지 주소")
    estimated_energy: int = Field(..., gt=0, description="예상 에너지 소모량")
    priority: int = Field(1, ge=1, le=10, description="우선순위")

class EnergyQueue(BaseModel):
    """에너지 대기열 응답"""
    id: int
    user_id: int
    transaction_type: str
    amount: Decimal
    to_address: Optional[str]
    estimated_energy: int
    priority: int
    status: str
    estimated_wait_time: Optional[int] = Field(None, description="예상 대기 시간(분)")
    queue_position: Optional[int] = Field(None, description="대기열 순서")
    created_at: datetime

    class Config:
        from_attributes = True

class QueueStatus(BaseModel):
    """대기열 상태 응답"""
    queue_position: int = Field(..., description="현재 대기열 순서")
    estimated_wait_time: int = Field(..., description="예상 대기 시간(분)")
    total_queue_size: int = Field(..., description="전체 대기열 크기")
    current_energy_status: EnergyPoolStatus

# 에너지 알림 관련 스키마
class EnergyAlert(BaseModel):
    """에너지 알림"""
    id: int
    alert_type: str = Field(..., description="알림 유형")
    title: str = Field(..., description="알림 제목")
    message: Optional[str] = Field(None, description="알림 내용")
    severity: str = Field(..., description="심각도")
    is_active: bool = Field(..., description="활성 상태")
    created_at: datetime
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")

    class Config:
        from_attributes = True

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
