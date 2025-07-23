"""
지갑 관련 Pydantic 스키마.
API 요청 및 응답에 사용되는 데이터 모델을 정의합니다.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class WalletResponse(BaseModel):
    """
    지갑 응답 스키마
    """

    model_config = ConfigDict(from_attributes=True)

    address: str
    hex_address: str
    is_active: bool
    is_monitored: bool
    created_at: datetime


class WalletCreateResponse(BaseModel):
    """
    지갑 생성 응답 스키마
    """

    address: str
    hex_address: str
    network: str
    message: str = "Wallet created successfully"


class WalletBalanceResponse(BaseModel):
    """
    지갑 잔고 응답 스키마
    """

    address: str
    balances: Dict[str, Dict[str, Any]]
    last_checked: str


class AddressValidationRequest(BaseModel):
    """
    주소 검증 요청 스키마
    """

    address: str = Field(..., min_length=34, max_length=34)


class AddressValidationResponse(BaseModel):
    """
    주소 검증 응답 스키마
    """

    address: str
    is_valid: bool
    is_internal: bool = False
    message: Optional[str] = None


class WalletMonitoringRequest(BaseModel):
    """
    모니터링 설정 요청 스키마
    """

    enable: bool
