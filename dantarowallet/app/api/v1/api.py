"""
API 버전 1의 라우터 정의
모든 API 엔드포인트를 중앙 집중식으로 관리합니다.
"""

from fastapi import APIRouter

# API 버전 1의 메인 라우터
api_router = APIRouter()

# ============================================================================
# IMPORT STATEMENTS - 카테고리별 정리
# ============================================================================

# === ADMIN ENDPOINTS ===
from app.api.v1.endpoints.admin import admin_dashboard
from app.api.v1.endpoints.admin import audit_compliance
from app.api.v1.endpoints.admin import dashboard as admin_dashboard_real
from app.api.v1.endpoints.admin import deployment_management
from app.api.v1.endpoints.admin import energy_pool
from app.api.v1.endpoints.admin import fees
from app.api.v1.endpoints.admin import monitoring
from app.api.v1.endpoints.admin import optimization
from app.api.v1.endpoints.admin import partners as admin_partners
from app.api.v1.endpoints.admin import sweep
from app.api.v1.endpoints.admin import system
from app.api.v1.endpoints.admin import withdrawal_management

# === PARTNER ENDPOINTS ===
from app.api.v1.endpoints.partner import energy as partner_energy
from app.api.v1.endpoints.partner import fee_policy
from app.api.v1.endpoints.partner import partner_onboarding
from app.api.v1.endpoints.partner import partners_simple
from app.api.v1.endpoints.partner import tronlink
from app.api.v1.endpoints import partner

# === COMMON ENDPOINTS ===
from app.api.v1.endpoints.common import auth
from app.api.v1.endpoints.common import balance
from app.api.v1.endpoints.common import deposit
from app.api.v1.endpoints.common import stats
from app.api.v1.endpoints.common import transaction_analytics
from app.api.v1.endpoints.common import transactions
from app.api.v1.endpoints.common import users
from app.api.v1.endpoints.common import wallet
from app.api.v1.endpoints.common import websocket
from app.api.v1.endpoints.common import withdrawal

# === SERVICES ===
from app.services.dashboard import integrated_dashboard

# ============================================================================
# ROUTER REGISTRATION - 기능별 그룹화
# ============================================================================

# === 🔐 AUTHENTICATION & CORE USER OPERATIONS ===
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# === 💰 FINANCIAL OPERATIONS ===
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(deposit.router, prefix="/deposit", tags=["deposit"])
api_router.include_router(withdrawal.router, prefix="/withdrawals", tags=["withdrawal"])

# === 🔐 SUPER ADMIN DASHBOARD ===
api_router.include_router(admin_dashboard.router, prefix="/admin/dashboard", tags=["admin_dashboard"])
api_router.include_router(admin_dashboard_real.router, tags=["admin_dashboard"])
api_router.include_router(fees.router, prefix="/admin/fees", tags=["admin_fees"])
api_router.include_router(monitoring.router, prefix="/admin/monitoring", tags=["admin"])
api_router.include_router(admin_partners.router, prefix="/admin/partners", tags=["admin_partners"])
api_router.include_router(system.router, prefix="/admin/system", tags=["admin"])
api_router.include_router(deployment_management.router, prefix="/admin/deployment", tags=["admin"])
api_router.include_router(energy_pool.router, prefix="/admin/energy-pool", tags=["admin_energy_pool"])
api_router.include_router(withdrawal_management.router, prefix="/withdrawal-management", tags=["withdrawal_management"])
api_router.include_router(sweep.router, prefix="/sweep", tags=["sweep"])
api_router.include_router(audit_compliance.router, tags=["audit-compliance"])
api_router.include_router(optimization.router, prefix="/admin/optimization", tags=["optimization"])

# === 🤝 PARTNER ADMIN TEMPLATE ===
api_router.include_router(tronlink.router, prefix="/tronlink", tags=["tronlink"])
api_router.include_router(partner_onboarding.router, prefix="/partner-onboarding", tags=["partner_onboarding"])
api_router.include_router(partners_simple.router, prefix="/partners-simple", tags=["partners_simple"])
api_router.include_router(fee_policy.router, prefix="/fee-policy", tags=["fee_policy"])
api_router.include_router(partner.router, prefix="/partner", tags=["partner"])
api_router.include_router(partner_energy.router, prefix="/partner/energy", tags=["partner_energy"])

# === 👥 USER & TRANSACTION MANAGEMENT ===
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])

# === 📊 ANALYTICS & DASHBOARD ===
api_router.include_router(stats.router, tags=["analytics"])
api_router.include_router(transaction_analytics.router, prefix="/transaction-analytics", tags=["analytics"])
api_router.include_router(integrated_dashboard.router, tags=["integrated_dashboard"])

# === 🔄 REAL-TIME SERVICES ===
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# === 🧪 TESTING ===
@api_router.get("/test", tags=["test"])
async def test_endpoint():
    """API가 정상 작동하는지 테스트하기 위한 엔드포인트"""
    return {"message": "API v1 is working", "status": "success"}
