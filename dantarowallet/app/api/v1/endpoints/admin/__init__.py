"""
Admin API 모듈 초기화

모듈화된 관리자 API 엔드포인트들을 통합 관리합니다.
기존의 830줄 단일 파일을 6개 모듈로 분할했습니다.

모듈 구성:
- auth.py: 로그인/로그아웃 관리
- dashboard.py: 메인 대시보드
- users.py: 사용자 관리
- system.py: 시스템 관리 및 출금 관리
- fees.py: 수수료 설정 관리
- energy.py: 에너지 풀 관리
"""

# 실제 import는 사용할 때만 수행 (선택적 import)
def get_auth_router():
    from .auth import router
    return router

def get_dashboard_router():
    from .dashboard import router
    return router

def get_users_router():
    from .users import router
    return router

def get_system_router():
    from .system import router
    return router

def get_fees_router():
    from .fees import router
    return router

def get_energy_router():
    from .energy import router
    return router

__all__ = [
    "get_auth_router",
    "get_dashboard_router", 
    "get_users_router",
    "get_system_router",
    "get_fees_router",
    "get_energy_router",
]
