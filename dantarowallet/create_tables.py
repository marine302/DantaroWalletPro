#!/usr/bin/env python3
"""
데이터베이스 테이블 직접 생성
"""
import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, engine

async def create_tables():
    """모든 테이블 생성"""
    try:
        print("🔄 모델 import 시작...")
        # 모든 모델 import
        from app.models.balance import Balance
        from app.models.deposit import Deposit
        from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog, EnergyPriceHistory
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
            PartnerPolicyCalculationLog
        )
        from app.models.withdrawal_policy import PartnerWithdrawalPolicy
        from app.models.fee_config import FeeCalculationLog
        from app.models.transaction import Transaction
        from app.models.transaction_analytics import TransactionAlert, TransactionSummary
        from app.models.user import User
        from app.models.wallet import Wallet
        from app.models.withdrawal import Withdrawal
        from app.models.partner_wallet import PartnerWallet
        from app.models.sweep import (
            HDWalletMaster,
            UserDepositAddress, 
            SweepConfiguration,
            SweepLog,
            SweepQueue
        )
        print("✅ 모델 import 완료")
        
        print("🔄 테이블 생성 시작...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print('✅ All tables created successfully')
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(create_tables())
