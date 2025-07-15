#!/usr/bin/env python3
"""통합 대시보드용 샘플 데이터 생성"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.wallet import Wallet
from app.models.transaction import Transaction  
from app.models.user import User
from app.models.partner import Partner
from app.models.energy_pool import EnergyPoolModel
from app.core.database import get_db

async def create_integrated_sample_data():
    """통합 대시보드용 샘플 데이터 생성"""
    
    # 데이터베이스 연결
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            print("🔄 통합 대시보드용 샘플 데이터 생성 시작...")
            
            # 1. 파트너 데이터 확인 및 생성
            partner_id = "partner_001"  # String ID로 변경
            partner = await db.get(Partner, partner_id)
            if not partner:
                partner = Partner(
                    id=partner_id,
                    name="DantaroWallet Test Partner",
                    display_name="테스트 파트너",
                    contact_email="partner@dantarowallet.com",
                    contact_phone="010-1234-5678",
                    business_type="crypto_exchange",
                    status="active",
                    onboarding_status="completed",
                    commission_rate=0.02,
                    api_key="test_api_key_123",
                    api_secret_hash="hashed_secret_123",
                    monthly_limit=30000000.0,
                    energy_balance=1000000.0
                )
                db.add(partner)
                await db.commit()
                print(f"✅ 파트너 생성: {partner.name}")
            
            # 2. 멀티 지갑 데이터 생성
            wallet_data = [
                {"type": "hot", "count": 3, "balance_range": (1000, 5000)},
                {"type": "warm", "count": 2, "balance_range": (10000, 50000)},
                {"type": "cold", "count": 1, "balance_range": (100000, 500000)}
            ]
            
            created_wallets = []
            for wallet_info in wallet_data:
                for i in range(wallet_info["count"]):
                    wallet_address = f"T{wallet_info['type'].upper()}{random.randint(100000, 999999)}{chr(65 + i)}"
                    balance = random.uniform(*wallet_info["balance_range"])
                    
                    wallet = Wallet(
                        address=wallet_address,
                        private_key=f"private_key_{wallet_address}",
                        partner_id=partner_id,
                        wallet_type=wallet_info["type"],
                        status="active",
                        balance=Decimal(str(balance)),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.add(wallet)
                    created_wallets.append(wallet)
            
            await db.commit()
            print(f"✅ 지갑 생성: {len(created_wallets)}개")
            
            # 3. 사용자 데이터 생성
            user_count = 50  # 줄여서 테스트
            created_users = []
            for i in range(user_count):
                is_active = random.choice([True, True, True, False])  # 75% 활성 사용자
                user = User(
                    email=f"user{i+1:03d}@test.com",
                    password_hash="hashed_password_123",  # 테스트용 해시
                    is_active=is_active,
                    is_verified=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                )
                db.add(user)
                created_users.append(user)
            
            await db.commit()
            print(f"✅ 사용자 생성: {len(created_users)}개")
            
            # 4. 거래 데이터 생성 (최근 30일)
            transaction_count = 500
            transaction_types = ["deposit", "withdrawal", "transfer", "fee"]
            
            for i in range(transaction_count):
                # 거래 시간 분포 (최근일수록 더 많이)
                days_ago = random.choices(
                    range(30), 
                    weights=[30-i for i in range(30)]
                )[0]
                
                transaction = Transaction(
                    id=f"tx_{i+1:06d}",
                    from_address=random.choice(created_wallets).address,
                    to_address=random.choice(created_wallets).address,
                    amount=Decimal(str(random.uniform(10, 10000))),
                    transaction_type=random.choice(transaction_types),
                    status="completed",
                    partner_id=partner_id,
                    user_id=random.choice(created_users).id,
                    network_fee=Decimal(str(random.uniform(1, 10))),
                    created_at=datetime.utcnow() - timedelta(
                        days=days_ago, 
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                )
                db.add(transaction)
            
            await db.commit()
            print(f"✅ 거래 데이터 생성: {transaction_count}개")
            
            # 5. 에너지 풀 데이터 생성
            energy_pools = [
                {
                    "name": "Main Energy Pool",
                    "total_energy": 1000000,
                    "available_energy": 750000,
                    "frozen_energy": 250000
                },
                {
                    "name": "Reserve Energy Pool", 
                    "total_energy": 500000,
                    "available_energy": 400000,
                    "frozen_energy": 100000
                }
            ]
            
            for pool_data in energy_pools:
                energy_pool = EnergyPoolModel(
                    name=pool_data["name"],
                    partner_id=partner_id,
                    total_energy=pool_data["total_energy"],
                    available_energy=pool_data["available_energy"],
                    frozen_energy=pool_data["frozen_energy"],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
                )
                db.add(energy_pool)
            
            await db.commit()
            print(f"✅ 에너지 풀 생성: {len(energy_pools)}개")
            
            print("\n🎉 통합 대시보드용 샘플 데이터 생성 완료!")
            print(f"📊 생성된 데이터:")
            print(f"   - 파트너: 1개")
            print(f"   - 지갑: {len(created_wallets)}개")
            print(f"   - 사용자: {len(created_users)}개")
            print(f"   - 거래: {transaction_count}개")
            print(f"   - 에너지 풀: {len(energy_pools)}개")
            
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            await db.rollback()
            raise
        finally:
            await db.close()
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_integrated_sample_data())
