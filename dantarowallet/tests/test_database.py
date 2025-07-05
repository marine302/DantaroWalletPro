"""
데이터베이스 모델 테스트.
User 및 Balance 모델의 기능과 제약 조건을 테스트합니다.
"""
from decimal import Decimal

import pytest
from app.core.database import AsyncSessionLocal, check_database_connection
from app.models.balance import Balance
from app.models.user import User
from sqlalchemy import select


@pytest.mark.asyncio
async def test_database_connection():
    """데이터베이스 연결 테스트"""
    assert await check_database_connection() is True


@pytest.mark.asyncio
async def test_create_user():
    """사용자 생성 테스트"""
    async with AsyncSessionLocal() as session:
        # 사용자 생성
        user = User(
            email="test@example.com", password_hash="hashed_password", is_active=True
        )
        session.add(user)
        await session.commit()

        # 조회
        result = await session.execute(select(User).filter_by(email="test@example.com"))
        saved_user = result.scalar_one_or_none()

        assert saved_user is not None
        assert saved_user.email == "test@example.com"
        assert saved_user.is_active is True

        # 정리
        await session.delete(saved_user)
        await session.commit()


@pytest.mark.asyncio
async def test_create_balance():
    """잔고 생성 테스트"""
    async with AsyncSessionLocal() as session:
        # 사용자 먼저 생성
        user = User(email="balance_test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        # 잔고 생성
        balance = Balance(
            user_id=user.id,
            asset="USDT",
            amount=Decimal("100.50"),
            locked_amount=Decimal("10.00"),
        )
        session.add(balance)
        await session.commit()

        # 검증
        assert balance.available_amount == Decimal("90.50")
        assert balance.can_withdraw(Decimal("90.00")) is True
        assert balance.can_withdraw(Decimal("100.00")) is False

        # 정리
        await session.delete(balance)
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_balance_constraints():
    """잔고 제약 조건 테스트"""
    async with AsyncSessionLocal() as session:
        # 사용자 생성
        user = User(email="constraint_test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        # 같은 사용자, 같은 자산으로 두 개의 잔고 생성 시도
        balance1 = Balance(user_id=user.id, asset="USDT")
        balance2 = Balance(user_id=user.id, asset="USDT")

        session.add(balance1)
        await session.commit()

        session.add(balance2)
        with pytest.raises(Exception):  # UniqueConstraint violation
            await session.commit()

        await session.rollback()

        # 정리
        await session.delete(balance1)
        await session.delete(user)
        await session.commit()
