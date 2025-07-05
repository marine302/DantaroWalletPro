"""
입금 모델 정의.
블록체인에서 감지된 입금 트랜잭션 정보를 저장합니다.
"""
from decimal import Decimal
from enum import Enum

from app.models.base import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship


class DepositStatus(str, Enum):
    """입금 상태"""

    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class Deposit(BaseModel):
    """
    입금 모델.
    블록체인에서 감지된 입금 트랜잭션을 관리합니다.
    """

    # 트랜잭션 정보
    tx_hash = Column(String(64), unique=True, nullable=False, index=True)
    from_address = Column(String(42), nullable=False, index=True)
    to_address = Column(String(42), nullable=False, index=True)

    # 금액 정보
    amount = Column(Numeric(precision=28, scale=8), nullable=False)
    token_symbol = Column(String(10), nullable=False, default="TRX")
    token_contract = Column(String(42), nullable=True)  # TRC20 토큰 계약 주소

    # 블록 정보
    block_number = Column(Integer, nullable=False, index=True)
    block_timestamp = Column(Integer, nullable=False)
    transaction_index = Column(Integer, nullable=False)

    # 확인 상태
    confirmations = Column(Integer, nullable=False, default=0)
    is_confirmed = Column(Boolean, nullable=False, default=False)
    min_confirmations = Column(Integer, nullable=False, default=19)  # TRON 권장 확인 수

    # 처리 상태
    is_processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(String, nullable=True)

    # 사용자 연결
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)

    # 오류 정보
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    # 관계
    user = relationship("User", back_populates="deposits", lazy="selectin")
    wallet = relationship("Wallet", back_populates="deposits", lazy="selectin")

    # 인덱스
    __table_args__ = (
        Index("idx_deposit_status", "is_confirmed", "is_processed"),
        Index("idx_deposit_block", "block_number", "transaction_index"),
        Index("idx_deposit_user_token", "user_id", "token_symbol"),
    )

    def __repr__(self) -> str:
        return f"<Deposit(tx_hash={self.tx_hash}, amount={self.amount}, user_id={self.user_id})>"

    @property
    def formatted_amount(self) -> str:
        """
        포맷된 금액 반환.

        Returns:
            str: 소수점 8자리까지 포맷된 금액
        """
        return f"{self.amount:.8f}"
