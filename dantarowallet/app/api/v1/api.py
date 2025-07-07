"""
API 버전 1의 라우터 정의.
모든 API 엔드포인트를 중앙 집중식으로 관리합니다.
"""
from fastapi import APIRouter

# API 버전 1의 메인 라우터
api_router = APIRouter()

from app.api.v1 import admin, dashboard

# 엔드포인트 모듈 임포트
from app.api.v1.endpoints import (
    auth,
    balance,
    deposit,
    # energy,  # 임시 비활성화 - doc-24 구현으로 대체됨
    transaction_analytics,
    wallet,
    withdrawal,
)

# 추후 추가 예정
# from app.api.v1.endpoints import users, transactions

# 기능별 라우터 등록
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(deposit.router, prefix="/deposit", tags=["deposit"])
api_router.include_router(withdrawal.router, prefix="/withdrawals", tags=["withdrawal"])
# api_router.include_router(energy.router, prefix="/energy", tags=["energy"])  # 임시 비활성화
api_router.include_router(
    transaction_analytics.router, prefix="/transaction-analytics", tags=["analytics"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# 추후 추가 예정
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])


# 임시 테스트 엔드포인트
@api_router.get("/test")
async def test_endpoint():
    """API가 정상 작동하는지 테스트하기 위한 임시 엔드포인트"""
    return {"message": "API v1 is working", "status": "success"}
