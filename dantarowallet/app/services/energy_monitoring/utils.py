"""
에너지 모니터링 서비스 - 타입 안전성 유틸리티
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional


def safe_decimal_to_int(value: Any, default: int = 0) -> int:
    """Decimal 값을 안전하게 int로 변환"""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


def safe_decimal_to_float(value: Any, default: float = 0.0) -> float:
    """Decimal 값을 안전하게 float로 변환"""
    if value is None:
        return default
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


def safe_enum_value(enum_obj: Any, default: str = "unknown") -> str:
    """Enum 값을 안전하게 문자열로 변환"""
    try:
        if hasattr(enum_obj, "value"):
            return enum_obj.value
        return str(enum_obj) if enum_obj else default
    except:
        return default


def safe_datetime_isoformat(dt: Any) -> Optional[str]:
    """DateTime을 안전하게 ISO 형식으로 변환"""
    try:
        if dt and hasattr(dt, "isoformat"):
            return dt.isoformat()
        return None
    except:
        return None


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """Any 값을 안전하게 int로 변환"""
    try:
        if isinstance(value, int):
            return value
        if hasattr(value, "__int__"):
            return int(value)
        return int(str(value))
    except:
        return default


def safe_bool_check(value: Any) -> bool:
    """SQLAlchemy 객체를 안전하게 bool로 변환"""
    try:
        if value is None:
            return False
        # SQLAlchemy Column 객체인 경우 값이 있다고 가정
        return True
    except:
        return False
