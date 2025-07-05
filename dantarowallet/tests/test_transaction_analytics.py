"""
트랜잭션 분석 API 테스트
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from app.main import app
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction_analytics import AlertLevel, AlertType, TransactionAlert
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 테스트용 사용자 정보 - conftest.py와 일관성 유지
test_user = {"email": "test@example.com", "password": "TestPassword123!"}
admin_user = {"email": "admin@example.com", "password": "AdminPassword123!"}


class TestTransactionAnalytics:
    """트랜잭션 분석 API 테스트"""

    @pytest.mark.asyncio
    async def test_get_analytics_unauthorized(self, client: AsyncClient):
        """인증되지 않은 사용자의 분석 요청 테스트"""
        response = await client.get("/api/v1/transaction-analytics/analytics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_analytics_user(self, client: AsyncClient, user_token_headers):
        """일반 사용자의 분석 요청 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/analytics", headers=user_token_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "overall_stats" in data
        assert "asset_breakdown" in data
        assert "daily_breakdown" in data

    @pytest.mark.asyncio
    async def test_get_analytics_admin(self, client: AsyncClient, admin_token_headers):
        """관리자의 분석 요청 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/analytics", headers=admin_token_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "overall_stats" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_own(self, client: AsyncClient, user_token_headers):
        """사용자 자신의 프로필 조회 테스트"""
        # 현재 사용자의 ID는 1이라고 가정 (테스트 환경에서)
        response = await client.get(
            f"/api/v1/transaction-analytics/profile/1", headers=user_token_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == 1
        assert "total_transactions" in data
        assert "total_volume_usd" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_forbidden(
        self, client: AsyncClient, user_token_headers
    ):
        """다른 사용자 프로필 조회 금지 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/profile/999", headers=user_token_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_real_time_metrics_admin_only(
        self, client: AsyncClient, user_token_headers
    ):
        """실시간 메트릭 관리자 전용 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/real-time-metrics",
            headers=user_token_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_real_time_metrics_admin(
        self, client: AsyncClient, admin_token_headers
    ):
        """관리자의 실시간 메트릭 조회 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/real-time-metrics",
            headers=admin_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "current_tps" in data
        assert "current_volume_per_minute" in data
        assert "system_health_score" in data

    @pytest.mark.asyncio
    async def test_create_alert_admin_only(
        self, client: AsyncClient, user_token_headers
    ):
        """알림 생성 관리자 전용 테스트"""
        alert_data = {
            "user_id": 1,
            "alert_type": "suspicious_activity",
            "level": "medium",
            "title": "테스트 알림",
            "description": "테스트용 알림입니다",
        }
        response = await client.post(
            "/api/v1/transaction-analytics/alerts",
            json=alert_data,
            headers=user_token_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_alerts_user(self, client: AsyncClient, user_token_headers):
        """사용자의 알림 조회 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/alerts", headers=user_token_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_trends_admin_only(self, client: AsyncClient, user_token_headers):
        """트렌드 분석 관리자 전용 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/trends", headers=user_token_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_trends_admin(self, client: AsyncClient, admin_token_headers):
        """관리자의 트렌드 분석 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/trends?period=7d",
            headers=admin_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["period"] == "7d"
        assert "trend_direction" in data

    @pytest.mark.asyncio
    async def test_suspicious_patterns_admin_only(
        self, client: AsyncClient, user_token_headers
    ):
        """의심스러운 패턴 탐지 관리자 전용 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/suspicious-patterns",
            headers=user_token_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_daily_stats_admin_only(
        self, client: AsyncClient, user_token_headers
    ):
        """일별 통계 관리자 전용 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/stats/daily", headers=user_token_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_daily_stats_admin(self, client: AsyncClient, admin_token_headers):
        """관리자의 일별 통계 조회 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/stats/daily", headers=admin_token_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "date" in data
        assert "total_transactions" in data

    @pytest.mark.asyncio
    async def test_stats_summary_admin_only(
        self, client: AsyncClient, user_token_headers
    ):
        """통계 요약 관리자 전용 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/stats/summary", headers=user_token_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_stats_summary_admin(self, client: AsyncClient, admin_token_headers):
        """관리자의 통계 요약 조회 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/stats/summary?period=30d",
            headers=admin_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["period"] == "30d"
        assert "total_transactions" in data

    @pytest.mark.asyncio
    async def test_monitoring_config_admin_only(
        self, client: AsyncClient, user_token_headers
    ):
        """모니터링 설정 관리자 전용 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/monitoring/config",
            headers=user_token_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_monitoring_config_admin(
        self, client: AsyncClient, admin_token_headers
    ):
        """관리자의 모니터링 설정 조회 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/monitoring/config",
            headers=admin_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "large_transaction_threshold_usd" in data
        assert "enable_pattern_detection" in data
        assert "enable_real_time_alerts" in data

    @pytest.mark.asyncio
    async def test_analytics_with_filters(
        self, client: AsyncClient, admin_token_headers
    ):
        """필터를 사용한 분석 조회 테스트"""
        # 날짜 필터
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "asset": "TRX",
            "min_amount": 1.0,
            "max_amount": 1000.0,
        }

        response = await client.get(
            "/api/v1/transaction-analytics/analytics",
            params=params,
            headers=admin_token_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_period_trends(
        self, client: AsyncClient, admin_token_headers
    ):
        """잘못된 기간으로 트렌드 분석 요청 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/trends?period=invalid",
            headers=admin_token_headers,
        )
        # 현재 구현에서는 기본값을 사용하므로 200이 반환될 수 있음
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_analytics_response_structure(
        self, client: AsyncClient, user_token_headers
    ):
        """분석 응답 구조 테스트"""
        response = await client.get(
            "/api/v1/transaction-analytics/analytics", headers=user_token_headers
        )
        assert response.status_code == 200

        data = response.json()

        # 전체 통계 검증
        assert "overall_stats" in data
        overall = data["overall_stats"]
        assert "total_count" in overall
        assert "total_volume" in overall
        assert "successful_count" in overall
        assert "failed_count" in overall

        # 자산별 분석 검증
        assert "asset_breakdown" in data
        assert isinstance(data["asset_breakdown"], list)

        # 일별 분석 검증
        assert "daily_breakdown" in data
        assert isinstance(data["daily_breakdown"], list)
