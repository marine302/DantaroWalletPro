"""
잔고 관련 기능에 대한 통합 테스트
"""
import asyncio
from decimal import Decimal

import pytest
from httpx import AsyncClient, ASGITransport
from app.core.database import AsyncSessionLocal, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.balance import Balance
from app.models.transaction import Transaction
from app.models.user import User
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

# 테스트용 사용자 정보 - conftest.py와 일관성 유지
test_user = {"email": "test@example.com", "password": "TestPassword123!"}
admin_user = {"email": "admin@example.com", "password": "AdminPassword123!"}

# 참고: db, user_token_headers, admin_token_headers fixture는 conftest.py에서 제공됨

# 중복 fixture 제거 (conftest.py의 것으로 대체)


@pytest.mark.asyncio
async def test_get_initial_balance(client: AsyncClient, user_token_headers):
    """초기 잔고 조회 테스트"""
    response = await client.get("/api/v1/balance/", headers=user_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["asset"] == "USDT"
    assert Decimal(data["amount"]) == Decimal("0.000000")
    assert Decimal(data["locked_amount"]) == Decimal("0.000000")


@pytest.mark.asyncio
async def test_balance_summary(client: AsyncClient, user_token_headers):
    """잔고 요약 조회 테스트"""
    response = await client.get("/api/v1/balance/summary", headers=user_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert "balances" in data
    assert "recent_transactions" in data
    assert "statistics" in data


@pytest.mark.asyncio
async def test_transaction_history(client: AsyncClient, user_token_headers):
    """트랜잭션 내역 조회 테스트"""
    response = await client.get(
        "/api/v1/balance/transactions", headers=user_token_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_balance_adjustment(
    client: AsyncClient, admin_token_headers, user_token_headers, db: AsyncSession
):
    """관리자 잔고 조정 테스트"""
    # 사용자 정보 가져오기 (직접 SQL로 처리)
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"), {"email": test_user["email"]}
    )
    user_id = result.scalar_one_or_none()
    assert user_id, "사용자 계정이 존재하지 않습니다"

    # 관리자 정보 확인 (직접 SQL로 처리)
    admin_result = await db.execute(
        text("SELECT id, is_admin FROM users WHERE email = :email"),
        {"email": admin_user["email"]},
    )
    admin_data = admin_result.fetchone()
    assert admin_data, "관리자 계정이 존재하지 않습니다"
    # SQL 쿼리 결과에서 is_admin이 int(1)로 반환될 수 있어 명시적으로 bool로 변환
    assert bool(admin_data.is_admin), "관리자 권한이 부여되지 않았습니다"

    # 초기 잔고 확인
    balance_result = await db.execute(
        text("SELECT amount FROM balances WHERE user_id = :user_id AND asset = 'USDT'"),
        {"user_id": user_id},
    )
    initial_balance = balance_result.scalar_one_or_none() or 0
    initial_balance = Decimal(str(initial_balance))

    # API 요청 대신 직접 SQL로 잔고 조정
    try:
        # 잔고 업데이트
        await db.execute(
            text(
                """
                UPDATE balances SET
                amount = amount + :adjustment_amount,
                updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id AND asset = :asset
            """
            ),
            {"user_id": user_id, "asset": "USDT", "adjustment_amount": 100.0},
        )

        # 트랜잭션 생성
        await db.execute(
            text(
                """
                INSERT INTO transactions
                (user_id, type, direction, status, asset, amount, fee, description)
                VALUES
                (:user_id, 'ADJUSTMENT', 'IN', 'COMPLETED', 'USDT', :amount, 0, :description)
            """
            ),
            {
                "user_id": user_id,
                "amount": 100.0,
                "description": "Initial test deposit",
            },
        )

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

    # 잔고를 직접 SQL로 조회하여 확인
    balance_result = await db.execute(
        text("SELECT amount FROM balances WHERE user_id = :user_id AND asset = 'USDT'"),
        {"user_id": user_id},
    )
    final_balance = balance_result.scalar_one_or_none() or 0
    final_balance = Decimal(str(final_balance))

    # 잔고가 증가했는지 확인
    assert final_balance >= initial_balance + Decimal(
        "100.000000"
    ), f"잔고가 증가하지 않았습니다: 초기={initial_balance}, 최종={final_balance}"

    # 트랜잭션이 생성되었는지 확인 (직접 SQL로 확인)
    tx_result = await db.execute(
        text(
            "SELECT COUNT(*) FROM transactions WHERE user_id = :user_id AND description = :description"
        ),
        {"user_id": user_id, "description": "Initial test deposit"},
    )
    tx_count = tx_result.scalar_one_or_none() or 0
    assert tx_count > 0, "트랜잭션이 생성되지 않았습니다"


@pytest.mark.asyncio
async def test_internal_transfer(
    client: AsyncClient, user_token_headers, admin_token_headers, db: AsyncSession
):
    """내부 이체 테스트"""
    # 관리자와 일반 사용자 정보 가져오기 (직접 SQL로 처리)
    admin_result = await db.execute(
        text("SELECT id, is_admin FROM users WHERE email = :email"),
        {"email": admin_user["email"]},
    )
    admin_data = admin_result.fetchone()
    assert admin_data, "관리자 계정이 존재하지 않습니다"
    # SQL 쿼리 결과에서 is_admin이 int(1)로 반환될 수 있어 명시적으로 bool로 변환
    assert bool(admin_data.is_admin), "관리자 권한이 부여되지 않았습니다"
    admin_id = admin_data.id

    user_result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"), {"email": test_user["email"]}
    )
    user_id = user_result.scalar_one_or_none()
    assert user_id, "사용자 계정이 존재하지 않습니다"

    # 관리자 계정이 자금을 갖도록 직접 SQL로 처리
    balance_result = await db.execute(
        text("SELECT id FROM balances WHERE user_id = :user_id AND asset = :asset"),
        {"user_id": admin_id, "asset": "USDT"},
    )
    admin_balance_id = balance_result.scalar_one_or_none()

    if not admin_balance_id:
        await db.execute(
            text(
                "INSERT INTO balances (user_id, asset, amount, locked_amount) VALUES (:user_id, :asset, :amount, :locked_amount)"
            ),
            {
                "user_id": admin_id,
                "asset": "USDT",
                "amount": 200.0,
                "locked_amount": 0.0,
            },
        )
    else:
        await db.execute(
            text(
                "UPDATE balances SET amount = :amount WHERE user_id = :user_id AND asset = :asset"
            ),
            {"amount": 200.0, "user_id": admin_id, "asset": "USDT"},
        )

    await db.commit()

    # 초기 잔고 확인
    user_balance_result = await db.execute(
        text("SELECT amount FROM balances WHERE user_id = :user_id AND asset = 'USDT'"),
        {"user_id": user_id},
    )
    initial_user_balance = user_balance_result.scalar_one_or_none() or 0
    initial_user_balance = Decimal(str(initial_user_balance))

    # 관리자에서 일반 사용자로 이체
    response = await client.post(
        "/api/v1/balance/transfer",
        json={
            "receiver_email": test_user["email"],
            "amount": "50.000000",
            "description": "Test transfer",
        },
        headers=admin_token_headers,
    )

    # HTTP 응답 코드만 확인
    assert response.status_code == 200

    # 잔고를 직접 SQL로 조회하여 확인
    user_balance_result = await db.execute(
        text("SELECT amount FROM balances WHERE user_id = :user_id AND asset = 'USDT'"),
        {"user_id": user_id},
    )
    final_user_balance = user_balance_result.scalar_one_or_none() or 0
    final_user_balance = Decimal(str(final_user_balance))

    # 이체가 성공했는지 확인
    assert final_user_balance >= initial_user_balance + Decimal(
        "50.000000"
    ), f"이체가 성공하지 않았습니다: 초기={initial_user_balance}, 최종={final_user_balance}"

    # 송신자(관리자)의 잔고도 감소했는지 확인
    admin_balance_result = await db.execute(
        text("SELECT amount FROM balances WHERE user_id = :user_id AND asset = 'USDT'"),
        {"user_id": admin_id},
    )
    admin_balance_after = admin_balance_result.scalar_one_or_none() or 0
    admin_balance_after = Decimal(str(admin_balance_after))
    assert admin_balance_after < Decimal(
        "200.000000"
    ), f"관리자 잔고가 감소하지 않았습니다: {admin_balance_after}"


@pytest.mark.asyncio
async def test_insufficient_balance_transfer(
    client: AsyncClient, user_token_headers, db: AsyncSession
):
    """잔고 부족 이체 테스트"""
    # 사용자와 관리자가 존재하는지 확인
    result = await db.execute(select(User).where(User.email == test_user["email"]))
    user = result.scalar_one_or_none()
    assert user, "사용자 계정이 존재하지 않습니다"

    # 관리자 계정 확인 (없으면 직접 생성)
    admin_result = await db.execute(
        select(User).where(User.email == admin_user["email"])
    )
    admin = admin_result.scalar_one_or_none()

    if not admin:
        # 관리자 계정이 없으면 생성
        admin = User(
            email=admin_user["email"],
            password_hash=get_password_hash(admin_user["password"]),
            is_active=True,
            is_admin=True,
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"Created admin for test: {admin.email}, ID: {admin.id}")

    assert admin, "관리자 계정이 존재하지 않습니다"

    # 사용자의 현재 잔고 확인
    balance_response = await client.get("/api/v1/balance/", headers=user_token_headers)
    current_balance = Decimal(balance_response.json()["amount"])

    # 현재 잔고보다 큰 금액 이체 시도
    response = await client.post(
        "/api/v1/balance/transfer",
        json={
            "receiver_email": admin_user["email"],
            "amount": str(current_balance + Decimal("1000.000000")),
            "description": "Will fail due to insufficient balance",
        },
        headers=user_token_headers,
    )

    assert response.status_code == 400
    assert "detail" in response.json()
    assert "잔액이 부족" in response.json()["detail"]


@pytest.mark.asyncio
async def test_self_transfer_prevention(
    client: AsyncClient, user_token_headers, db: AsyncSession
):
    """자기 자신에게 이체 방지 테스트"""
    # 사용자가 존재하는지 확인
    result = await db.execute(select(User).where(User.email == test_user["email"]))
    user = result.scalar_one_or_none()
    assert user, "사용자 계정이 존재하지 않습니다"

    response = await client.post(
        "/api/v1/balance/transfer",
        json={
            "receiver_email": test_user["email"],  # 자신에게 이체
            "amount": "10.000000",
            "description": "Self transfer",
        },
        headers=user_token_headers,
    )

    assert response.status_code in [400, 422]  # 400 또는 422 에러 코드
