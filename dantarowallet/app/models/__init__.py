"""
데이터베이스 모델 모듈.
모든 SQLAlchemy 모델을 한 곳에서 가져올 수 있도록 합니다.
"""

from app.models.audit import (
    AuditEventType,
    AuditLog,
    ComplianceCheck,
    SuspiciousActivity,
)
from app.models.balance import Balance
from app.models.base import BaseModel
# 에너지 관련 모델 (Doc-40, Doc-41 구현)
from app.models.company_wallet import CompanyWallet, CompanyWalletType
from app.models.energy_allocation import AllocationStatus, EnergyAllocation
from app.models.energy_pool import EnergyPool, EnergySourceStatus, EnergySourceType
from app.models.energy_supplier import EnergySupplier, SupplierStatus, SupplierType
from app.models.deposit import Deposit
from app.models.fee_config import FeeCalculationLog
from app.models.fee_policy import (
    FeeTier,
    FeeType,
    PartnerFeePolicy,
    PartnerPolicyCalculationLog,
    UserTier,
    WithdrawalPolicy,
)
from app.models.partner import Partner
from app.models.partner_api_log import PartnerApiLog
from app.models.partner_history import (
    PartnerApiUsage,
    PartnerDailyStatistics,
    PartnerDeployment,
    PartnerEnergyAllocation,
    PartnerEnergyUsageHistory,
    PartnerFeeConfigHistory,
    PartnerFeeRevenue,
    PartnerOnboardingStep,
)
from app.models.partner_onboarding import (
    ChecklistCategory,
    OnboardingChecklist,
    OnboardingLog,
    OnboardingStatus,
    OnboardingStep,
    OnboardingStepStatus,
    PartnerOnboarding,
)
from app.models.partner_wallet import (
    PartnerWallet,
    TransactionStatus,
    WalletPurpose,
    WalletType,
)
from app.models.sweep import (
    HDWalletMaster,
    SweepConfiguration,
    SweepLog,
    SweepQueue,
    UserDepositAddress,
)
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction_analytics import (
    AlertLevel,
    AlertType,
    TransactionAlert,
    TransactionSummary,
)
from app.models.user import User
from app.models.wallet import Wallet
from app.models.withdrawal import Withdrawal, WithdrawalPriority, WithdrawalStatus
from app.models.withdrawal_policy import (
    PartnerWithdrawalPolicy,
    WithdrawalApprovalRule,
    WithdrawalWhitelist,
)

__all__ = [
    "BaseModel",
    "User",
    "Balance",
    "Transaction",
    "TransactionType",
    "TransactionStatus",
    "TransactionDirection",
    "Wallet",
    "Deposit",
    "Withdrawal",
    "WithdrawalStatus",
    "WithdrawalPriority",
    "TransactionAlert",
    "TransactionSummary",
    "AlertLevel",
    "AlertType",
    "Partner",
    "PartnerApiLog",
    # 에너지 관련 모델 (Doc-40, Doc-41)
    "CompanyWallet",
    "CompanyWalletType",
    "EnergyAllocation",
    "AllocationStatus",
    "EnergyPool",
    "EnergySourceType",
    "EnergySourceStatus",
    "EnergySupplier",
    "SupplierType",
    "SupplierStatus",
    # Partner History 모델
    "PartnerApiUsage",
    "PartnerDailyStatistics",
    "PartnerFeeRevenue",
    "PartnerFeeConfigHistory",
    "PartnerOnboardingStep",
    "PartnerDeployment",
    # Doc-26: 수수료 및 정책 모델
    "PartnerFeePolicy",
    "FeeTier",
    "PartnerWithdrawalPolicy",
    "UserTier",
    "PartnerPolicyCalculationLog",
    "FeeType",
    "WithdrawalPolicy",
    "FeeCalculationLog",
    # Partner Wallet 모델
    "PartnerWallet",
    "WalletType",
    "WalletPurpose",
    "TransactionStatus",
    # Doc-27: Sweep 자동화 모델
    "HDWalletMaster",
    "UserDepositAddress",
    "SweepConfiguration",
    "SweepLog",
    "SweepQueue",
    # Doc-28: 출금 관리 고도화 모델
    "WithdrawalApprovalRule",
    "WithdrawalWhitelist",
    # Doc-29: 온보딩 자동화 모델
    "PartnerOnboarding",
    "OnboardingStep",
    "OnboardingChecklist",
    "OnboardingLog",
    "OnboardingStatus",
    "OnboardingStepStatus",
    "ChecklistCategory",
    # Audit 모델
    "AuditLog",
    "AuditEventType",
    "ComplianceCheck",
    "SuspiciousActivity",
]
