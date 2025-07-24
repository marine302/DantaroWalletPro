"""
관리자 API 엔드포인트 초기화
"""

from fastapi import APIRouter

from . import fees, partners

router = APIRouter()

# 관리자 하위 라우터 등록
router.include_router(fees.router, prefix="/fees", tags=["수수료 관리"])
router.include_router(partners.router, prefix="/partners", tags=["파트너사 관리"])
