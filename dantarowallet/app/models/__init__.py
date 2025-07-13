"""
데이터베이스 모델 모듈.
모든 SQLAlchemy 모델을 한 곳에서 가져올 수 있도록 합니다.
"""
from app.models.balance import Balance
from app.models.base import BaseModel
from app.models.deposit import Deposit
from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog, EnergyPriceHistory
from app.models.external_energy import ExternalEnergyProvider, ExternalEnergyPriceHistory
from app.models.energy_usage_history import EnergyUsageHistory
from app.models.partner import Partner
from app.models.partner_history import (
    PartnerApiUsage,
    PartnerDailyStatistics,
    PartnerEnergyAllocation,
    PartnerEnergyUsageHistory,
    PartnerFeeRevenue,
    PartnerFeeConfigHistory,
    PartnerOnboardingStep,
    PartnerDeployment
)
from app.models.fee_policy import (
    PartnerFeePolicy, 
    FeeTier, 
    PartnerEnergyPolicy, 
    UserTier, 
    PartnerPolicyCalculationLog,
    FeeType,
    WithdrawalPolicy,
    EnergyPolicy
)
from app.models.fee_config import FeeCalculationLog
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
from app.models.partner_wallet import PartnerWallet, WalletType, WalletPurpose, TransactionStatus
from app.models.sweep import (
    HDWalletMaster,
    UserDepositAddress, 
    SweepConfiguration,
    SweepLog,
    SweepQueue
)
from app.models.withdrawal_policy import (
    PartnerWithdrawalPolicy,
    WithdrawalApprovalRule,
    WithdrawalWhitelist
)
from app.models.partner_onboarding import (
    PartnerOnboarding,
    OnboardingStep,
    OnboardingChecklist,
    OnboardingLog,
    OnboardingStatus,
    OnboardingStepStatus,
    ChecklistCategory
)
from app.models.audit import AuditLog, AuditEventType, ComplianceCheck, SuspiciousActivity

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
    "EnergyPoolModel",
    "EnergyUsageLog",
    "EnergyPriceHistory",
    "EnergyUsageHistory",
    "Partner",
    # Partner History 모델
    "PartnerApiUsage",
    "PartnerDailyStatistics",
    "PartnerEnergyAllocation",
    "PartnerEnergyUsageHistory",
    "PartnerFeeRevenue",
    "PartnerFeeConfigHistory",
    "PartnerOnboardingStep",
    "PartnerDeployment",
    # Doc-26: 수수료 및 정책 모델
    "PartnerFeePolicy",
    "FeeTier", 
    "PartnerWithdrawalPolicy",
    "PartnerEnergyPolicy",
    "UserTier",
    "PartnerPolicyCalculationLog",
    "FeeType",
    "WithdrawalPolicy",
    "EnergyPolicy",
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
