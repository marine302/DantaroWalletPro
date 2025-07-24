"""
파트너 API 로그 모델
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text

from app.models.base import Base


class PartnerApiLog(Base):
    """파트너 API 호출 로그"""

    __tablename__ = "partner_api_logs"

    id = Column(Integer, primary_key=True)
    partner_id = Column(String(50), nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Numeric(10, 2), nullable=False)
    request_size = Column(Integer, default=0)
    response_size = Column(Integer, default=0)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
