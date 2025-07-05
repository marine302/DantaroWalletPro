#!/usr/bin/env python3
"""
TRON 출금 처리 시스템 완전 테스트
"""
import json

import requests

BASE_URL = "http://localhost:8007"


def test_complete_withdrawal_flow():
    """출금 플로우 완전 테스트"""
    print("🚀 TRON 출금 처리 시스템 완전 테스트 시작\n")

    # 1. 건강 체크
    print("1️⃣ 건강 체크...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   상태: {response.status_code}")
    if response.status_code != 200:
        print(f"   오류: {response.text}")
        return
    print(f"   응답: {response.json()}")

    # 2. 사용자 등록
    print("\n2️⃣ 테스트 사용자 등록...")
    user_data = {
        "email": "testwithdrawal@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"   상태: {response.status_code}")
    if response.status_code in [200, 201]:
        user = response.json()
        print(f"   사용자 생성: {user['email']}")
    else:
        print(f"   응답: {response.text}")
        if "already exists" not in response.text:
            return

    # 3. 로그인
    print("\n3️⃣ 로그인...")
    login_data = {"email": user_data["email"], "password": user_data["password"]}

    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"   상태: {response.status_code}")
    if response.status_code != 200:
        print(f"   로그인 실패: {response.text}")
        return

    auth_data = response.json()
    access_token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"   토큰 획득 성공")

    # 4. 지갑 생성
    print("\n4️⃣ 지갑 생성...")
    response = requests.post(f"{BASE_URL}/api/v1/wallet/create", headers=headers)
    print(f"   상태: {response.status_code}")
    if response.status_code in [200, 201]:
        wallet = response.json()
        print(f"   지갑 주소: {wallet['address']}")
    else:
        print(f"   응답: {response.text}")

    # 5. 잔액 확인
    print("\n5️⃣ 잔액 확인...")
    response = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        balance = response.json()
        print(f"   TRX 잔액: {balance.get('trx_balance', 0)}")
        print(f"   USDT 잔액: {balance.get('usdt_balance', 0)}")
    else:
        print(f"   응답: {response.text}")

    # 6. 출금 요청 (잔액 부족 예상)
    print("\n6️⃣ 출금 요청 테스트...")
    withdrawal_data = {
        "asset_type": "USDT",
        "amount": "10.0",
        "to_address": "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE",
        "priority": "normal",
        "notes": "테스트 출금",
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/withdrawals/request", json=withdrawal_data, headers=headers
    )
    print(f"   상태: {response.status_code}")
    result = response.json()
    print(f"   응답: {result}")

    # 7. 출금 목록 조회
    print("\n7️⃣ 출금 목록 조회...")
    response = requests.get(f"{BASE_URL}/api/v1/withdrawals/list", headers=headers)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        withdrawals = response.json()
        print(f"   출금 건수: {len(withdrawals)}")
        for w in withdrawals:
            print(
                f"   - ID: {w['id']}, 상태: {w['status']}, 금액: {w['amount']} {w['asset_type']}"
            )
    else:
        print(f"   응답: {response.text}")

    # 8. 관리자 통계 (권한 없음 예상)
    print("\n8️⃣ 관리자 출금 통계 조회 테스트...")
    response = requests.get(
        f"{BASE_URL}/api/v1/withdrawals/admin/stats", headers=headers
    )
    print(f"   상태: {response.status_code}")
    print(f"   응답: {response.json()}")

    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    test_complete_withdrawal_flow()
