"""
외부 에너지 주문 관리 모델
"""
from sqlalchemy import Column, String, Numeric, DateTime, Enum, BigInteger, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class OrderType(enum.Enum):
    """주문 유형"""
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(enum.Enum):
    """주문 상태"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EnergyOrder(Base):
    """에너지 주문"""
    __tablename__ = "energy_orders"
    
    # 기본 정보
    id = Column(String(50), primary_key=True)  # UUID
    provider_id = Column(String(50), ForeignKey("energy_providers.id"), nullable=False)
    user_id = Column(String(50), nullable=False)  # 사용자 ID
    
    # 주문 상세
    amount = Column(BigInteger, nullable=False)  # 에너지 양
    price = Column(Numeric(12, 8), nullable=False)  # 단가
    total_cost = Column(Numeric(16, 8), nullable=False)  # 총 비용
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    duration = Column(BigInteger, default=1)  # 대여 기간 (일)
    
    # 수수료
    trading_fee = Column(Numeric(16, 8), default=0.00000000)
    withdrawal_fee = Column(Numeric(16, 8), default=0.00000000)
    
    # 외부 시스템 연동
    external_order_id = Column(String(100))  # 외부 주문 ID
    transaction_hash = Column(String(100))   # 트랜잭션 해시
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True))
    
    # 인덱스
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_provider_status', 'provider_id', 'status'),
    )
    
    # 관계
    provider = relationship("EnergyProvider")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "providerId": self.provider_id,
            "userId": self.user_id,
            "amount": self.amount,
            "price": float(self.price) if self.price else 0.0,  # type: ignore
            "totalCost": float(self.total_cost) if self.total_cost else 0.0,  # type: ignore
            "orderType": self.order_type.value,
            "status": self.status.value,
            "duration": self.duration,
            "fees": {
                "trading": float(self.trading_fee) if self.trading_fee else 0.0,  # type: ignore
                "withdrawal": float(self.withdrawal_fee) if self.withdrawal_fee else 0.0  # type: ignore
            },
            "externalOrderId": self.external_order_id,
            "transactionHash": self.transaction_hash,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "filledAt": self.filled_at.isoformat() if self.filled_at else None
        }
