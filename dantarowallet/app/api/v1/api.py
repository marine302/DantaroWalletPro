"""
API 버전 1의 라우터 정의 (에너지 API 제거 후)
모든 API 엔드포인트를 중앙 집중식으로 관리합니다.
"""

from fastapi import APIRouter

# API 버전 1의 메인 라우터
api_router = APIRouter()

# 엔드포인트 모듈 임포트 (에너지 관련 제외)
from app.api.v1 import admin
from app.api.v1.endpoints.admin import audit_compliance  # Doc #30: 트랜잭션 감사 및 컴플라이언스
from app.api.v1.endpoints.common import auth
from app.api.v1.endpoints.common import balance
from app.api.v1.endpoints.common import deposit
from app.api.v1.endpoints.partner import fee_policy  # Doc #26: 파트너사 수수료 및 정책 관리
from app.api.v1.endpoints.admin import optimization  # 백엔드 최적화 관리
from app.api.v1.endpoints.partner import partner_onboarding  # Doc #29: 파트너사 온보딩 자동화
from app.api.v1.endpoints.partner import partners_simple  # 간단한 파트너 관리 API
from app.api.v1.endpoints.common import stats  # 통계 API 엔드포인트
from app.api.v1.endpoints.admin import sweep  # Doc #27: 입금 Sweep 자동화 시스템
from app.api.v1.endpoints.common import transaction_analytics
from app.api.v1.endpoints.common import transactions  # 거래 관리 API 엔드포인트 - 오류 수정 완료
from app.api.v1.endpoints.partner import tronlink  # TronLink 연동 (메인 엔드포인트)
from app.api.v1.endpoints.common import users  # 사용자 관리 API 엔드포인트
from app.api.v1.endpoints.common import wallet
from app.api.v1.endpoints.common import websocket  # WebSocket 실시간 데이터 스트리밍
from app.api.v1.endpoints.common import withdrawal
from app.api.v1.endpoints.admin import withdrawal_management  # Doc #28: 파트너사 출금 관리 고도화

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
#     - admin, admin_dashboard, admin_fees, admin_partners
#     - audit-compliance, integrated_dashboard, withdrawal_management, sweep
#     - partner_onboarding, analytics, statistics, transactions, users
#
# 🤝 PARTNER ADMIN TEMPLATE (Port 3030: /frontend/partner-admin-template/
#   🎯 Purpose: Partner-specific operations and management
#   📡 APIs Used:
#     - tronlink, fee_policy
#     - authentication, balance, wallet, deposit, withdrawal (shared)
#
# 🔄 COMMON APIS: Used by both frontends with different contexts
#   - authentication: User login/auth for both admin and partner users
#   - balance: Internal balance management
#   - wallet: On-chain wallet operations
#   - deposit/withdrawal: Transaction processing
#
# ============================================================================

# === AUTHENTICATION & CORE USER OPERATIONS ===
# Used by both frontends - essential user operations
api_router.include_router(auth.router, prefix="/auth", tags=["🔐 Authentication"])
api_router.include_router(
    balance.router, prefix="/balance", tags=["💰 Balance & Payments"]
)  # Internal balance (different from wallet on-chain)
api_router.include_router(
    wallet.router, prefix="/wallet", tags=["🏦 Wallet Management"]
)  # On-chain wallet & balance
api_router.include_router(deposit.router, prefix="/deposit", tags=["💰 Balance & Payments"])
api_router.include_router(withdrawal.router, prefix="/withdrawals", tags=["💰 Balance & Payments"])

# === SUPER ADMIN DASHBOARD EXCLUSIVE ===
# Advanced administration and system monitoring

# System Administration
api_router.include_router(
    admin.router, prefix="/admin", tags=["🔧 Super Admin - Core"]
)  # Core admin operations
api_router.include_router(
    admin_dashboard_real.router, tags=["🔧 Super Admin - Dashboard"]
)  # Super admin dashboard (real implementation)
api_router.include_router(
    users.router, prefix="/users", tags=["👥 User Management"]
)  # User management
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["📊 Transaction Analytics"]
)  # Transaction admin

# Financial Management
api_router.include_router(
    fee_policy.router, prefix="/fee-policy", tags=["🤝 Partner Admin - Policy"]
)  # Partner fee policies
api_router.include_router(
    withdrawal_management.router,
    prefix="/withdrawal-management",
    tags=["🔧 Super Admin - Finance"],
)  # Advanced withdrawal controls
api_router.include_router(
    sweep.router, prefix="/sweep", tags=["🔧 Super Admin - Automation"]
)  # Deposit sweep automation

# Compliance & Security
api_router.include_router(
    audit_compliance.router, tags=["🔒 Compliance & Security"]
)  # 🔍 Frontend: /app/audit-compliance/page.tsx
# Note: Uses prefix="/audit-compliance" defined in the router itself

# Integrated Dashboard - Comprehensive partner analytics dashboard
api_router.include_router(
    integrated_dashboard.router, tags=["📊 Dashboard & Analytics"]
)  # 🔍 Frontend: /app/integrated-dashboard/page.tsx

# Analytics & Reporting
api_router.include_router(
    stats.router, tags=["📊 Dashboard & Analytics"]
)  # General system statistics
api_router.include_router(
    transaction_analytics.router, prefix="/transaction-analytics", tags=["📊 Transaction Analytics"]
)

# === PARTNER ADMIN TEMPLATE EXCLUSIVE ===
# Partner-specific operations and integrations

# TronLink Integration - Core partner functionality
api_router.include_router(
    tronlink.router, prefix="/tronlink", tags=["🤝 Partner Admin - Integration"]
)  # 🔗 TronLink wallet integration

# Partner Management
api_router.include_router(
    partner_onboarding.router, prefix="/partner-onboarding", tags=["🤝 Partner Admin - Onboarding"]
)  # Partner onboarding automation

api_router.include_router(
    partners_simple.router, prefix="/partners-simple", tags=["🤝 Partner Admin - Management"]
)  # Simple partner management

# === WEBSOCKET REAL-TIME APIS ===
# Real-time data streaming for both frontends
api_router.include_router(
    websocket.router, prefix="/ws", tags=["🔄 Real-time Data"]
)  # WebSocket real-time streaming

# Backend Optimization - System performance management (Super Admin only)
api_router.include_router(
    optimization.router, prefix="/admin/optimization", tags=["🔧 Super Admin - System"]
)  # Performance optimization


# 임시 테스트 엔드포인트
@api_router.get("/test")
async def test_endpoint():
    """API가 정상 작동하는지 테스트하기 위한 임시 엔드포인트"""
    return {"message": "API v1 is working (에너지 API 제거 완료)", "status": "success"}
