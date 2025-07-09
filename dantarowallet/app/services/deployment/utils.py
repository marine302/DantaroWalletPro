"""
배포 서비스용 타입 안전성 유틸리티 함수들
"""
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation as DecimalException
from typing import Any, Dict, Optional


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default
    
    value = getattr(obj, attr, default)
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        return value.value if value.value is not None else default
    
    return value if value is not None else default


def safe_str(value: Any, default: str = '') -> str:
    """안전한 문자열 변환"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
        
    return str(value)


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 정수 변환"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전한 실수 변환"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
    
    try:
        return Decimal(str(value))
    except (DecimalException, ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 불린 변환"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return bool(value)
    
    return default


def safe_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """안전한 datetime 변환"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
    
    if isinstance(value, datetime):
        return value
    
    return default


def safe_dict(value: Any, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """안전한 딕셔너리 변환"""
    if default is None:
        default = {}
    
    if value is None:
        return default
    
    # SQLAlchemy Column 타입 처리
    if hasattr(value, 'value'):
        value = value.value
    
    if value is None:
        return default
    
    if isinstance(value, dict):
        return value
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default
    
    return default
