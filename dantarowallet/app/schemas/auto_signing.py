"""
TronLink 자동 서명 관련 Pydantic 스키마
실제 TronLink API 표준 기반
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class BatchPriority(str, Enum):
    """배치 우선순위"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TronLinkAuthRequest(BaseModel):
    """TronLink 계정 인증 요청 (tron_requestAccounts)"""

    wallet_address: str = Field(..., description="TronLink 지갑 주소")
    signature: str = Field(..., description="서명")
    message: str = Field(..., description="서명할 메시지")

    @validator("wallet_address")
    def validate_wallet_address(cls, v):
        if not v or len(v) != 34 or not v.startswith("T"):
            raise ValueError("유효하지 않은 TRON 지갑 주소입니다")
        return v


class TronLinkAuthResponse(BaseModel):
    """TronLink 계정 인증 응답"""

    code: int = Field(..., description="응답 코드 (200: 성공, 4000: 대기, 4001: 거부)")
    message: str = Field(..., description="응답 메시지")
    authorized: bool = Field(..., description="인증 성공 여부")
    wallet_id: Optional[int] = Field(None, description="지갑 ID")
    wallet_address: Optional[str] = Field(None, description="지갑 주소")


class AutoSigningSessionRequest(BaseModel):
    """자동 서명 세션 생성 요청"""

    wallet_address: str = Field(..., description="서명할 지갑 주소")
    session_duration_hours: int = Field(
        24, ge=1, le=168, description="세션 지속 시간 (시간, 최대 7일)"
    )
    max_amount_per_tx: Optional[Decimal] = Field(
        None, description="건당 최대 출금 금액"
    )
    max_daily_amount: Optional[Decimal] = Field(None, description="일일 최대 출금 금액")
    allowed_addresses: Optional[List[str]] = Field(
        None, description="허용된 수신 주소 목록"
    )

    @validator("wallet_address")
    def validate_wallet_address(cls, v):
        if not v or len(v) != 34 or not v.startswith("T"):
            raise ValueError("유효하지 않은 TRON 지갑 주소입니다")
        return v

    @validator("allowed_addresses")
    def validate_allowed_addresses(cls, v):
        if v:
            for addr in v:
                if not addr or len(addr) != 34 or not addr.startswith("T"):
                    raise ValueError("허용 주소 목록에 유효하지 않은 주소가 있습니다")
        return v


class AutoSigningSessionResponse(BaseModel):
    """자동 서명 세션 생성 응답"""

    session_token: str = Field(..., description="세션 토큰")
    expires_at: str = Field(..., description="만료 시간 (ISO 형식)")
    max_amount_per_tx: Optional[str] = Field(None, description="건당 최대 출금 금액")
    max_daily_amount: Optional[str] = Field(None, description="일일 최대 출금 금액")
    status: str = Field("active", description="세션 상태")
    tronweb_ready: bool = Field(True, description="TronWeb 준비 상태")


class TronWebSignRequest(BaseModel):
    """TronWeb 트랜잭션 서명 요청"""

    withdrawal_id: int = Field(..., description="출금 요청 ID")
    session_token: str = Field(..., description="자동 서명 세션 토큰")


class TronWebSignResponse(BaseModel):
    """TronWeb 트랜잭션 서명 응답"""

    withdrawal_id: int = Field(..., description="출금 요청 ID")
    transaction_hash: Optional[str] = Field(None, description="트랜잭션 해시")
    status: str = Field(..., description="처리 상태")
    auto_signed: bool = Field(True, description="자동 서명 여부")
    signed_at: str = Field(..., description="서명 시간 (ISO 형식)")
    tronweb_compatible: bool = Field(True, description="TronWeb 호환성")


class BatchSigningRequest(BaseModel):
    """배치 자동 서명 요청"""

    withdrawal_ids: List[int] = Field(..., description="출금 요청 ID 목록")
    session_token: str = Field(..., description="자동 서명 세션 토큰")
    priority: BatchPriority = Field(BatchPriority.NORMAL, description="배치 우선순위")
    max_concurrent: int = Field(5, ge=1, le=20, description="최대 동시 처리 수")
    schedule_at: Optional[datetime] = Field(None, description="예약 실행 시간")

    @validator("withdrawal_ids")
    def validate_withdrawal_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError("출금 요청 ID가 필요합니다")
        if len(v) > 100:
            raise ValueError("배치당 최대 100개까지 처리할 수 있습니다")
        return v


class BatchSigningResponse(BaseModel):
    """배치 자동 서명 응답"""

    batch_id: str = Field(..., description="배치 ID")
    status: str = Field(..., description="배치 상태")
    total_count: int = Field(..., description="총 출금 요청 수")
    total_amount: str = Field(..., description="총 출금 금액")
    priority: str = Field(..., description="배치 우선순위")
    schedule_at: Optional[str] = Field(None, description="예약 실행 시간")
    created_at: str = Field(..., description="생성 시간")
    tronlink_compatible: bool = Field(True, description="TronLink 호환성")


class TronWebStatusRequest(BaseModel):
    """TronWeb 상태 조회 요청"""

    session_token: str = Field(..., description="세션 토큰")


class TronWebStatusResponse(BaseModel):
    """TronWeb 상태 조회 응답 (window.tronWeb 상태)"""

    tronweb_ready: bool = Field(..., description="TronWeb 준비 상태")
    default_address: Optional[str] = Field(None, description="기본 주소 (base58)")
    status: str = Field(..., description="세션 상태")
    wallet_address: str = Field(..., description="지갑 주소")
    created_at: str = Field(..., description="생성 시간")
    expires_at: str = Field(..., description="만료 시간")
    max_amount_per_tx: Optional[str] = Field(None, description="건당 최대 출금 금액")
    max_daily_amount: Optional[str] = Field(None, description="일일 최대 출금 금액")
    daily_used_amount: str = Field("0", description="일일 사용 금액")
    transaction_count: int = Field(0, description="처리된 트랜잭션 수")
    allowed_addresses_count: int = Field(0, description="허용된 주소 수")


class SessionRevokeRequest(BaseModel):
    """세션 해제 요청"""

    session_token: str = Field(..., description="해제할 세션 토큰")


class SessionRevokeResponse(BaseModel):
    """세션 해제 응답"""

    status: str = Field("revoked", description="해제 상태")
    revoked_at: str = Field(..., description="해제 시간")
    tronlink_disconnected: bool = Field(True, description="TronLink 연결 해제됨")


class BatchStatusResponse(BaseModel):
    """배치 상태 조회 응답"""

    batch_id: str = Field(..., description="배치 ID")
    status: str = Field(..., description="배치 상태")
    priority: str = Field(..., description="배치 우선순위")
    total_count: int = Field(..., description="총 출금 요청 수")
    total_amount: str = Field(..., description="총 출금 금액")
    success_count: int = Field(0, description="성공한 출금 수")
    failed_count: int = Field(0, description="실패한 출금 수")
    created_at: str = Field(..., description="생성 시간")
    updated_at: str = Field(..., description="업데이트 시간")
    completed_at: Optional[str] = Field(None, description="완료 시간")
    schedule_at: Optional[str] = Field(None, description="예약 실행 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    tronlink_compatible: bool = Field(True, description="TronLink 호환성")


class SuccessfulWithdrawal(BaseModel):
    """성공한 출금 정보"""

    withdrawal_id: int = Field(..., description="출금 요청 ID")
    transaction_hash: str = Field(..., description="트랜잭션 해시")
    signed_at: str = Field(..., description="서명 시간")


class FailedWithdrawal(BaseModel):
    """실패한 출금 정보"""

    withdrawal_id: int = Field(..., description="출금 요청 ID")
    error: str = Field(..., description="오류 메시지")


class BatchResultResponse(BaseModel):
    """배치 처리 결과 응답"""

    batch_id: str = Field(..., description="배치 ID")
    status: str = Field(..., description="최종 상태")
    total_count: int = Field(..., description="총 출금 요청 수")
    success_count: int = Field(..., description="성공한 출금 수")
    failed_count: int = Field(..., description="실패한 출금 수")
    successful_withdrawals: List[SuccessfulWithdrawal] = Field(
        ..., description="성공한 출금 목록"
    )
    failed_withdrawals: List[FailedWithdrawal] = Field(
        ..., description="실패한 출금 목록"
    )
    completed_at: str = Field(..., description="완료 시간")
    tronlink_compatible: bool = Field(True, description="TronLink 호환성")


# 기존 호환성을 위한 별칭
AutoSignWithdrawalRequest = TronWebSignRequest
AutoSignWithdrawalResponse = TronWebSignResponse
SessionStatusResponse = TronWebStatusResponse
