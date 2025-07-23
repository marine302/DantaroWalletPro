#!/usr/bin/env python3
"""API 응답 테스트"""

import json

import requests


def test_api():
    """API 응답 테스트"""

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzUyNTkyNzE5fQ.0vBkw9S2XxVPYbJqBVz6_yM5hT__NhNb6NrYIEzOC2g"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        print("🔄 API 응답 테스트 시작...")

        # 1. 메인 대시보드 API 테스트
        response = requests.get(
            "http://localhost:8001/api/v1/integrated-dashboard/dashboard/test_partner_001",
            headers=headers,
            timeout=10,
        )

        print(f"📊 응답 상태: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                dashboard_data = data.get("data", {})
                print("✅ API 응답 성공!")
                print(
                    f"   - wallet_overview: {bool(dashboard_data.get('wallet_overview'))}"
                )
                print(
                    f"   - transaction_flow: {bool(dashboard_data.get('transaction_flow'))}"
                )
                print(
                    f"   - energy_status: {bool(dashboard_data.get('energy_status'))}"
                )
                print(
                    f"   - user_analytics: {bool(dashboard_data.get('user_analytics'))}"
                )
                print(f"   - last_updated: {dashboard_data.get('last_updated')}")

                # 실제 데이터 확인
                wallet_overview = dashboard_data.get("wallet_overview", {})
                if wallet_overview:
                    print(f"   - 총 잔액: {wallet_overview.get('total_balance', 0)}")
                    print(f"   - 지갑 수: {wallet_overview.get('wallet_count', 0)}")

            else:
                print("❌ API 실패:", data.get("message", "Unknown error"))
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text[:200]}")

    except Exception as e:
        print(f"❌ 연결 오류: {str(e)}")


if __name__ == "__main__":
    test_api()
