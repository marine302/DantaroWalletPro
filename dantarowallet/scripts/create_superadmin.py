#!/usr/bin/env python3
"""
슈퍼어드민 계정 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_superadmin():
    """슈퍼어드민 계정 생성"""
    logger.info("Creating superadmin account...")

    # DB 세션 생성
    async with AsyncSessionLocal() as db:
        try:
            # 기존 슈퍼어드민 확인
            result = await db.execute(
                select(User).filter(User.email == "superadmin@dantaro.com")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info("Superadmin already exists")
                return
            
            # 슈퍼어드민 계정 생성
            hashed_password = get_password_hash("SuperAdmin123!")
            
            superadmin = User(
                email="superadmin@dantaro.com",
                password_hash=hashed_password,
                is_active=True,
                is_admin=True,
                is_verified=True
            )
            
            db.add(superadmin)
            await db.commit()
            await db.refresh(superadmin)
            
            logger.info(f"Superadmin created successfully: {superadmin.email}")
            logger.info("Login credentials:")
            logger.info("  Email: superadmin@dantaro.com")
            logger.info("  Password: SuperAdmin123!")
            
        except Exception as e:
            logger.error(f"Failed to create superadmin: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(create_superadmin())
