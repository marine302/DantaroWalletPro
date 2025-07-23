"""
외부 지갑 연동 스키마
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ConnectExternalWalletRequest(BaseModel):
    wallet_address: str = Field(..., description="지갑 주소")
    public_key: Optional[str] = Field(None, description="공개키")
    signature: str = Field(..., description="서명")
    message: Optional[str] = Field(None, description="서명한 메시지")


class ExternalWalletResponse(BaseModel):
    id: int
    partner_id: int
    wallet_type: str
    wallet_address: str
    nickname: Optional[str]
    is_active: bool
    connected_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class WalletBalanceResponse(BaseModel):
    wallet_address: str
    trx_balance: Decimal
    usdt_balance: Decimal
    energy: Optional[int] = 0
    bandwidth: Optional[int] = 0
    last_updated: datetime


class TransactionHistoryResponse(BaseModel):
    transaction_id: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    amount: Decimal
    token_type: str  # TRX, USDT
    transaction_type: str  # send, receive
    fee: Optional[Decimal] = None
    status: str  # success, failed, pending


class MessageResponse(BaseModel):
    message: str
