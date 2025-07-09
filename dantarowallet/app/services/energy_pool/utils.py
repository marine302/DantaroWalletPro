"""
에너지 풀 서비스 - 유틸리티 함수들
"""
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


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전하게 float로 변환합니다."""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_usage_rate(used_energy: int, total_energy: int) -> float:
    """에너지 사용률 계산"""
    if total_energy <= 0:
        return 0.0
    return (used_energy / total_energy) * 100


def calculate_efficiency_score(available_energy: int, total_energy: int) -> float:
    """효율성 점수 계산"""
    if total_energy <= 0:
        return 0.0
    
    usage_rate = calculate_usage_rate(total_energy - available_energy, total_energy)
    
    # 60-80% 사용률일 때 최고 효율
    if 60 <= usage_rate <= 80:
        return 95.0
    elif usage_rate < 60:
        return 85.0 + (usage_rate / 60.0) * 10.0
    else:
        return 95.0 - ((usage_rate - 80.0) / 20.0) * 20.0
