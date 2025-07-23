#!/usr/bin/env python3
"""
테스트용 샘플 데이터 생성 스크립트
"""
import asyncio
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.audit import AuditLog, SuspiciousActivity
from app.models.external_energy import (
    EnergyProviderType,
    ExternalEnergyProvider,
    ExternalEnergyPurchase,
    PurchaseStatus,
)
from app.models.partner_onboarding import OnboardingStatus, PartnerOnboarding
from app.models.user import User

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_users():
    """테스트용 일반 사용자들 생성"""
    logger.info("Creating sample users...")

    async with AsyncSessionLocal() as db:
        try:
            # 일반 사용자들 생성
            users_data = [
                {"email": "user1@test.com", "password": "User123!"},
                {"email": "user2@test.com", "password": "User123!"},
                {"email": "user3@test.com", "password": "User123!"},
                {"email": "partner1@company.com", "password": "Partner123!"},
                {"email": "partner2@company.com", "password": "Partner123!"},
            ]

            for user_data in users_data:
                user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    is_active=True,
                    is_admin=False,
                    is_verified=True,
                )
                db.add(user)

            await db.commit()
            logger.info("Sample users created successfully")

        except Exception as e:
            logger.error(f"Failed to create sample users: {e}")
            await db.rollback()


async def create_sample_audit_data():
    """테스트용 감사 데이터 생성"""
    logger.info("Creating sample audit data...")

    async with AsyncSessionLocal() as db:
        try:
            # 감사 로그 생성
            audit_logs = []
            for i in range(20):
                audit_log = AuditLog(
                    user_id=random.randint(1, 5),
                    action=random.choice(
                        ["LOGIN", "WITHDRAWAL", "TRANSFER", "DEPOSIT"]
                    ),
                    resource_type="transaction",
                    resource_id=f"tx_{i:06d}",
                    details={
                        "amount": random.randint(100, 10000),
                        "currency": "USDT",
                        "ip_address": f"192.168.1.{random.randint(1, 255)}",
                        "user_agent": "Mozilla/5.0...",
                    },
                    ip_address=f"192.168.1.{random.randint(1, 255)}",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    timestamp=datetime.utcnow()
                    - timedelta(hours=random.randint(1, 72)),
                )
                audit_logs.append(audit_log)

            db.add_all(audit_logs)

            # 의심스러운 활동 생성
            suspicious_activities = []
            for i in range(10):
                activity = SuspiciousActivity(
                    user_id=random.randint(1, 5),
                    activity_type=random.choice(
                        ["LARGE_TRANSACTION", "RAPID_TRANSACTIONS", "UNUSUAL_PATTERN"]
                    ),
                    description=f"Suspicious activity detected: {random.choice(['Large withdrawal', 'Multiple rapid transactions', 'Unusual login pattern'])}",
                    risk_score=random.randint(20, 95),
                    details={
                        "transaction_amount": random.randint(5000, 50000),
                        "frequency": random.randint(1, 10),
                        "time_window": "5 minutes",
                    },
                    status=random.choice(["pending", "investigating", "resolved"]),
                    detected_at=datetime.utcnow()
                    - timedelta(hours=random.randint(1, 48)),
                )
                suspicious_activities.append(activity)

            db.add_all(suspicious_activities)
            await db.commit()
            logger.info("Sample audit data created successfully")

        except Exception as e:
            logger.error(f"Failed to create sample audit data: {e}")
            await db.rollback()


async def create_sample_energy_data():
    """테스트용 에너지 데이터 생성"""
    logger.info("Creating sample energy data...")

    async with AsyncSessionLocal() as db:
        try:
            # 외부 에너지 공급자 생성
            providers_data = [
                {
                    "provider_type": "justlend",
                    "name": "JustLend Energy Market",
                    "api_endpoint": "https://api.justlend.org/energy",
                    "is_active": True,
                    "priority": 1,
                    "last_price": 0.00028,
                    "success_rate": 98.5,
                    "max_daily_purchase": 500000,
                },
                {
                    "provider_type": "tronnrg",
                    "name": "TronNRG",
                    "api_endpoint": "https://api.tronnrg.com/energy",
                    "is_active": True,
                    "priority": 2,
                    "last_price": 0.00032,
                    "success_rate": 96.8,
                    "max_daily_purchase": 300000,
                },
                {
                    "provider_type": "tronscan",
                    "name": "TRONSCAN Energy",
                    "api_endpoint": "https://api.tronscan.io/energy",
                    "is_active": True,
                    "priority": 3,
                    "last_price": 0.00035,
                    "success_rate": 94.2,
                    "max_daily_purchase": 200000,
                },
            ]

            providers = []
            for provider_data in providers_data:
                provider = ExternalEnergyProvider(
                    provider_type=provider_data["provider_type"],
                    name=provider_data["name"],
                    api_endpoint=provider_data["api_endpoint"],
                    is_active=provider_data["is_active"],
                    priority=provider_data["priority"],
                    last_price=provider_data["last_price"],
                    price_updated_at=datetime.utcnow(),
                    success_rate=provider_data["success_rate"],
                    average_response_time=random.randint(100, 500),
                    max_daily_purchase=provider_data["max_daily_purchase"],
                )
                providers.append(provider)

            db.add_all(providers)
            await db.commit()

            # 에너지 구매 기록 생성
            purchases = []
            for i in range(15):
                price_per_energy = Decimal(str(random.uniform(0.00025, 0.00040)))
                purchase = ExternalEnergyPurchase(
                    provider_id=random.randint(1, 3),
                    energy_amount=random.randint(10000, 100000),
                    price_per_energy=price_per_energy,
                    total_cost=Decimal(str(random.randint(10000, 100000)))
                    * price_per_energy,
                    purchase_type=random.choice(["manual", "auto"]),
                    status=random.choice(
                        [
                            PurchaseStatus.COMPLETED,
                            PurchaseStatus.PENDING,
                            PurchaseStatus.FAILED,
                        ]
                    ),
                    created_at=datetime.utcnow()
                    - timedelta(hours=random.randint(1, 72)),
                )
                purchases.append(purchase)

            db.add_all(purchases)
            await db.commit()
            logger.info("Sample energy data created successfully")

        except Exception as e:
            logger.error(f"Failed to create sample energy data: {e}")
            await db.rollback()


async def create_sample_partner_data():
    """테스트용 파트너 온보딩 데이터 생성"""
    logger.info("Creating sample partner data...")

    async with AsyncSessionLocal() as db:
        try:
            # 파트너 온보딩 데이터 생성
            partners_data = []
            for i in range(10):
                partners_data.append(
                    {
                        "partner_id": f"PARTNER_{i+1:03d}",
                        "status": random.choice(
                            [
                                OnboardingStatus.PENDING,
                                OnboardingStatus.REGISTRATION,
                                OnboardingStatus.COMPLETED,
                            ]
                        ),
                        "current_step": random.randint(1, 6),
                    }
                )

            partners = []
            for partner_data in partners_data:
                partner = PartnerOnboarding(
                    partner_id=partner_data["partner_id"],
                    status=partner_data["status"],
                    current_step=partner_data["current_step"],
                    progress_percentage=partner_data["current_step"]
                    * 16,  # 6단계이므로 100/6 ≈ 16
                    created_at=datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                )
                partners.append(partner)

            db.add_all(partners)
            await db.commit()
            logger.info("Sample partner data created successfully")

        except Exception as e:
            logger.error(f"Failed to create sample partner data: {e}")
            await db.rollback()


async def main():
    """메인 실행 함수"""
    logger.info("🚀 Creating sample data for testing...")

    await create_sample_users()
    await create_sample_audit_data()
    await create_sample_energy_data()
    await create_sample_partner_data()

    logger.info("✅ All sample data created successfully!")
    logger.info("You can now test the dashboard with real data.")


if __name__ == "__main__":
    asyncio.run(main())
