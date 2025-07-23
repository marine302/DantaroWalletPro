"""
TronLink 외부 지갑 연동 관련 스키마
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class TronLinkConnectRequest(BaseModel):
    """TronLink 지갑 연결 요청"""

    wallet_address: str = Field(..., description="TronLink 지갑 주소")
    signature: str = Field(..., description="서명")
    message: str = Field(..., description="서명된 메시지")

    @validator("wallet_address")
    def validate_tron_address(cls, v):
        """TRON 주소 형식 검증"""
        if not v.startswith("T") or len(v) != 34:
            raise ValueError("올바르지 않은 TRON 주소 형식입니다")
        return v

    @validator("signature")
    def validate_signature(cls, v):
        """서명 형식 검증"""
        if not re.match(r"^0x[a-fA-F0-9]{130}$", v):
            raise ValueError("올바르지 않은 서명 형식입니다")
        return v


class TronLinkConnectResponse(BaseModel):
    """TronLink 지갑 연결 응답"""

    status: str = Field(..., description="연결 상태 (connected/reconnected)")
    wallet_id: int = Field(..., description="지갑 ID")
    address: str = Field(..., description="지갑 주소")
    message: str = Field(..., description="응답 메시지")


class WalletBalanceResponse(BaseModel):
    """지갑 잔액 응답"""

    address: str = Field(..., description="지갑 주소")
    trx_balance: float = Field(..., description="TRX 잔액")
    usdt_balance: float = Field(..., description="USDT 잔액")
    updated_at: str = Field(..., description="업데이트 시간")


class PartnerWalletInfo(BaseModel):
    """파트너 지갑 정보"""

    id: int = Field(..., description="지갑 ID")
    address: str = Field(..., description="지갑 주소")
    status: str = Field(..., description="지갑 상태")
    provider: str = Field(..., description="지갑 제공자")
    balance: WalletBalanceResponse = Field(..., description="잔액 정보")
    last_connected_at: Optional[str] = Field(None, description="마지막 연결 시간")
    created_at: str = Field(..., description="생성 시간")


class PartnerWalletsResponse(BaseModel):
    """파트너 지갑 목록 응답"""

    wallets: List[PartnerWalletInfo] = Field(..., description="지갑 목록")
    total_count: int = Field(..., description="총 지갑 개수")


class WalletDisconnectRequest(BaseModel):
    """지갑 연결 해제 요청"""

    wallet_id: int = Field(..., description="지갑 ID")


class WalletTransactionRequest(BaseModel):
    """지갑 거래 요청"""

    wallet_id: int = Field(..., description="지갑 ID")
    to_address: str = Field(..., description="수신 주소")
    amount: Decimal = Field(..., description="전송 금액", gt=0)
    token_type: str = Field("TRX", description="토큰 유형 (TRX/USDT)")
    memo: Optional[str] = Field(None, description="메모")

    @validator("to_address")
    def validate_to_address(cls, v):
        """수신 주소 검증"""
        if not v.startswith("T") or len(v) != 34:
            raise ValueError("올바르지 않은 TRON 주소 형식입니다")
        return v

    @validator("token_type")
    def validate_token_type(cls, v):
        """토큰 유형 검증"""
        if v not in ["TRX", "USDT"]:
            raise ValueError("지원하지 않는 토큰 유형입니다")
        return v


class WalletTransactionResponse(BaseModel):
    """지갑 거래 응답"""

    transaction_id: str = Field(..., description="거래 ID")
    status: str = Field(..., description="거래 상태")
    from_address: str = Field(..., description="송신 주소")
    to_address: str = Field(..., description="수신 주소")
    amount: Decimal = Field(..., description="전송 금액")
    token_type: str = Field(..., description="토큰 유형")
    fee: Decimal = Field(..., description="거래 수수료")
    created_at: str = Field(..., description="생성 시간")


class TronLinkStatusResponse(BaseModel):
    """TronLink 상태 응답"""

    is_connected: bool = Field(..., description="연결 상태")
    wallet_count: int = Field(..., description="연결된 지갑 수")
    total_balance: Dict[str, float] = Field(..., description="총 잔액")
    last_activity: Optional[str] = Field(None, description="마지막 활동 시간")


class MessageResponse(BaseModel):
    """기본 메시지 응답"""

    message: str = Field(..., description="응답 메시지")
    success: bool = Field(True, description="성공 여부")


class ErrorResponse(BaseModel):
    """에러 응답"""

    error: str = Field(..., description="에러 메시지")
    code: str = Field(..., description="에러 코드")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세정보")


class TronLinkAuthRequest(BaseModel):
    """TronLink 인증 요청 - 로그인용"""

    wallet_address: str = Field(..., description="지갑 주소")
    signature: str = Field(..., description="서명")
    timestamp: int = Field(..., description="타임스탬프")

    @validator("timestamp")
    def validate_timestamp(cls, v):
        """타임스탬프 유효성 검증 (5분 이내)"""
        import time

        current_time = int(time.time())
        if abs(current_time - v) > 300:  # 5분
            raise ValueError("타임스탬프가 유효하지 않습니다")
        return v


class TronLinkAuthResponse(BaseModel):
    """TronLink 인증 응답"""

    access_token: str = Field(..., description="액세스 토큰")
    partner_id: int = Field(..., description="파트너 ID")
    wallet_address: str = Field(..., description="지갑 주소")
    expires_in: int = Field(..., description="토큰 만료 시간 (초)")
