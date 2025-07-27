"""파트너 관리자 API 엔드포인트"""

from fastapi import APIRouter

from . import energy

router = APIRouter()

# 파트너 하위 라우터 등록
router.include_router(energy.router, prefix="/energy", tags=["파트너 에너지 관리"])
