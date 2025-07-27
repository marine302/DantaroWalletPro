"""
에너지 공급원 가격 이력 모델 - 문서 #40 기반
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from decimal import Decimal
from datetime import datetime
from app.models.base import BaseModel

class EnergySupplierPriceHistory(BaseModel):
    """에너지 공급원 가격 이력"""

    # 공급원 정보
    supplier_id = Column(Integer, ForeignKey("energysuppliers.id"), nullable=False)
    supplier_type = Column(String(20), nullable=False)

    # 가격 정보
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    min_order_amount = Column(Integer)
    max_order_amount = Column(Integer)

    # 변경 정보
    changed_from = Column(Numeric(20, 10))  # 이전 가격
    changed_to = Column(Numeric(20, 10))    # 새 가격
    change_reason = Column(String(200))      # 변경 사유
    
    # 유효 기간
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # 메타데이터
    changed_by = Column(String(100))  # 변경자
    notes = Column(String(500))       # 비고

    def __repr__(self):
        return f"<EnergySupplierPriceHistory {self.supplier_type} {self.price_per_energy}>"
