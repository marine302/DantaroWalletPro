"""
관리자 대시보드 API 엔드포인트 (통합 라우터)

이 파일은 모듈화된 admin API들을 통합하는 메인 라우터입니다.
원래 830줄의 단일 파일을 6개 모듈로 분할하고, 
이 파일에서 모든 라우터를 통합 관리합니다.

분할된 모듈:
- admin/auth.py: 인증 관련 (로그인/로그아웃)
- admin/dashboard.py: 메인 대시보드
- admin/users.py: 사용자 관리
- admin/system.py: 시스템 관리 및 출금 관리  
- admin/fees.py: 수수료 설정 관리
- admin/energy.py: 에너지 풀 관리

이전: 830줄 단일 파일 + 20+ 엔드포인트 혼재
현재: 6개 모듈 + 기능별 명확한 분리
"""
from fastapi import APIRouter

from .admin import (
    get_auth_router,
    get_dashboard_router,
    get_energy_router,
    get_fees_router,
    get_system_router,
    get_users_router,
)

# 메인 관리자 라우터 생성
router = APIRouter()

# 모든 서브 라우터 포함
router.include_router(get_auth_router(), tags=["admin-auth"])
router.include_router(get_dashboard_router(), tags=["admin-dashboard"])  
router.include_router(get_users_router(), tags=["admin-users"])
router.include_router(get_system_router(), tags=["admin-system"])
router.include_router(get_fees_router(), tags=["admin-fees"])
router.include_router(get_energy_router(), tags=["admin-energy"])

# 백워드 호환성을 위한 별칭 (기존 import 구조 유지)
admin_router = router

__all__ = ["router", "admin_router"]
