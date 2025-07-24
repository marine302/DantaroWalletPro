#!/usr/bin/env python3
"""
SuperAdminUser 테이블에 슈퍼어드민 계정 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.system_admin import SuperAdminUser
from app.core.security import get_password_hash

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_super_admin_user():
    """SuperAdminUser 테이블에 슈퍼어드민 계정 생성"""
    logger.info("Creating super admin user account...")

    # DB 세션 생성
    async with AsyncSessionLocal() as db:
        try:
            # 기존 슈퍼어드민 확인
            result = await db.execute(
                select(SuperAdminUser).filter(SuperAdminUser.email == "admin@dantaro.com")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info("Super admin user already exists")
                return
            
            # 슈퍼어드민 계정 생성
            hashed_password = get_password_hash("admin123")
            
            super_admin = SuperAdminUser(
                username="admin",
                email="admin@dantaro.com",
                hashed_password=hashed_password,
                full_name="Super Administrator",
                role="super_admin",
                permissions=["all"],
                is_active=True
            )
            
            db.add(super_admin)
            await db.commit()
            await db.refresh(super_admin)
            
            logger.info(f"Super admin user created successfully: {super_admin.email}")
            logger.info("Login credentials:")
            logger.info("  Email: admin@dantaro.com")
            logger.info("  Password: admin123")
            
        except Exception as e:
            logger.error(f"Failed to create super admin user: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(create_super_admin_user())
