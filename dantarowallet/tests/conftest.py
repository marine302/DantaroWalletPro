"""
Pytest configuration and fixtures for DantaroWallet tests.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, Generator

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, engine, get_db
from app.core.security import get_password_hash, verify_token
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async for session in get_db():
        yield session


@pytest_asyncio.fixture
async def user_token_headers(client: AsyncClient, db: AsyncSession) -> Dict[str, str]:
    """Get auth headers for a test user."""
    from sqlalchemy import select

    from app.models.balance import Balance
    from app.models.user import User

    # 기존 사용자 확인 및 삭제
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        await db.delete(existing_user)
        await db.commit()

    # 새 사용자 직접 생성
    password_hash = get_password_hash("TestPassword123!")
    user = User(
        email="test@example.com",
        password_hash=password_hash,
        is_active=True,
        is_verified=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"Test user created with ID: {user.id}")

    # 사용자 잔고 초기화
    balance = Balance(user_id=user.id, asset="USDT", amount=0, locked_amount=0)
    db.add(balance)
    await db.commit()

    # 로그인
    login_data = {"email": "test@example.com", "password": "TestPassword123!"}

    login_response = await client.post("/api/v1/auth/login", json=login_data)
    print(f"Login response: {login_response.status_code}, {login_response.text}")

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return {}


@pytest_asyncio.fixture
async def admin_token_headers(client: AsyncClient, db: AsyncSession) -> Dict[str, str]:
    """Get auth headers for an admin user."""
    # DB에 직접 관리자 생성 (register endpoint 대신 직접 DB에 쓰기)
    from sqlalchemy import select, update

    from app.models.user import User

    # 기존 사용자 확인 및 삭제
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    existing_admin = result.scalar_one_or_none()
    if existing_admin:
        await db.delete(existing_admin)
        await db.commit()

    # 새로운 관리자 생성
    password_hash = get_password_hash("AdminPassword123!")
    admin = User(
        email="admin@example.com",
        password_hash=password_hash,
        is_active=True,
        is_admin=True,  # 직접 관리자로 설정
        is_verified=True,  # 인증된 사용자로 설정
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    print(f"Admin user created with ID: {admin.id}, is_admin: {admin.is_admin}")

    # 관리자 로그인
    login_data = {"email": "admin@example.com", "password": "AdminPassword123!"}

    login_response = await client.post("/api/v1/auth/login", json=login_data)
    print(f"Admin login response: {login_response.status_code}, {login_response.text}")

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return {}


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> Any:
    """테스트용 일반 사용자 ORM 객체 반환"""
    from sqlalchemy import select

    from app.models.user import User

    # 기존 사용자 확인
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    test_user = result.scalar_one_or_none()

    # 사용자가 없으면 생성
    if not test_user:
        password_hash = get_password_hash("TestPassword123!")
        test_user = User(
            email="test@example.com",
            password_hash=password_hash,
            is_active=True,
            is_admin=False,
            is_verified=True,
        )
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)

    return test_user


@pytest_asyncio.fixture
async def test_admin_user(db: AsyncSession) -> Any:
    """테스트용 관리자 ORM 객체 반환"""
    from sqlalchemy import select

    from app.models.user import User

    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    admin_user = result.scalar_one_or_none()
    return admin_user


# 테스트 데이터 자동 정리 (예시: 사용자, 지갑, 거래 등)
@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(db: AsyncSession):
    """테스트 후 테스트용 사용자/관리자 데이터 자동 삭제"""
    yield
    from app.models.user import User

    await db.execute(
        User.__table__.delete().where(
            User.email.in_(["test@example.com", "admin@example.com"])
        )
    )
    await db.commit()


@pytest_asyncio.fixture(autouse=True, scope="function")
async def truncate_all_tables():
    """각 테스트 시작 전 DB의 모든 테이블을 truncate하여 데이터 중복 방지"""
    async with engine.begin() as conn:
        # 외래 키 제약 조건 일시적으로 비활성화
        await conn.execute(sqlalchemy.text("PRAGMA foreign_keys = OFF"))

        # 테이블 순서를 역순으로 정렬하여 종속성 문제 방지
        for table in reversed(Base.metadata.sorted_tables):
            try:
                await conn.execute(sqlalchemy.text(f"DELETE FROM {table.name}"))
            except Exception as e:
                # 테이블이 존재하지 않는 경우 무시
                if "no such table" not in str(e):
                    raise

        # 외래 키 제약 조건 다시 활성화
        await conn.execute(sqlalchemy.text("PRAGMA foreign_keys = ON"))
        await conn.commit()
    yield


# fixture 네이밍 안내: 테스트에서는 반드시 user_token_headers, admin_token_headers fixture 이름을 사용해야 합니다.
# 주의: 이 fixture들은 이미 비동기 처리되어 있으므로 추가로 await를 사용하지 않습니다.
# 예시: def test_function(client, user_token_headers):
