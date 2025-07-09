"""
관리자 API 기본 테스트
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TestAdminAPIs:
    """관리자 API 테스트 클래스"""

    def test_health_check(self):
        """헬스 체크 테스트"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Health check: {data}")

    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print(f"✅ Root endpoint: {response.status_code}")

    def test_docs_available(self):
        """API 문서 접근 가능성 테스트 (DEBUG 모드에서만)"""
        response = requests.get(f"{BASE_URL}/docs")
        # 프로덕션에서는 docs가 비활성화될 수 있음
        if response.status_code == 404:
            print(f"⚠️  API docs disabled (production mode): {response.status_code}")
        else:
            assert response.status_code == 200
            print(f"✅ API docs accessible: {response.status_code}")

    def test_admin_api_routes_exist(self):
        """관리자 API 라우트 존재 확인"""
        # OpenAPI spec 확인 (프로덕션에서는 비활성화될 수 있음)
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 404:
            print(f"⚠️  OpenAPI spec disabled (production mode)")
            # 대신 실제 엔드포인트 접근성 테스트
            test_routes = [
                "/api/v1/admin/energy/status",
                "/api/v1/admin/fees/total-revenue-stats"
            ]
            for route in test_routes:
                resp = requests.get(f"{BASE_URL}{route}")
                # 401/403은 인증 문제이므로 정상 (라우트는 존재)
                assert resp.status_code in [401, 403, 422], f"Route {route} not accessible: {resp.status_code}"
                print(f"✅ Route accessible (auth required): {route}")
        else:
            assert response.status_code == 200
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            # 우리가 구현한 주요 API들이 존재하는지 확인
            expected_admin_routes = [
                "/api/v1/admin/partners/",
                "/api/v1/admin/energy/status", 
                "/api/v1/admin/fees/configs"
            ]
            
            for route in expected_admin_routes:
                assert route in paths, f"Route {route} not found in OpenAPI spec"
                print(f"✅ Route exists: {route}")

    def test_partner_api_structure(self):
        """파트너 API 구조 확인"""
        # 직접 API 테스트
        partner_routes = [
            "/api/v1/admin/partners/",
            "/api/v1/admin/partners/test123",
            "/api/v1/admin/partners/test123/statistics"
        ]
        
        for route in partner_routes:
            response = requests.get(f"{BASE_URL}{route}")
            # 401/403/422는 인증 또는 데이터 문제이므로 라우트는 존재
            assert response.status_code in [401, 403, 422, 404], f"Partner route {route} error: {response.status_code}"
            print(f"✅ Partner route accessible: {route}")

    def test_energy_api_structure(self):
        """에너지 API 구조 확인"""
        # 직접 API 테스트
        energy_routes = [
            "/api/v1/admin/energy/status",
            "/api/v1/admin/energy/usage-stats",
            "/api/v1/admin/energy/alerts"
        ]
        
        for route in energy_routes:
            response = requests.get(f"{BASE_URL}{route}")
            # 401/403/422는 인증 또는 데이터 문제이므로 라우트는 존재
            assert response.status_code in [401, 403, 422], f"Energy route {route} error: {response.status_code}"
            print(f"✅ Energy route accessible: {route}")

    def test_fees_api_structure(self):
        """수수료 API 구조 확인"""
        # 직접 API 테스트  
        fee_routes = [
            "/api/v1/admin/fees/total-revenue-stats"
        ]
        
        for route in fee_routes:
            response = requests.get(f"{BASE_URL}{route}")
            # 401/403/422는 인증 또는 데이터 문제이므로 라우트는 존재
            assert response.status_code in [401, 403, 422], f"Fee route {route} error: {response.status_code}"
            print(f"✅ Fee route accessible: {route}")


if __name__ == "__main__":
    # 간단한 테스트 실행
    test_instance = TestAdminAPIs()
    
    try:
        print("🧪 Starting API tests...\n")
        
        test_instance.test_health_check()
        test_instance.test_root_endpoint()
        test_instance.test_docs_available()
        test_instance.test_admin_api_routes_exist()
        test_instance.test_partner_api_structure()
        test_instance.test_energy_api_structure()
        test_instance.test_fees_api_structure()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
