"""
Doc #30 API 엔드포인트 빠른 테스트
"""
import asyncio
import json
from app.main import app
from fastapi.testclient import TestClient

def test_audit_compliance_endpoints():
    """감사 및 컴플라이언스 API 엔드포인트 테스트"""
    print("=== Doc #30 API 엔드포인트 테스트 ===\n")
    
    client = TestClient(app)
    
    # 1. Health check
    print("1. Health Check...")
    response = client.get("/health")
    if response.status_code == 200:
        print(f"✅ Health Check: {response.json()}")
    else:
        print(f"❌ Health Check 실패: {response.status_code}")
    
    # 2. 감사 통계 조회
    print("\n2. 감사 통계 조회...")
    try:
        response = client.get("/api/v1/audit-compliance/statistics/audit")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 감사 통계: {stats}")
        else:
            print(f"❌ 감사 통계 조회 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 감사 통계 조회 오류: {e}")
    
    # 3. 컴플라이언스 통계 조회
    print("\n3. 컴플라이언스 통계 조회...")
    try:
        response = client.get("/api/v1/audit-compliance/statistics/compliance")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 컴플라이언스 통계: {stats}")
        else:
            print(f"❌ 컴플라이언스 통계 조회 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 컴플라이언스 통계 조회 오류: {e}")
    
    # 4. ML 탐지 통계 조회
    print("\n4. ML 탐지 통계 조회...")
    try:
        response = client.get("/api/v1/audit-compliance/statistics/detection")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ ML 탐지 통계: {stats}")
        else:
            print(f"❌ ML 탐지 통계 조회 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ ML 탐지 통계 조회 오류: {e}")
    
    print("\n=== API 테스트 완료 ===")


if __name__ == "__main__":
    test_audit_compliance_endpoints()
