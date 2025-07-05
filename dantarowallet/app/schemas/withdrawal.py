"""
출금 관련 스키마.
출금 요청, 응답, 검토 등의 스키마를 정의합니다.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.withdrawal import WithdrawalPriority, WithdrawalStatus
from pydantic import BaseModel, ConfigDict, Field, field_validator


class WithdrawalRequest(BaseModel):
    """출금 요청 스키마"""

    to_address: str = Field(..., min_length=34, max_length=34, description="TRON 수신 주소")
    amount: Decimal = Field(..., gt=0, decimal_places=6, description="출금 금액")
    asset: str = Field(default="USDT", description="자산 종류")
    notes: Optional[str] = Field(None, max_length=500, description="사용자 메모")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal("10"):
            raise ValueError("최소 출금 금액은 10 USDT입니다")
        if v > Decimal("10000"):
            raise ValueError("최대 출금 금액은 10,000 USDT입니다")
        return v

    @field_validator("to_address")
    @classmethod
    def validate_address(cls, v):
        if not v.startswith("T"):
            raise ValueError("유효하지 않은 TRON 주소입니다")
        return v


class WithdrawalResponse(BaseModel):
    """출금 응답 스키마"""

    id: int
    user_id: int
    to_address: str
    amount: Decimal
    fee: Decimal
    net_amount: Decimal
    asset: str
    status: WithdrawalStatus
    priority: WithdrawalPriority
    requested_at: datetime
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]
    tx_hash: Optional[str]
    notes: Optional[str]
    rejection_reason: Optional[str]
    admin_notes: Optional[str]

    @property
    def total_amount(self) -> Decimal:
        """총 차감 금액"""
        return self.amount + self.fee

    model_config = ConfigDict(from_attributes=True)


class WithdrawalListResponse(BaseModel):
    """출금 목록 응답"""

    items: List[WithdrawalResponse]
    total: int
    pending_count: int
    total_pending_amount: Decimal


class WithdrawalReviewRequest(BaseModel):
    """출금 검토 요청"""

    action: str = Field(..., pattern="^(approve|reject)$", description="승인 또는 거부")
    admin_notes: Optional[str] = Field(None, max_length=500, description="관리자 메모")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="거부 사유")

    @field_validator("rejection_reason")
    @classmethod
    def validate_rejection_reason(cls, v, info):
        if info.data.get("action") == "reject" and not v:
            raise ValueError("거부 시 거부 사유는 필수입니다")
        return v


class WithdrawalCompleteRequest(BaseModel):
    """출금 완료 요청"""

    tx_hash: str = Field(..., min_length=64, max_length=66, description="트랜잭션 해시")
    tx_fee: Optional[Decimal] = Field(None, decimal_places=6, description="실제 네트워크 수수료")


class WithdrawalProcessingGuide(BaseModel):
    """출금 처리 가이드"""

    withdrawal_id: int
    status: str
    amount: str
    fee: str
    to_address: str
    instructions: List[str]
    warnings: List[str]
    checklist: List[str]


class WithdrawalStats(BaseModel):
    """출금 통계"""

    by_status: Dict[str, Dict[str, Any]]
    today: Dict[str, Any]
    pending_priority: Dict[str, int]
