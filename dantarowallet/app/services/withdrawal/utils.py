"""
출금 서비스 유틸리티 함수들
공통으로 사용되는 헬퍼 함수들을 제공합니다.
"""

from decimal import Decimal
from typing import Any


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default

    value = getattr(obj, attr, default)

    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, "value"):
        return value.value
    elif hasattr(value, "__getitem__") and hasattr(value, "keys"):
        # dict-like object
        return value
    else:
        return value


def safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """안전한 str 변환"""
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 bool 변환"""
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    try:
        return bool(value)
    except (TypeError, ValueError):
        return default
