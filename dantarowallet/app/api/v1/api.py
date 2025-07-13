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
    energy,  # Doc #25: 에너지 풀 고급 관리 시스템
    fee_policy,  # Doc #26: 파트너사 수수료 및 정책 관리
    partners,  # 파트너 관리 API 엔드포인트
    sweep,  # Doc #27: 입금 Sweep 자동화 시스템
    stats,  # 통계 API 엔드포인트
    transactions,  # 거래 관리 API 엔드포인트
    users,  # 사용자 관리 API 엔드포인트
    transaction_analytics,
    wallet,
    withdrawal,
    withdrawal_management,  # Doc #28: 파트너사 출금 관리 고도화
    partner_onboarding,  # Doc #29: 파트너사 온보딩 자동화
    audit_compliance,  # Doc #30: 트랜잭션 감사 및 컴플라이언스
    external_energy,  # Doc #35(38): 외부 에너지 공급자 연동
    integrated_dashboard,  # Doc #37(34): 파트너사 종합 대시보드
)
from app.api.v1.endpoints.partner import tronlink

# 추후 추가 예정
# from app.api.v1.endpoints import users, transactions

# 기능별 라우터 등록
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(deposit.router, prefix="/deposit", tags=["deposit"])
api_router.include_router(withdrawal.router, prefix="/withdrawals", tags=["withdrawal"])
api_router.include_router(withdrawal_management.router, prefix="/withdrawal-management", tags=["withdrawal_management"])  # Doc #28: 파트너사 출금 관리 고도화
api_router.include_router(partner_onboarding.router, prefix="/partner-onboarding", tags=["partner_onboarding"])  # Doc #29: 파트너사 온보딩 자동화
api_router.include_router(tronlink.router, prefix="/tronlink", tags=["tronlink"])
api_router.include_router(energy.router, prefix="/energy", tags=["energy"])  # Doc #25: 에너지 풀 고급 관리
api_router.include_router(fee_policy.router, prefix="/fee-policy", tags=["fee_policy"])  # Doc #26: 파트너사 수수료 및 정책 관리
api_router.include_router(sweep.router, prefix="/sweep", tags=["sweep"])  # Doc #27: 입금 Sweep 자동화 시스템
api_router.include_router(stats.router, tags=["statistics"])  # 통계 API
api_router.include_router(users.router, prefix="/users", tags=["users"])  # 사용자 관리 API
api_router.include_router(partners.router, prefix="/partners", tags=["partners"])  # 파트너 관리 API
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])  # 거래 관리 API
api_router.include_router(
    transaction_analytics.router, prefix="/transaction-analytics", tags=["analytics"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(audit_compliance.router, tags=["audit_compliance"])  # Doc #30: 트랜잭션 감사 및 컴플라이언스
api_router.include_router(external_energy.router, tags=["external_energy"])  # Doc #35(38): 외부 에너지 공급자 연동
api_router.include_router(integrated_dashboard.router, prefix="/integrated-dashboard", tags=["integrated_dashboard"])  # Doc #37(34): 파트너사 종합 대시보드
# 추후 추가 예정
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])


# 임시 테스트 엔드포인트
@api_router.get("/test")
async def test_endpoint():
    """API가 정상 작동하는지 테스트하기 위한 임시 엔드포인트"""
    return {"message": "API v1 is working", "status": "success"}
