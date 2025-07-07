"""
에너지 사용 이력 모델
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class EnergyUsageHistory(Base):
    """에너지 사용 이력 테이블"""
    
    __tablename__ = "energy_usage_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # deposit, withdrawal, etc.
    energy_amount = Column(Integer, nullable=False)  # 사용된 에너지 양
    transaction_id = Column(String(100), nullable=True)  # 관련 거래 ID
    description = Column(String(255), nullable=True)  # 설명
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 관계
    partner = relationship("Partner", back_populates="energy_usage_history")
    
    def __repr__(self):
        return f"<EnergyUsageHistory(id={self.id}, partner_id={self.partner_id}, type={self.transaction_type}, amount={self.energy_amount})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "partner_id": str(self.partner_id),
            "transaction_type": self.transaction_type,
            "energy_amount": self.energy_amount,
            "transaction_id": self.transaction_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at is not None else None
        }
