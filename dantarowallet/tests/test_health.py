"""
Health check endpoint tests.
Tests the basic application health and status endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint returns correct status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Verify required fields
    assert data["status"] == "healthy"
    assert data["app_name"] == "DantaroWallet"
    assert "version" in data
    assert "environment" in data
    assert "debug" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint returns API information."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    # Verify required fields
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "health" in data
    assert data["health"] == "/health"


@pytest.mark.asyncio
async def test_health_check_response_format(client: AsyncClient):
    """Test that health check response has correct format and types."""
    response = await client.get("/health")
    data = response.json()

    # Type checks
    assert isinstance(data["status"], str)
    assert isinstance(data["app_name"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["environment"], str)
    assert isinstance(data["debug"], bool)
