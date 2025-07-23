"""
기본 모델 클래스 정의.
모든 데이터베이스 모델의 기본 클래스로 사용됩니다.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class BaseModel(Base):
    """
    모든 모델의 기본 클래스.
    공통 필드와 메서드를 제공합니다.
    """

    __abstract__ = True

    # 기본 식별자
    id = Column(Integer, primary_key=True, index=True)

    # 생성 시간 (자동 기록)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 수정 시간 (자동 업데이트)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """
        테이블명을 클래스명의 소문자 복수형으로 자동 생성
        """
        return cls.__name__.lower() + "s"

    def dict(self) -> Dict[str, Any]:
        """
        모델을 딕셔너리로 변환.

        Returns:
            Dict[str, Any]: 모델 속성을 담은 딕셔너리
        """
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update(self, **kwargs) -> None:
        """
        모델 속성 일괄 업데이트.

        Args:
            **kwargs: 속성명=값 쌍
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
