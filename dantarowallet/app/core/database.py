"""
데이터베이스 연결 및 세션 관리 모듈.
SQLAlchemy 2.0 기반 비동기 ORM을 설정합니다.
"""
import logging
from typing import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

# 먼저 settings에 TESTING 추가 여부 확인
is_testing = getattr(settings, "TESTING", False)

# 데이터베이스 엔진 생성
# SQLite를 사용할 때는 pool_size와 max_overflow를 설정하지 않음
if "sqlite" in settings.DATABASE_URL:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # SQL 로깅 (개발 환경에서만)
        pool_pre_ping=True,  # 연결 상태 체크
        poolclass=NullPool if is_testing else None,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # SQL 로깅 (개발 환경에서만)
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # 연결 상태 체크
        # 테스트 환경에서는 연결 풀 비활성화
        poolclass=NullPool if is_testing else None,
    )

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base 클래스
Base = declarative_base()


# 의존성 주입용 세션 getter
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입을 위한 데이터베이스 세션 생성기.
    예외 발생 시 자동 롤백, 세션은 항상 닫힘.

    Yields:
        AsyncSession: SQLAlchemy 비동기 세션 인스턴스
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 데이터베이스 연결 테스트
async def check_database_connection() -> bool:
    """
    데이터베이스 연결 상태를 확인합니다.

    Returns:
        bool: 연결 성공 여부
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# 테이블 생성 (개발용)
async def create_tables() -> None:
    """
    데이터베이스 테이블을 생성합니다.
    주로 개발 또는 테스트 환경에서 사용됩니다.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")


# 테이블 삭제 (테스트용)
async def drop_tables() -> None:
    """
    데이터베이스 테이블을 삭제합니다.
    주로 테스트 환경에서 사용됩니다.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")

# 동기 데이터베이스 세션 (파트너 관리용)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 동기 엔진 생성
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {},
)

# 동기 세션 로컬
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    """동기 DB 세션 의존성"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """
    동기 데이터베이스 세션을 반환합니다.
    
    Returns:
        Session: SQLAlchemy 동기 세션 인스턴스
    """
    return SyncSessionLocal()
