#!/usr/bin/env python3
"""
테스트 파트너 정보 조회 스크립트
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.partner import Partner
from sqlalchemy import select

async def get_test_partner_info():
    """테스트 파트너 정보 조회"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Partner).where(Partner.id == "test_partner_001"))
            partner = result.scalar_one_or_none()
            
            if partner:
                print(f"📋 테스트 파트너 정보:")
                print(f"   - ID: {partner.id}")
                print(f"   - 이름: {partner.name}")
                print(f"   - API 키: {partner.api_key}")
                print(f"   - 상태: {partner.status}")
                print(f"   - 온보딩 상태: {partner.onboarding_status}")
                return partner.api_key
            else:
                print("❌ 테스트 파트너를 찾을 수 없습니다")
                return None
                
        except Exception as e:
            print(f"❌ 파트너 조회 실패: {e}")
            return None

if __name__ == "__main__":
    asyncio.run(get_test_partner_info())
