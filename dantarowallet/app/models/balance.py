"""
잔고 모델 정의.
사용자의 디지털 자산 잔고를 관리합니다.
"""
from decimal import Decimal
from typing import TYPE_CHECKING

from app.models.base import BaseModel
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from app.models.user import User


class Balance(BaseModel):
    """
    잔고 모델.
    사용자의 디지털 자산 잔고를 관리합니다.
    """

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset = Column(String(10), nullable=False, default="USDT")
    amount = Column(
        Numeric(precision=18, scale=6), nullable=False, default=Decimal("0.000000")
    )
    locked_amount = Column(
        Numeric(precision=18, scale=6), nullable=False, default=Decimal("0.000000")
    )
    __table_args__ = (
        UniqueConstraint("user_id", "asset", name="uq_user_asset"),
        CheckConstraint("amount >= 0", name="check_positive_amount"),
        CheckConstraint("locked_amount >= 0", name="check_positive_locked"),
        CheckConstraint(
            "locked_amount <= amount", name="check_locked_not_exceed_amount"
        ),
        Index("idx_balance_user_asset", "user_id", "asset"),
    )

    def __repr__(self) -> str:
        """세션 바인딩 문제 방지를 위해 __dict__를 사용하여 안전하게 처리"""
        try:
            attrs = {}
            if hasattr(self, "__dict__"):
                attrs = self.__dict__

            user_id = attrs.get("user_id", "N/A") if "user_id" in attrs else "N/A"
            asset = attrs.get("asset", "N/A") if "asset" in attrs else "N/A"
            amount = attrs.get("amount", "N/A") if "amount" in attrs else "N/A"

            return f"<Balance(user_id={user_id}, asset={asset}, amount={amount})>"
        except:
            return "<Balance(detached)>"

    @property
    def available_amount(self) -> Decimal:
        """
        사용 가능한 잔고 계산 (전체 - 잠긴 금액).

        Returns:
            Decimal: 출금 또는 사용 가능한 잔고
        """
        total = Decimal(str(self.amount) if self.amount is not None else "0")
        locked = Decimal(
            str(self.locked_amount) if self.locked_amount is not None else "0"
        )
        return total - locked

    def can_withdraw(self, amount: Decimal) -> bool:
        """
        출금 가능 여부 확인.

        Args:
            amount: 출금하려는 금액

        Returns:
            bool: 출금 가능 여부
        """
        return self.available_amount >= amount

    def lock(self, amount: Decimal) -> bool:
        """
        금액 잠금 (출금 제한 등).

        Args:
            amount: 잠글 금액

        Returns:
            bool: 잠금 성공 여부
        """
        avail = self.available_amount
        if avail >= amount:
            current_locked = Decimal(
                str(self.locked_amount) if self.locked_amount is not None else "0"
            )
            self.locked_amount = current_locked + amount
            return True
        return False

    def unlock(self, amount: Decimal) -> bool:
        """
        금액 잠금 해제.

        Args:
            amount: 잠금 해제할 금액

        Returns:
            bool: 잠금 해제 성공 여부
        """
        current_locked = Decimal(
            str(self.locked_amount) if self.locked_amount is not None else "0"
        )

        if current_locked >= amount:
            self.locked_amount = current_locked - amount
            return True
        return False
