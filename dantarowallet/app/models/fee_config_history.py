"""
수수료 설정 이력 모델
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class FeeConfigHistory(Base):
    """수수료 설정 변경 이력 테이블"""
    
    __tablename__ = "fee_config_history"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    old_config = Column(JSON, nullable=True)  # 이전 설정
    new_config = Column(JSON, nullable=False)  # 새 설정
    changed_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 변경한 관리자
    change_reason = Column(String(255), nullable=True)  # 변경 이유
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 관계
    partner = relationship("Partner", back_populates="fee_config_history")
    changed_by_user = relationship("User")
    
    def __repr__(self):
        return f"<FeeConfigHistory(id={self.id}, partner_id={self.partner_id}, changed_by={self.changed_by})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "partner_id": str(self.partner_id),
            "old_config": self.old_config,
            "new_config": self.new_config,
            "changed_by": str(self.changed_by),
            "change_reason": self.change_reason,
            "created_at": self.created_at.isoformat()
        }
