#!/usr/bin/env python3
"""
관리자 계정 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

import logging

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.user import User

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def make_admin():
    """기존 사용자를 관리자로 만들기"""
    async with AsyncSessionLocal() as db:
        # admin@dantarowallet.com 사용자 찾기
        result = await db.execute(
            select(User).filter(User.email == "admin@dantarowallet.com")
        )
        user = result.scalar_one_or_none()

        if user:
            # 관리자 권한 부여
            user.is_admin = True
            user.is_verified = True
            user.is_active = True
            await db.commit()
            logger.info(f"User {user.email} is now an admin")
        else:
            logger.error("User admin@dantarowallet.com not found")


if __name__ == "__main__":
    asyncio.run(make_admin())
