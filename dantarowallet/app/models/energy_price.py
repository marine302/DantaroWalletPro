"""
에너지 가격 히스토리 모델
"""
from sqlalchemy import Column, String, Numeric, DateTime, BigInteger, ForeignKey, Index, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class EnergyPrice(Base):
    """에너지 가격 히스토리"""
    __tablename__ = "energy_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(50), ForeignKey("energy_providers.id"), nullable=False)
    
    # 가격 정보
    price = Column(Numeric(12, 8), nullable=False)  # 에너지당 가격
    currency = Column(String(10), default="TRX")  # 통화 단위
    available_energy = Column(BigInteger, default=0)  # 사용 가능한 에너지량
    
    # 시장 데이터
    volume_24h = Column(BigInteger, default=0)  # 24시간 거래량
    change_24h = Column(Numeric(8, 4), default=0.0000)  # 24시간 변동률 (%)
    
    # 타임스탬프
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 인덱스
    __table_args__ = (
        Index('idx_provider_timestamp', 'provider_id', 'timestamp'),
    )
    
    # 관계
    provider = relationship("EnergyProvider", back_populates="prices")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "providerId": self.provider_id,
            "price": float(self.price) if self.price else 0.0,  # type: ignore
            "currency": self.currency,
            "availableEnergy": self.available_energy,
            "volume24h": self.volume_24h,
            "change24h": float(self.change_24h) if self.change_24h else 0.0,  # type: ignore
            "timestamp": self.timestamp.isoformat()
        }


# EnergyProvider 모델에 역관계 추가
from app.models.energy_provider import EnergyProvider
EnergyProvider.prices = relationship("EnergyPrice", back_populates="provider")
