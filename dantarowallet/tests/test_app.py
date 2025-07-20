from httpx import AsyncClient, ASGITransport
"""
기본 애플리케이션 기능 테스트.
미들웨어, 핵심 엔드포인트 및 오류 처리를 검증합니다.
"""
import pytest
from app.main import app
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Health 엔드포인트 테스트"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "DantaroWallet"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """루트 엔드포인트 테스트"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "health" in data
    assert data["health"] == "/health"


@pytest.mark.asyncio
async def test_api_test_endpoint(client: AsyncClient):
    """API v1 테스트 엔드포인트 테스트"""
    response = await client.get("/api/v1/test")
    assert response.status_code == 200
    assert response.json()["message"] == "API v1 is working"


@pytest.mark.asyncio
async def test_request_id_header(client: AsyncClient):
    """요청 ID 헤더 테스트"""
    response = await client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    """CORS 헤더 테스트 - CORS credentials만 확인"""
    response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS 설정이 적용되었는지 확인 (credentials 헤더로 확인)
    assert "access-control-allow-credentials" in response.headers


@pytest.mark.asyncio
async def test_404_error(client: AsyncClient):
    """존재하지 않는 엔드포인트 테스트"""
    response = await client.get("/non-existent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_json_error(client: AsyncClient):
    """잘못된 JSON 요청 테스트"""
    response = await client.post(
        "/api/v1/test",
        headers={"Content-Type": "application/json"},
        content="{invalid-json",
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "INVALID_JSON" in data["error"]
