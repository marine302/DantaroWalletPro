"""
시스템 메트릭스 모델
"""
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.models.base import Base


class SystemMetrics(Base):
    """시스템 메트릭스 테이블"""
    
    __tablename__ = "system_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(100), nullable=False)  # cpu_usage, memory_usage, api_calls, etc.
    metric_value = Column(DECIMAL(10, 4), nullable=False)  # 메트릭 값
    metric_unit = Column(String(20), nullable=True)  # %, MB, count, etc.
    partner_id = Column(PG_UUID(as_uuid=True), nullable=True)  # 파트너별 메트릭인 경우
    extra_data = Column(JSON, nullable=True)  # 추가 메타데이터
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, type={self.metric_type}, value={self.metric_value})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "metric_type": self.metric_type,
            "metric_value": float(self.metric_value) if self.metric_value else None,
            "metric_unit": self.metric_unit,
            "partner_id": str(self.partner_id) if self.partner_id else None,
            "extra_data": self.extra_data,
            "recorded_at": self.recorded_at.isoformat()
        }
