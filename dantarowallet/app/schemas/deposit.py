"""
입금 관련 Pydantic 스키마.
API 요청 및 응답에 사용되는 데이터 모델을 정의합니다.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.deposit import DepositStatus


class DepositRequest(BaseModel):
    """입금 요청 스키마"""

    amount: Decimal = Field(..., gt=0)
    asset: str = Field(default="USDT", pattern="^(USDT|TRX)$")
    description: Optional[str] = Field(None, max_length=200)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal("0.000001"):
            raise ValueError("Amount must be at least 0.000001")
        if v > Decimal("1000000"):
            raise ValueError("Amount too large")
        return v


class DepositResponse(BaseModel):
    """입금 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_id: str
    amount: Decimal
    asset: str
    wallet_address: str
    deposit_address: str
    status: DepositStatus
    confirmations: int
    required_confirmations: int
    tx_hash: Optional[str]
    network_fee: Decimal
    net_amount: Decimal
    description: Optional[str]
    created_at: datetime
    confirmed_at: Optional[datetime]


class DepositStatusResponse(BaseModel):
    """입금 상태 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_id: str
    status: DepositStatus
    confirmations: int
    required_confirmations: int
    tx_hash: Optional[str]
    amount: Decimal
    asset: str
    is_confirmed: bool
    estimated_completion: Optional[datetime]


class DepositHistoryResponse(BaseModel):
    """입금 이력 응답 스키마"""

    deposits: List[DepositResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int


class DepositSummaryResponse(BaseModel):
    """입금 요약 응답 스키마"""

    total_deposits: int
    total_amount: Decimal
    pending_deposits: int
    pending_amount: Decimal
    completed_deposits: int
    completed_amount: Decimal
    failed_deposits: int
    recent_deposits: List[DepositResponse]


class DepositAddressResponse(BaseModel):
    """입금 주소 응답 스키마"""

    address: str
    hex_address: str
    asset: str
    network: str
    qr_code_url: Optional[str]
    is_active: bool
    expires_at: Optional[datetime]


class DepositConfirmationRequest(BaseModel):
    """입금 확인 요청 스키마 (관리자용)"""

    deposit_id: int
    tx_hash: str = Field(..., min_length=64, max_length=64)
    confirmations: int = Field(default=1, ge=1)
    network_fee: Decimal = Field(default=Decimal("0"))
    notes: Optional[str] = Field(None, max_length=500)


class DepositWebhookData(BaseModel):
    """입금 웹훅 데이터 스키마"""

    tx_hash: str
    from_address: str
    to_address: str
    amount: Decimal
    asset: str
    confirmations: int
    block_height: Optional[int]
    timestamp: datetime
    network_fee: Decimal
