"""
Pool 모듈 초기화
"""

def get_pool_manager(db):
    """풀 관리자 반환"""
    from .pool_manager import PoolManager
    return PoolManager(db)

def get_usage_tracker(db):
    """사용량 추적기 반환"""
    from .usage_tracker import UsageTracker
    return UsageTracker(db)

__all__ = [
    "get_pool_manager",
    "get_usage_tracker",
]
