#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트.
개발 및 테스트 환경에서 데이터베이스를 초기화합니다.
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

import logging

from app.core.config import settings
from app.core.database import check_database_connection, create_tables, engine

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """데이터베이스 초기화"""
    logger.info("Initializing database...")

    # 연결 확인
    if not await check_database_connection():
        logger.error("Failed to connect to database")
        return False

    # 개발 환경에서만 테이블 생성 (운영에서는 Alembic 사용)
    if settings.DEBUG:
        await create_tables()
        logger.info("Database tables created successfully")

    return True


if __name__ == "__main__":
    asyncio.run(init_db())
