"""
사용자 모델 정의.
시스템의 사용자 및 인증 정보를 저장합니다.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, Index, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.deposit import Deposit
    from app.models.wallet import Wallet


class User(BaseModel):
    """
    사용자 모델.
    인증, 인가 및 기본 사용자 정보를 관리합니다.
    """

    # 기본 정보
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 상태
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # 지갑 정보
    tron_address = Column(String(42), unique=True, nullable=True, index=True)

    # 관계 설정
    deposits = relationship("Deposit", back_populates="user", lazy="selectin")
    wallets = relationship("Wallet", back_populates="user", lazy="selectin")

    # 인덱스
    __table_args__ = (Index("idx_user_email_active", "email", "is_active"),)

    def __repr__(self) -> str:
        """객체 표현 문자열"""
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def is_authenticated(self) -> bool:
        """
        사용자 인증 상태 확인.

        Returns:
            bool: 활성 상태인 경우 True, 아니면 False
        """
        return bool(self.is_active)

    def has_wallet(self) -> bool:
        """
        사용자 지갑 생성 여부 확인.

        Returns:
            bool: 지갑 주소가 설정된 경우 True, 아니면 False
        """
        return bool(self.tron_address)
