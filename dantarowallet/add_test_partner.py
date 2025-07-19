#!/usr/bin/env python3
"""
테스트 파트너를 데이터베이스에 추가하는 스크립트
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.partner import Partner
from app.core.database import AsyncSessionLocal
from sqlalchemy import select

async def add_test_partner():
    async with AsyncSessionLocal() as db:
        try:
            # 기존 파트너 확인
            result = await db.execute(select(Partner).filter(Partner.id == '1'))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Partner already exists: {existing.name}")
                return
            
            # 새 파트너 추가
            partner = Partner(
                id='1',  # String ID
                name='Test Partner',
                contact_email='test@example.com',
                business_type='exchange',
                api_key='test-api-key',
                api_secret_hash='test-hash',
                status='active'
            )
            db.add(partner)
            await db.commit()
            print("Test partner added successfully")
            
        except Exception as e:
            print(f"Error adding partner: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_test_partner())
