"""
API 버전 1의 라우터 정의.
모든 API 엔드포인트를 중앙 집중식으로 관리합니다.
"""

from fastapi import APIRouter

# API 버전 1의 메인 라우터
api_router = APIRouter()

# 엔드포인트 모듈 임포트
from app.api import energy_rental  # 에너지 렌탈 시스템
from app.api.v1 import admin
from app.api.v1.endpoints import audit_compliance  # Doc #30: 트랜잭션 감사 및 컴플라이언스
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import balance
from app.api.v1.endpoints import deposit
from app.api.v1.endpoints import energy  # Doc #25: 에너지 풀 고급 관리 시스템 - 오류 수정 완료
from app.api.v1.endpoints import energy_management  # Doc #25: 파트너용 에너지 풀 CRUD 관리
from app.api.v1.endpoints import external_energy  # Doc #35(38): 외부 에너지 공급자 연동
from app.api.v1.endpoints import fee_policy  # Doc #26: 파트너사 수수료 및 정책 관리
from app.api.v1.endpoints import optimization  # 백엔드 최적화 관리
from app.api.v1.endpoints import partner_energy  # 파트너 에너지 렌탈 시스템
from app.api.v1.endpoints import partner_onboarding  # Doc #29: 파트너사 온보딩 자동화
from app.api.v1.endpoints import partners_simple  # 간단한 파트너 관리 API
from app.api.v1.endpoints import stats  # 통계 API 엔드포인트
from app.api.v1.endpoints import sweep  # Doc #27: 입금 Sweep 자동화 시스템
from app.api.v1.endpoints import transaction_analytics
from app.api.v1.endpoints import transactions  # 거래 관리 API 엔드포인트 - 오류 수정 완료
from app.api.v1.endpoints import tronlink  # TronLink 연동 (메인 엔드포인트)
from app.api.v1.endpoints import users  # 사용자 관리 API 엔드포인트
from app.api.v1.endpoints import wallet
from app.api.v1.endpoints import websocket  # WebSocket 실시간 데이터 스트리밍
from app.api.v1.endpoints import withdrawal
from app.api.v1.endpoints import withdrawal_management  # Doc #28: 파트너사 출금 관리 고도화
from app.api.v1.endpoints import simple_energy  # Simple Energy Service - 개인/소규모 프로젝트용

# admin 폴더의 실제 구현된 라우터들 임포트
from app.api.v1.endpoints.admin import dashboard as admin_dashboard_real

# services 모듈 임포트 (separate from endpoints)
from app.services.dashboard import integrated_dashboard

# ============================================================================
# FRONTEND REFERENCE GUIDE & API CLASSIFICATION
# ============================================================================
#
# 🔐 SUPER ADMIN DASHBOARD (Port 3020): /frontend/super-admin-dashboard/
#   📁 Files: /app/audit-compliance/page.tsx, /app/integrated-dashboard/page.tsx
#   🎯 Purpose: Complete system administration and monitoring
#   📡 APIs Used:
#     - admin, admin_dashboard, admin_fees, admin_energy, admin_partners
#     - audit-compliance, integrated_dashboard, withdrawal_management, sweep
#     - partner_onboarding, analytics, statistics, transactions, users
#
# 🤝 PARTNER ADMIN TEMPLATE (Port 3030: /frontend/partner-admin-template/
#   🎯 Purpose: Partner-specific operations and management
#   📡 APIs Used:
#     - tronlink, energy_management, fee_policy
#     - authentication, balance, wallet, deposit, withdrawal (shared)
#
# 🔄 COMMON APIS: Used by both frontends with different contexts
#   - authentication: User login/auth for both admin and partner users
#   - balance: Internal balance management
#   - wallet: On-chain wallet operations
#   - deposit/withdrawal: Transaction processing
#   - energy: Energy monitoring (admin view vs partner view)
#
# ============================================================================

# === AUTHENTICATION & CORE USER OPERATIONS ===
# Used by both frontends - essential user operations
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    balance.router, prefix="/balance", tags=["balance"]
)  # Internal balance (different from wallet on-chain)
api_router.include_router(
    wallet.router, prefix="/wallet", tags=["wallet"]
)  # On-chain wallet & balance
api_router.include_router(deposit.router, prefix="/deposit", tags=["deposit"])
api_router.include_router(withdrawal.router, prefix="/withdrawals", tags=["withdrawal"])

# === SUPER ADMIN DASHBOARD EXCLUSIVE ===
# Advanced administration and system monitoring

# Partner Management & Onboarding
api_router.include_router(
    energy_rental.router, tags=["energy_rental"]
)  # 기존 에너지 렌탈 API (공통 기능)

# 역할별 에너지 렌탈 API 추가
from app.api.v1.endpoints.admin import energy_rental as admin_energy_rental
from app.api.v1.endpoints import partner_energy_rental

api_router.include_router(
    admin_energy_rental.router, tags=["admin_energy_rental"]
)  # 수퍼어드민 전용 에너지 렌탈 관리

api_router.include_router(
    partner_energy_rental.router, tags=["partner_energy_rental"]
)  # 파트너어드민 전용 에너지 렌탈

# System Administration
api_router.include_router(
    admin.router, prefix="/admin", tags=["admin"]
)  # Core admin operations
api_router.include_router(
    admin_dashboard_real.router, tags=["admin_dashboard"]
)  # Super admin dashboard (real implementation)
api_router.include_router(
    users.router, prefix="/users", tags=["users"]
)  # User management
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)  # Transaction admin

# Financial Management
api_router.include_router(
    fee_policy.router, prefix="/fee-policy", tags=["fee_policy"]
)  # Partner fee policies
api_router.include_router(
    withdrawal_management.router,
    prefix="/withdrawal-management",
    tags=["withdrawal_management"],
)  # Advanced withdrawal controls
api_router.include_router(
    sweep.router, prefix="/sweep", tags=["sweep"]
)  # Deposit sweep automation

# Compliance & Security
api_router.include_router(
    audit_compliance.router
)  # 🔍 Frontend: /app/audit-compliance/page.tsx
# Note: Uses prefix="/audit-compliance" defined in the router itself

# Integrated Dashboard - Comprehensive partner analytics dashboard
api_router.include_router(
    integrated_dashboard.router, tags=["integrated_dashboard"]
)  # 🔍 Frontend: /app/integrated-dashboard/page.tsx

# Analytics & Reporting
# dashboard router는 하단에서 /dashboard로 등록되므로 여기서는 제거
api_router.include_router(
    stats.router, tags=["statistics"]
)  # General system statistics
api_router.include_router(
    transaction_analytics.router, prefix="/transaction-analytics", tags=["analytics"]
)

# === PARTNER ADMIN TEMPLATE EXCLUSIVE ===
# Partner-specific operations and integrations

# TronLink Integration - Core partner functionality
api_router.include_router(
    tronlink.router, prefix="/tronlink", tags=["tronlink"]
)  # 🔗 TronLink wallet integration

# Partner Energy Management - CRUD operations for energy pools
api_router.include_router(
    energy_management.router, tags=["energy_management"]
)  # Energy pool management UI

# === SIMPLE ENERGY APIS === 
# 개인/소규모 프로젝트용 쉬운 에너지 API (인증 불필요)
api_router.include_router(
    simple_energy.router, prefix="/simple-energy", tags=["simple_energy"]
)  # Simple Energy Service - 5분 내 시작 가능

# === WEBSOCKET REAL-TIME APIS ===
# Real-time data streaming for both frontends
api_router.include_router(
    websocket.router, prefix="/ws", tags=["websocket"]
)  # WebSocket real-time streaming

# Backend Optimization - System performance management (Super Admin only)
api_router.include_router(
    optimization.router, prefix="/admin", tags=["optimization"]
)  # Performance optimization


# 임시 테스트 엔드포인트
@api_router.get("/test")
async def test_endpoint():
    """API가 정상 작동하는지 테스트하기 위한 임시 엔드포인트"""
    return {"message": "API v1 is working", "status": "success"}
