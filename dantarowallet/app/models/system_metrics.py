"""
시스템 메트릭스 모델
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import DECIMAL, JSON, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base


class SystemMetrics(Base):
    """시스템 메트릭스 테이블"""

    __tablename__ = "system_metrics"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(
        String(100), nullable=False
    )  # cpu_usage, memory_usage, api_calls, etc.
    metric_value = Column(DECIMAL(10, 4), nullable=False)  # 메트릭 값
    metric_unit = Column(String(20), nullable=True)  # %, MB, count, etc.
    partner_id = Column(PG_UUID(as_uuid=True), nullable=True)  # 파트너별 메트릭인 경우
    extra_data = Column(JSON, nullable=True)  # 추가 메타데이터
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, type={self.metric_type}, value={self.metric_value})>"

    def to_dict(self):
        # 헬퍼 함수 정의
        def safe_get_attr(obj, attr, default=None):
            """SQLAlchemy 객체에서 안전하게 속성을 가져옵니다."""
            try:
                value = getattr(obj, attr, default)
                # SQLAlchemy Column 타입인지 확인
                if hasattr(value, "__class__") and "Column" in str(value.__class__):
                    return default
                return value
            except (AttributeError, TypeError):
                return default

        def safe_float(value, default=0.0):
            """안전하게 float로 변환합니다."""
            try:
                if value is None:
                    return None
                return float(value)
            except (ValueError, TypeError):
                return default

        metric_value = safe_get_attr(self, "metric_value")
        partner_id = safe_get_attr(self, "partner_id")

        recorded_at = safe_get_attr(self, "recorded_at")
        if recorded_at and hasattr(recorded_at, "isoformat"):
            recorded_at_str = recorded_at.isoformat()
        else:
            recorded_at_str = datetime.utcnow().isoformat()

        return {
            "id": str(safe_get_attr(self, "id", "")),
            "metric_type": safe_get_attr(self, "metric_type", ""),
            "metric_value": (
                safe_float(metric_value) if metric_value is not None else None
            ),
            "metric_unit": safe_get_attr(self, "metric_unit"),
            "partner_id": str(partner_id) if partner_id is not None else None,
            "extra_data": safe_get_attr(self, "extra_data"),
            "recorded_at": recorded_at_str,
        }
