"""수수료 관련 스키마"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# 수수료 설정 관련 스키마
class FeeConfigBase(BaseModel):
    """수수료 설정 기본 스키마"""
    transaction_type: str = Field(..., description="거래 유형")
    base_fee: Decimal = Field(..., ge=0, description="기본 수수료")
    percentage_fee: Decimal = Field(..., ge=0, le=1, description="비율 수수료")
    min_fee: Decimal = Field(..., ge=0, description="최소 수수료")
    max_fee: Decimal = Field(..., ge=0, description="최대 수수료")
    partner_id: Optional[int] = Field(None, description="파트너사 ID")


class FeeConfigCreate(FeeConfigBase):
    """수수료 설정 생성 요청"""
    pass


class FeeConfigUpdate(BaseModel):
    """수수료 설정 업데이트 요청"""
    base_fee: Optional[Decimal] = Field(None, ge=0, description="기본 수수료")
    percentage_fee: Optional[Decimal] = Field(None, ge=0, le=1, description="비율 수수료")
    min_fee: Optional[Decimal] = Field(None, ge=0, description="최소 수수료")
    max_fee: Optional[Decimal] = Field(None, ge=0, description="최대 수수료")
    is_active: Optional[bool] = Field(None, description="활성 상태")


class FeeConfig(FeeConfigBase):
    """수수료 설정 응답"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 동적 수수료 규칙 관련 스키마
class DynamicFeeRuleBase(BaseModel):
    """동적 수수료 규칙 기본 스키마"""
    rule_name: str = Field(..., max_length=100, description="규칙 이름")
    transaction_type: str = Field(..., description="거래 유형")
    condition_type: str = Field(..., description="조건 유형")
    condition_value: Dict[str, Any] = Field(..., description="조건 설정")
    fee_multiplier: Decimal = Field(..., gt=0, description="수수료 배율")
    priority: int = Field(1, ge=1, le=10, description="우선순위")


class DynamicFeeRuleCreate(DynamicFeeRuleBase):
    """동적 수수료 규칙 생성 요청"""
    pass


class DynamicFeeRuleUpdate(BaseModel):
    """동적 수수료 규칙 업데이트 요청"""
    rule_name: Optional[str] = Field(None, max_length=100, description="규칙 이름")
    condition_value: Optional[Dict[str, Any]] = Field(None, description="조건 설정")
    fee_multiplier: Optional[Decimal] = Field(None, gt=0, description="수수료 배율")
    priority: Optional[int] = Field(None, ge=1, le=10, description="우선순위")
    is_active: Optional[bool] = Field(None, description="활성 상태")


class DynamicFeeRule(DynamicFeeRuleBase):
    """동적 수수료 규칙 응답"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 수수료 계산 관련 스키마
class FeeCalculationRequest(BaseModel):
    """수수료 계산 요청"""
    transaction_type: str = Field(..., description="거래 유형")
    amount: Decimal = Field(..., gt=0, description="거래 금액")
    partner_id: Optional[int] = Field(None, description="파트너사 ID")
    user_id: Optional[int] = Field(None, description="사용자 ID")


class FeeCalculationResult(BaseModel):
    """수수료 계산 결과"""
    base_fee: Decimal = Field(..., description="기본 수수료")
    percentage_fee: Decimal = Field(..., description="비율 수수료")
    dynamic_multiplier: Decimal = Field(..., description="동적 배율")
    final_fee: Decimal = Field(..., description="최종 수수료")
    applied_rules: List[str] = Field(..., description="적용된 규칙들")
    calculation_details: Dict[str, Any] = Field(..., description="계산 세부사항")


# 수수료 이력 관련 스키마
class FeeHistoryCreate(BaseModel):
    """수수료 변경 이력 생성 요청"""
    fee_config_id: int = Field(..., description="수수료 설정 ID")
    old_values: Dict[str, Any] = Field(..., description="이전 설정값")
    new_values: Dict[str, Any] = Field(..., description="새 설정값")
    change_reason: Optional[str] = Field(None, description="변경 사유")


class FeeHistory(BaseModel):
    """수수료 변경 이력 응답"""
    id: int
    fee_config_id: int
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    changed_by: int
    change_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# 수수료 통계 관련 스키마
class FeeRevenueStats(BaseModel):
    """수수료 매출 통계"""
    date: datetime
    partner_id: Optional[int]
    transaction_type: Optional[str]
    total_transactions: int = Field(..., description="총 거래 수")
    total_fee_collected: Decimal = Field(..., description="총 수수료 수집액")
    average_fee: Decimal = Field(..., description="평균 수수료")
    min_fee: Decimal = Field(..., description="최소 수수료")
    max_fee: Decimal = Field(..., description="최대 수수료")

    class Config:
        from_attributes = True


class PartnerFeeStats(BaseModel):
    """파트너별 수수료 통계"""
    partner_id: int
    partner_name: Optional[str]
    total_transactions: int
    total_fee_collected: Decimal
    average_fee: Decimal
    fee_percentage: Decimal = Field(..., description="전체 대비 수수료 비율")


class TotalRevenueStats(BaseModel):
    """전체 매출 통계"""
    total_transactions: int
    total_fee_collected: Decimal
    average_fee: Decimal
    partners_count: int
    top_partners: List[PartnerFeeStats]
    daily_revenue: List[FeeRevenueStats]


# 수수료 설정 변경 요청 스키마
class FeeConfigUpdateRequest(BaseModel):
    """수수료 설정 변경 요청"""
    config_updates: List[FeeConfigUpdate] = Field(..., description="수수료 설정 업데이트 목록")
    change_reason: str = Field(..., description="변경 사유")
    effective_date: Optional[datetime] = Field(None, description="적용 일시")


class BulkFeeUpdateResponse(BaseModel):
    """대량 수수료 업데이트 응답"""
    updated_count: int = Field(..., description="업데이트된 설정 수")
    failed_count: int = Field(..., description="실패한 설정 수")
    updated_configs: List[FeeConfig] = Field(..., description="업데이트된 설정들")
    errors: List[str] = Field(..., description="오류 메시지들")
