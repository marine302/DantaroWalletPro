"""
인증 시스템 테스트 모듈.
회원가입, 로그인, 토큰 갱신 등 인증 관련 기능을 테스트합니다.
"""
import json

import pytest
from app.core.database import AsyncSessionLocal
from app.core.security import verify_token
from app.main import app
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import text


@pytest.mark.asyncio
async def test_user_registration():
    """사용자 회원가입 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "password" not in data

    # 테스트 데이터 정리
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM users WHERE email='newuser@example.com'")
        )
        await session.commit()


@pytest.mark.asyncio
async def test_duplicate_registration():
    """중복 회원가입 방지 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 첫 번째 가입
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#",
            },
        )

        # 중복 가입 시도
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#",
            },
        )

    assert response.status_code == 409
    assert response.json()["error"] == "CONFLICT"

    # 테스트 데이터 정리
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM users WHERE email='duplicate@example.com'")
        )
        await session.commit()


@pytest.mark.asyncio
async def test_weak_password():
    """약한 비밀번호 거부 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "weak",
                "password_confirm": "weak",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_login():
    """로그인 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 사용자 생성
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#",
            },
        )

        # 로그인
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "logintest@example.com", "password": "Test123!@#"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # 토큰 검증
    payload = verify_token(data["access_token"])
    assert payload is not None
    assert payload["type"] == "access"

    # 테스트 데이터 정리
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM users WHERE email='logintest@example.com'")
        )
        await session.commit()


@pytest.mark.asyncio
async def test_invalid_login():
    """잘못된 로그인 정보 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPass123!"},
        )

    assert response.status_code == 401
    assert response.json()["error"] == "AUTH_ERROR"


@pytest.mark.asyncio
async def test_get_current_user():
    """현재 사용자 정보 조회 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 회원가입
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "currentuser@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#",
            },
        )

        # 로그인
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "currentuser@example.com", "password": "Test123!@#"},
        )

        token = login_response.json()["access_token"]

        # 사용자 정보 조회
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "currentuser@example.com"

    # 테스트 데이터 정리
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM users WHERE email='currentuser@example.com'")
        )
        await session.commit()


@pytest.mark.asyncio
async def test_token_refresh():
    """토큰 갱신 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 회원가입
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshtest@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#",
            },
        )

        # 로그인하여 토큰 획득
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "refreshtest@example.com", "password": "Test123!@#"},
        )

        refresh_token = login_response.json()["refresh_token"]

        # 토큰 갱신
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # 테스트 데이터 정리
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM users WHERE email='refreshtest@example.com'")
        )
        await session.commit()
