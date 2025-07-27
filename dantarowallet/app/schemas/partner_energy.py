"""
파트너사 에너지 관련 스키마
문서 41번에 따른 요청/응답 모델
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WithdrawalRequest(BaseModel):
    """개별 출금 요청"""
    request_id: str
    amount: Decimal = Field(..., gt=0)
    to_address: str = Field(..., max_length=64)
    type: str = Field(..., pattern="^(immediate|standard|scheduled)$")


class EnergyCalculationRequest(BaseModel):
    """에너지 계산 요청"""
    partner_id: str
    withdrawal_requests: List[WithdrawalRequest]
    batch_mode: bool = False


class EnergyCalculationResponse(BaseModel):
    """에너지 계산 응답"""
    total_energy_required: Decimal
    base_cost_trx: Decimal
    margin_trx: Decimal
    saas_fee_trx: Decimal
    total_cost_trx: Decimal
    energy_price: Decimal
    fallback_burn_trx: Decimal
    valid_until: str


class EnergyChargeRequest(BaseModel):
    """에너지 충전 요청"""
    trx_amount: Decimal = Field(..., gt=0)
    tx_hash: str = Field(..., min_length=64, max_length=64)
    reference_id: str
    target_address: str = Field(..., max_length=64)
    energy_amount: Decimal = Field(..., gt=0)
    duration_days: int = Field(default=1, ge=1, le=30)


class EnergyChargeResponse(BaseModel):
    """에너지 충전 응답"""
    delegation_tx_hash: str
    delegated_energy: Decimal
    expires_at: str
    status: str


class WithdrawalBatchRequest(BaseModel):
    """출금 배치 처리 요청"""
    withdrawal_requests: List[WithdrawalRequest]
    optimization_level: str = Field(default="standard", pattern="^(standard|aggressive|conservative)$")


class EnergyMonitoringResponse(BaseModel):
    """에너지 모니터링 응답"""
    hot_wallet_address: str
    cold_wallet_address: str
    hot_wallet_usdt_balance: Decimal
    hot_wallet_trx_balance: Decimal
    current_energy: Decimal
    daily_average_usage: Decimal
    estimated_depletion: str
    auto_recharge_threshold: Decimal
    auto_recharge_needed: bool


class SaaSFeeSettings(BaseModel):
    """SaaS 수수료 설정"""
    per_transaction_fee: Decimal = Field(default=Decimal("1.0"))
    minimum_batch_fee: Decimal = Field(default=Decimal("5.0"))
    fee_type: str = Field(default="fixed", pattern="^(fixed|percentage|tiered)$")
    
    
class PartnerFeeSettingsUpdate(BaseModel):
    """파트너사 수수료 설정 업데이트"""
    partner_id: str
    fee_settings: SaaSFeeSettings
