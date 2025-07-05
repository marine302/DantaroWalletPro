"""
지갑 시스템 테스트.
지갑 생성, 조회, 잔고 확인, 모니터링 등의 기능을 테스트합니다.
"""
import json

import pytest
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Wallet
from app.services.wallet_service import WalletService
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 각 테스트 함수에 @pytest.mark.asyncio를 표시하는 방식으로 변경
# pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_create_wallet(client: AsyncClient, user_token_headers, db: AsyncSession):
    """지갑 생성 테스트"""
    # 사용자 정보 확인
    user_result = await db.execute(
        text("SELECT id FROM users WHERE email = 'test@example.com'")
    )
    user_id = user_result.scalar_one_or_none()
    assert user_id, "사용자 계정이 존재하지 않습니다"

    # API 호출하여 지갑 생성
    response = await client.post("/api/v1/wallet/create", headers=user_token_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "address" in data
    assert "hex_address" in data
    assert data["network"] == "nile"  # testnet

    # DB에 지갑이 제대로 생성되었는지 확인
    wallet_result = await db.execute(
        text("SELECT address FROM wallets WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    wallet_address = wallet_result.scalar_one_or_none()
    assert wallet_address == data["address"], "지갑 주소가 DB에 제대로 저장되지 않았습니다"


@pytest.mark.asyncio
async def test_get_wallet(client: AsyncClient, user_token_headers):
    """지갑 조회 테스트"""
    # 먼저 지갑 생성
    await client.post("/api/v1/wallet/create", headers=user_token_headers)

    # 지갑 정보 조회
    response = await client.get("/api/v1/wallet/", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "address" in data
    assert "is_active" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_wallet_balance(client: AsyncClient, user_token_headers):
    """지갑 잔고 조회 테스트"""
    # 먼저 지갑 생성
    await client.post("/api/v1/wallet/create", headers=user_token_headers)

    # 잔고 조회
    response = await client.get("/api/v1/wallet/balance", headers=user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "address" in data
    assert "balances" in data
    assert "TRX" in data["balances"]
    assert "USDT" in data["balances"]


@pytest.mark.asyncio
async def test_validate_address(client: AsyncClient, user_token_headers):
    """주소 유효성 검증 테스트"""
    # 유효한 TRON 주소 검증
    valid_address = "TJYeasTPQUDfyYPukGFWoMxGGHg4u2j5FB"
    response = await client.post(
        "/api/v1/wallet/validate-address",
        headers=user_token_headers,
        json={"address": valid_address},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_valid"] is True
    assert "message" in data

    # 유효하지 않은 주소 검증
    invalid_address = "invalid_address"
    response = await client.post(
        "/api/v1/wallet/validate-address",
        headers=user_token_headers,
        json={"address": invalid_address},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_valid"] is False
    assert "message" in data


@pytest.mark.asyncio
async def test_wallet_monitoring(client: AsyncClient, user_token_headers):
    """지갑 모니터링 설정 테스트"""
    # 먼저 지갑 생성
    await client.post("/api/v1/wallet/create", headers=user_token_headers)

    # 모니터링 비활성화
    response = await client.post(
        "/api/v1/wallet/monitoring", headers=user_token_headers, json={"enable": False}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_monitored"] is False

    # 모니터링 재활성화
    response = await client.post(
        "/api/v1/wallet/monitoring", headers=user_token_headers, json={"enable": True}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_monitored"] is True


@pytest.mark.asyncio
async def test_duplicate_wallet_creation(client: AsyncClient, user_token_headers):
    """중복 지갑 생성 시도 테스트"""
    # 첫 번째 지갑 생성
    response = await client.post("/api/v1/wallet/create", headers=user_token_headers)
    assert response.status_code == status.HTTP_201_CREATED

    # 두 번째 지갑 생성 시도
    response = await client.post("/api/v1/wallet/create", headers=user_token_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
