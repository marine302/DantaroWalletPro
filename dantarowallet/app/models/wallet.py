"""
지갑 모델 정의.
사용자별 TRON 지갑 주소 및 암호화된 프라이빗 키를 관리합니다.
"""

import json
from typing import TYPE_CHECKING, Dict, Optional

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.deposit import Deposit
    from app.models.user import User


class Wallet(BaseModel):
    """
    지갑 모델
    Attributes:
        user_id (int): 사용자 ID (Foreign Key)
        address (str): TRON 지갑 주소
        hex_address (str): TRON hex 형식 주소
        encrypted_private_key (str): 암호화된 프라이빗 키
        encryption_salt (str): 암호화에 사용된 salt
        is_active (bool): 지갑 활성화 상태
        is_monitored (bool): 입금 모니터링 활성화 상태
        wallet_metadata (str, optional): JSON 형태의 추가 데이터
    """

    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 지갑 정보
    address = Column(String(42), unique=True, nullable=False, index=True)
    hex_address = Column(String(42), unique=True, nullable=False)  # TRON hex format

    # 암호화된 프라이빗 키 (AES-256 암호화)
    encrypted_private_key = Column(Text, nullable=False)
    encryption_salt = Column(String(32), nullable=False)

    # 지갑 상태
    is_active = Column(Boolean, default=True, nullable=False)
    is_monitored = Column(Boolean, default=True, nullable=False)  # 입금 모니터링 여부

    # 추가 정보
    wallet_metadata = Column(Text, nullable=True)  # JSON 형태의 추가 데이터

    # 관계
    deposits = relationship("Deposit", back_populates="wallet", lazy="selectin")
    user = relationship(
        "User", back_populates="wallets", uselist=False, lazy="selectin"
    )

    # 인덱스
    __table_args__ = (
        Index("idx_wallet_user_active", "user_id", "is_active"),
        Index("idx_wallet_address_active", "address", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Wallet(user_id={self.user_id}, address={self.address})>"

    def get_metadata(self) -> Optional[Dict]:
        """
        메타데이터 파싱
        Returns:
            dict 또는 None
        """
        metadata_str = (
            str(self.wallet_metadata) if self.wallet_metadata is not None else None
        )
        if metadata_str:
            try:
                return json.loads(metadata_str)
            except Exception:
                return None
        return None

    def set_metadata(self, data: dict):
        """메타데이터 설정"""
        self.wallet_metadata = json.dumps(data)
