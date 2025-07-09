"""에너지 풀 서비스 유틸리티 함수들"""
from typing import Any
from decimal import Decimal
import decimal


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 객체에서 안전하게 속성을 가져옵니다."""
    if obj is None:
        return default
    try:
        value = getattr(obj, attr, default)
        # SQLAlchemy Column 타입인지 확인
        if hasattr(value, '__class__') and 'Column' in str(value.__class__):
            return default
        return value
    except (AttributeError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """안전하게 정수로 변환합니다."""
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """안전하게 Decimal로 변환합니다."""
    try:
        if value is None:
            return default
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return default


def calculate_energy_efficiency(used_energy: int, total_energy: int) -> float:
    """에너지 효율성을 계산합니다."""
    if total_energy == 0:
        return 0.0
    return (used_energy / total_energy) * 100


def validate_energy_amount(amount: int) -> bool:
    """에너지 양이 유효한지 검증합니다."""
    return isinstance(amount, int) and amount > 0