"""
잔고 관련 Pydantic 스키마.
API 요청 및 응답에 사용되는 데이터 모델을 정의합니다.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.transaction import (
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)


class BalanceResponse(BaseModel):
    """잔고 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    asset: str
    amount: Decimal
    locked_amount: Decimal
    available_amount: Decimal
    updated_at: datetime


class TransferRequest(BaseModel):
    """내부 이체 요청 스키마"""

    receiver_email: str
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=200)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal("0.000001"):
            raise ValueError("Amount must be at least 0.000001 USDT")
        if v > Decimal("1000000"):
            raise ValueError("Amount too large")
        return v


class TransferResponse(BaseModel):
    """이체 응답 스키마"""

    transaction_id: int
    reference_id: str
    amount: Decimal
    receiver_email: str
    sender_balance: Decimal
    timestamp: datetime


class TransactionResponse(BaseModel):
    """트랜잭션 응답 스키마"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    direction: TransactionDirection
    status: TransactionStatus
    amount: Decimal
    fee: Decimal
    net_amount: Decimal
    asset: str
    description: Optional[str]
    related_user_id: Optional[int]
    tx_hash: Optional[str]
    created_at: datetime


class BalanceSummaryResponse(BaseModel):
    """잔고 요약 응답 스키마"""

    balances: List[dict]
    recent_transactions: List[TransactionResponse]
    statistics: Dict[str, str]


class BalanceAdjustmentRequest(BaseModel):
    """잔고 조정 요청 스키마 (관리자용)"""

    user_id: int
    amount: Decimal
    adjustment_type: str = Field(..., pattern="^(deposit|bonus|correction|penalty)$")
    description: str = Field(..., min_length=5, max_length=200)
