#!/usr/bin/env python3
"""
출금 API 엔드포인트 직접 테스트
"""
import json

import requests

BASE_URL = "http://localhost:8007"


def test_withdrawal_endpoints():
    """출금 엔드포인트만 직접 테스트"""
    print("🔗 출금 API 엔드포인트 테스트\n")

    # 1. 건강 체크
    print("1️⃣ 건강 체크...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   상태: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
        else:
            print(f"   오류: {response.text}")
            return
    except Exception as e:
        print(f"   연결 오류: {e}")
        return

    # 2. 출금 목록 조회 (인증 없이 - 401 예상)
    print("\n2️⃣ 출금 목록 조회 (인증 없음)...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/withdrawals/list")
        print(f"   상태: {response.status_code}")
        print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"   오류: {e}")

    # 3. 출금 요청 (인증 없이 - 401 예상)
    print("\n3️⃣ 출금 요청 (인증 없음)...")
    withdrawal_data = {
        "asset_type": "USDT",
        "amount": "10.0",
        "to_address": "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE",
        "priority": "normal",
        "notes": "테스트 출금",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/withdrawals/request", json=withdrawal_data
        )
        print(f"   상태: {response.status_code}")
        print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"   오류: {e}")

    # 4. 관리자 출금 통계 (인증 없이 - 401 예상)
    print("\n4️⃣ 관리자 출금 통계 조회...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/withdrawals/admin/stats")
        print(f"   상태: {response.status_code}")
        print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"   오류: {e}")

    print("\n✅ 출금 엔드포인트 테스트 완료!")


if __name__ == "__main__":
    test_withdrawal_endpoints()
