#!/usr/bin/env python3
"""
테스트용 파트너 생성 스크립트
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.partner import Partner
import uuid

async def create_test_partner():
    """테스트용 파트너 생성"""
    async with AsyncSessionLocal() as db:
        try:
            # 기존 파트너 확인
            from sqlalchemy import select
            result = await db.execute(select(Partner).where(Partner.id == "test_partner_001"))
            existing_partner = result.scalar_one_or_none()
            
            if existing_partner:
                print(f"✅ 기존 테스트 파트너가 이미 존재합니다: {existing_partner.name}")
                return existing_partner
            
            # 새 파트너 생성
            partner = Partner(
                id="test_partner_001",
                name="Test Partner",
                display_name="테스트 파트너",
                domain="test.example.com",
                contact_email="test@example.com",
                contact_phone="010-1234-5678",
                business_type="test",
                api_key=str(uuid.uuid4()),
                api_secret_hash="test_secret_hash",
                status="active",
                onboarding_status="completed",
                subscription_plan="premium",
                commission_rate=0.001,
                energy_balance=1000000
            )
            
            db.add(partner)
            await db.commit()
            await db.refresh(partner)
            
            print(f"✅ 테스트 파트너 생성 완료:")
            print(f"   - ID: {partner.id}")
            print(f"   - 이름: {partner.name}")
            print(f"   - API 키: {partner.api_key}")
            print(f"   - 상태: {partner.status}")
            
            return partner
            
        except Exception as e:
            print(f"❌ 파트너 생성 실패: {e}")
            await db.rollback()
            return None

if __name__ == "__main__":
    asyncio.run(create_test_partner())
