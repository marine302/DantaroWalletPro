"""
대시보드 API 테스트
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(client: AsyncClient, user_token_headers):
    """대시보드 개요 정보 조회 테스트"""
    response = await client.get(
        "/api/v1/dashboard/overview", headers=user_token_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert "total_balance" in data
    assert "total_wallets" in data
    assert "total_transactions" in data
    assert "pending_transactions" in data
    assert "monthly_volume" in data


@pytest.mark.asyncio
async def test_recent_transactions(client: AsyncClient, user_token_headers):
    """최근 거래 내역 조회 테스트"""
    response = await client.get(
        "/api/v1/dashboard/recent-transactions?limit=5", headers=user_token_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_balance_history(client: AsyncClient, user_token_headers):
    """잔고 변화 이력 조회 테스트"""
    response = await client.get(
        "/api/v1/dashboard/balance-history?days=7", headers=user_token_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_wallet_stats(client: AsyncClient, user_token_headers):
    """지갑 통계 조회 테스트"""
    response = await client.get(
        "/api/v1/dashboard/wallet-stats", headers=user_token_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert "active_wallets" in data
    assert "inactive_wallets" in data
    assert "total_received" in data
    assert "total_sent" in data
    assert "average_balance" in data


@pytest.mark.asyncio
async def test_dashboard_unauthorized(client: AsyncClient):
    """인증되지 않은 요청 테스트"""
    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_with_invalid_token(client: AsyncClient):
    """잘못된 토큰으로 요청 테스트"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/dashboard/overview", headers=headers)
    assert response.status_code == 401
