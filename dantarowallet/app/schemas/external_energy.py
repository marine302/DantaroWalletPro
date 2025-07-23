"""
외부 에너지 API 스키마
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    """공급자 상태"""

    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class OrderType(str, Enum):
    """주문 유형"""

    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    """주문 상태"""

    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


# === 공급자 관련 스키마 ===


class ProviderFees(BaseModel):
    """공급자 수수료 정보"""

    tradingFee: float = Field(..., description="거래 수수료")
    withdrawalFee: float = Field(..., description="출금 수수료")


class EnergyProviderResponse(BaseModel):
    """에너지 공급자 응답"""

    id: str = Field(..., description="공급자 ID")
    name: str = Field(..., description="공급자 이름")
    status: ProviderStatus = Field(..., description="공급자 상태")
    pricePerEnergy: float = Field(..., description="에너지당 가격")
    availableEnergy: int = Field(..., description="사용 가능한 에너지")
    reliability: float = Field(..., description="신뢰성 점수")
    avgResponseTime: float = Field(..., description="평균 응답 시간")
    minOrderSize: int = Field(..., description="최소 주문 크기")
    maxOrderSize: int = Field(..., description="최대 주문 크기")
    fees: ProviderFees = Field(..., description="수수료 정보")
    lastUpdated: str = Field(..., description="마지막 업데이트 시간")


class ProvidersListResponse(BaseModel):
    """공급자 목록 응답"""

    success: bool = True
    data: List[EnergyProviderResponse]


class ProviderDetailResponse(BaseModel):
    """공급자 상세 정보 응답"""

    success: bool = True
    data: EnergyProviderResponse


# === 시장 데이터 스키마 ===


class MarketSummary(BaseModel):
    """시장 요약 정보"""

    bestPrice: float = Field(..., description="최저 가격")
    bestProvider: str = Field(..., description="최저 가격 공급자")
    totalProviders: int = Field(..., description="전체 공급자 수")
    activeProviders: int = Field(..., description="활성 공급자 수")
    avgPrice: float = Field(..., description="평균 가격")
    priceChange24h: float = Field(..., description="24시간 가격 변동률")
    totalVolume: int = Field(..., description="총 거래량")
    lastUpdated: str = Field(..., description="마지막 업데이트 시간")


class MarketSummaryResponse(BaseModel):
    """시장 요약 응답"""

    success: bool = True
    data: MarketSummary


class PriceUpdate(BaseModel):
    """실시간 가격 업데이트"""

    type: str = "price_update"
    providerId: str = Field(..., description="공급자 ID")
    price: float = Field(..., description="가격")
    change24h: float = Field(..., description="24시간 변동률")
    timestamp: str = Field(..., description="타임스탬프")


# === 주문 관련 스키마 ===


class CreateOrderRequest(BaseModel):
    """주문 생성 요청"""

    providerId: str = Field(..., description="공급자 ID")
    amount: int = Field(..., gt=0, description="에너지 양")
    orderType: OrderType = Field(default=OrderType.MARKET, description="주문 유형")
    duration: int = Field(default=3, gt=0, description="대여 기간 (일)")
    priceLimit: Optional[float] = Field(None, description="가격 제한 (limit 주문용)")


class OrderFees(BaseModel):
    """주문 수수료"""

    trading: float = Field(..., description="거래 수수료")
    withdrawal: float = Field(..., description="출금 수수료")


class EnergyOrderResponse(BaseModel):
    """에너지 주문 응답"""

    id: str = Field(..., description="주문 ID")
    providerId: str = Field(..., description="공급자 ID")
    userId: str = Field(..., description="사용자 ID")
    amount: int = Field(..., description="에너지 양")
    price: float = Field(..., description="단가")
    totalCost: float = Field(..., description="총 비용")
    orderType: OrderType = Field(..., description="주문 유형")
    status: OrderStatus = Field(..., description="주문 상태")
    duration: int = Field(..., description="대여 기간")
    fees: OrderFees = Field(..., description="수수료")
    externalOrderId: Optional[str] = Field(None, description="외부 주문 ID")
    transactionHash: Optional[str] = Field(None, description="트랜잭션 해시")
    createdAt: str = Field(..., description="생성 시간")
    filledAt: Optional[str] = Field(None, description="체결 시간")


class CreateOrderResponse(BaseModel):
    """주문 생성 응답"""

    success: bool = True
    data: EnergyOrderResponse


class OrderListResponse(BaseModel):
    """주문 목록 응답"""

    success: bool = True
    data: List[EnergyOrderResponse]
    pagination: Optional[Dict[str, Any]] = None


# === 에러 응답 ===


class ErrorResponse(BaseModel):
    """에러 응답"""

    success: bool = False
    error: str = Field(..., description="에러 메시지")
    code: Optional[str] = Field(None, description="에러 코드")
    details: Optional[Dict[str, Any]] = Field(None, description="추가 상세 정보")


# === 에너지 공급업체 통합 스키마 ===


class EnergyPriceTier(BaseModel):
    """에너지 가격 티어"""

    amount: int = Field(..., description="에너지 양")
    price_per_unit: float = Field(..., description="단위당 가격")
    total_price: float = Field(..., description="총 가격")
    discount_rate: float = Field(default=0.0, description="할인율")
    tier_name: str = Field(..., description="티어 이름")


class EnergyPriceResponse(BaseModel):
    """에너지 가격 응답"""

    provider: str = Field(..., description="공급업체 이름")
    prices: List[EnergyPriceTier] = Field(..., description="가격 티어 목록")
    currency: str = Field(default="TRX", description="통화")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")
    valid_until: datetime = Field(..., description="유효 기간")
    minimum_order: int = Field(..., description="최소 주문량")
    maximum_order: int = Field(..., description="최대 주문량")


class EnergyPurchaseRequest(BaseModel):
    """에너지 구매 요청"""

    amount: int = Field(..., gt=0, description="에너지 양")
    target_address: str = Field(..., description="대상 주소")
    auto_distribute: bool = Field(default=False, description="자동 분배 여부")
    partner_allocation: Optional[Dict[str, int]] = Field(
        None, description="파트너별 할당"
    )


class EnergyPurchaseResponse(BaseModel):
    """에너지 구매 응답"""

    transaction_id: str = Field(..., description="거래 ID")
    provider: str = Field(..., description="공급업체 이름")
    amount: int = Field(..., description="구매한 에너지 양")
    total_cost: float = Field(..., description="총 비용")
    status: str = Field(..., description="거래 상태")
    estimated_delivery: datetime = Field(..., description="예상 전달 시간")
    tx_hash: str = Field(default="", description="블록체인 트랜잭션 해시")
    partner_benefits: Optional[Dict[str, Any]] = Field(
        None, description="파트너 혜택 정보"
    )


class EnergyBalanceResponse(BaseModel):
    """에너지 잔액 응답"""

    address: str = Field(..., description="주소")
    available_energy: int = Field(..., description="사용 가능한 에너지")
    reserved_energy: int = Field(default=0, description="예약된 에너지")
    total_purchased: int = Field(default=0, description="총 구매 에너지")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")
    provider: str = Field(..., description="공급업체 이름")
    partner_tier: Optional[str] = Field(None, description="파트너 티어")
    next_refill_discount: float = Field(default=0.0, description="다음 리필 할인율")


class ProviderHealthCheck(BaseModel):
    """공급업체 상태 확인"""

    provider: str = Field(..., description="공급업체 이름")
    is_healthy: bool = Field(..., description="상태 양호 여부")
    response_time: float = Field(..., description="응답 시간 (초)")
    last_check: datetime = Field(..., description="마지막 확인 시간")
    error_message: Optional[str] = Field(None, description="에러 메시지")
