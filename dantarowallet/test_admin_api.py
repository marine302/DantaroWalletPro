"""
관리자 API 엔드포인트 테스트
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.api.deps import get_current_admin_user

# 테스트용 인메모리 SQLite 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_admin_user():
    """테스트용 관리자 사용자"""
    return User(
        id=1,
        email="admin@test.com",
        is_admin=True,
        is_active=True,
        is_verified=True
    )


# 의존성 오버라이드
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

client = TestClient(app)


@pytest.fixture
def setup_database():
    """테스트용 데이터베이스 초기화"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestPartnerAPI:
    """파트너 관리 API 테스트"""

    def test_get_partners_list(self, setup_database):
        """파트너 목록 조회 테스트"""
        response = client.get("/api/v1/admin/partners/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_partner_validation(self, setup_database):
        """파트너 생성 요청 유효성 검증 테스트"""
        # 잘못된 데이터로 테스트
        invalid_data = {
            "name": "",  # 빈 이름
            "domain": "invalid-domain",  # 잘못된 도메인
            "contact_email": "invalid-email"  # 잘못된 이메일
        }
        
        response = client.post("/api/v1/admin/partners/", json=invalid_data)
        # 유효성 검증 오류가 발생해야 함
        assert response.status_code in [400, 422]


class TestEnergyAPI:
    """에너지 관리 API 테스트"""

    def test_get_energy_status(self, setup_database):
        """에너지 상태 조회 테스트"""
        response = client.get("/api/v1/admin/energy/status")
        assert response.status_code == 200
        data = response.json()
        # 에너지 상태 응답 필드 확인
        expected_fields = [
            "total_energy", "available_energy", "reserved_energy",
            "daily_consumption", "is_sufficient"
        ]
        for field in expected_fields:
            assert field in data

    def test_get_usage_stats(self, setup_database):
        """에너지 사용 통계 조회 테스트"""
        response = client.get("/api/v1/admin/energy/usage-stats")
        assert response.status_code == 200
        data = response.json()
        # 통계 응답 필드 확인
        expected_fields = [
            "total_used_today", "average_per_transaction",
            "peak_hour_usage", "transactions_count"
        ]
        for field in expected_fields:
            assert field in data


class TestFeeAPI:
    """수수료 관리 API 테스트"""

    def test_calculate_fee_validation(self, setup_database):
        """수수료 계산 요청 유효성 검증 테스트"""
        # 잘못된 계산 요청
        invalid_request = {
            "amount": -100,  # 음수 금액
            "transaction_type": "",  # 빈 거래 유형
        }
        
        response = client.post("/api/v1/admin/fees/calculate", json=invalid_request)
        # 유효성 검증 오류가 발생해야 함
        assert response.status_code in [400, 422]

    def test_get_total_revenue_stats(self, setup_database):
        """전체 수익 통계 조회 테스트"""
        response = client.get("/api/v1/admin/fees/total-revenue-stats?days=30")
        assert response.status_code == 200
        # 응답이 JSON 형태여야 함
        assert response.headers["content-type"] == "application/json"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
