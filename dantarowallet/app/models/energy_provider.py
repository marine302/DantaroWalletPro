"""
외부 에너지 공급자 관리 모델
요구사항 문서 기반으로 설계된 새로운 모델
"""

import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class ProviderStatus(enum.Enum):
    """공급자 상태"""

    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class EnergyProvider(Base):
    """에너지 공급자 정보"""

    __tablename__ = "energy_providers"

    # 기본 정보
    id = Column(String(50), primary_key=True)  # 예: "tronnrg-1"
    name = Column(String(100), nullable=False)  # 예: "TronNRG Pool A"
    api_endpoint = Column(String(255), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)  # 암호화된 API 키

    # 상태 및 성능 지표
    status = Column(Enum(ProviderStatus), default=ProviderStatus.ONLINE)
    reliability_score = Column(Numeric(5, 2), default=0.00)  # 99.2%
    response_time_avg = Column(Numeric(8, 2), default=0.00)  # 평균 응답 시간 (초)

    # 주문 제한
    min_order_size = Column(BigInteger, default=0)  # 최소 주문 크기
    max_order_size = Column(BigInteger, default=0)  # 최대 주문 크기

    # 수수료
    trading_fee = Column(Numeric(8, 6), default=0.000000)  # 거래 수수료
    withdrawal_fee = Column(Numeric(8, 6), default=0.000000)  # 출금 수수료

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "reliability": float(self.reliability_score) if self.reliability_score is not None else 0.0,  # type: ignore
            "avgResponseTime": float(self.response_time_avg) if self.response_time_avg is not None else 0.0,  # type: ignore
            "minOrderSize": self.min_order_size,
            "maxOrderSize": self.max_order_size,
            "fees": {
                "tradingFee": float(self.trading_fee) if self.trading_fee is not None else 0.0,  # type: ignore
                "withdrawalFee": float(self.withdrawal_fee) if self.withdrawal_fee is not None else 0.0,  # type: ignore
            },
            "lastUpdated": (
                self.updated_at.isoformat() if self.updated_at is not None else None
            ),
        }
