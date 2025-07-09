#!/usr/bin/env python3
"""
FastAPI 서버를 통한 Sweep API 테스트
"""
import requests
import json
import time

def test_sweep_api():
    base_url = "http://localhost:8000"
    # Bearer 토큰 형식으로 변경
    headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }
    
    print("🚀 FastAPI Sweep API 테스트 시작")
    
    # 전역 변수 선언
    user_wallets = []
    master_wallet_id = None
    partner_wallet_id = 1
    
    # 1. 서버 헬스 체크
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 서버 헬스 체크 성공")
        else:
            print(f"❌ 서버 헬스 체크 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return
    
    # 2. 마스터 지갑 생성 API 테스트
    try:
        response = requests.post(f"{base_url}/api/v1/sweep/wallets/master", 
                               json={"partner_id": "test_partner_001"}, 
                               headers=headers)
        
        if response.status_code == 200:
            master_data = response.json()
            print("✅ 마스터 지갑 생성 성공:")
            print(f"   - 마스터 주소: {master_data.get('collection_address')}")
            print(f"   - 지갑 ID: {master_data.get('id')}")
            
            master_wallet_id = master_data.get('id')
            
            # 3. 사용자 지갑 생성 API 테스트
            user_wallets = []
            for i in range(1, 4):  # 3개 사용자 지갑만 테스트
                user_response = requests.post(f"{base_url}/api/v1/sweep/addresses", 
                                             json={
                                                 "user_id": i,  # 정수로 변경
                                                 "partner_id": "test_partner_001",  # partner_id 추가
                                                 "is_active": True,
                                                 "is_monitored": True,
                                                 "priority_level": 1
                                             }, 
                                             headers=headers)
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    user_wallets.append(user_data)
                    print(f"✅ 사용자 지갑 {i} 생성 성공: {user_data.get('address')}")
                else:
                    print(f"❌ 사용자 지갑 {i} 생성 실패: {user_response.status_code}")
                    print(f"   에러: {user_response.text}")
            
            # 3.5 파트너 지갑 정보 조회 (테스트에서는 ID 1 사용)
            # API가 없으므로 DB에 미리 생성된 지갑이 있다고 가정
            print("ℹ️ 파트너 지갑 API가 아직 구현되지 않아 기존 지갑 ID 사용")
            partner_wallet_id = 1
            print(f"🔍 파트너 지갑 ID: {partner_wallet_id} 사용")
                
            # 4. Sweep 설정 생성 또는 조회 API 테스트
            sweep_response = requests.post(f"{base_url}/api/v1/sweep/config", 
                                          json={
                                              "destination_wallet_id": partner_wallet_id,  # 파트너 지갑 ID 사용
                                              "partner_id": "test_partner_001",
                                              "is_enabled": True,
                                              "auto_sweep_enabled": True,
                                              "min_sweep_amount": "10.0",
                                              "sweep_interval_minutes": 60
                                          }, 
                                          headers=headers)
            
            if sweep_response.status_code == 200:
                sweep_data = sweep_response.json()
                print("✅ Sweep 설정 생성 성공:")
                print(f"   - Sweep ID: {sweep_data.get('id')}")
                print(f"   - 최소 스위프 금액: {sweep_data.get('min_sweep_amount')} TRX")
                
            elif sweep_response.status_code == 400 and "already exists" in sweep_response.text:
                print("ℹ️ Sweep 설정이 이미 존재합니다. 기존 설정을 조회합니다.")
                # 기존 설정 조회
                list_response = requests.get(f"{base_url}/api/v1/sweep/config", headers=headers)
                if list_response.status_code == 200:
                    sweep_list = list_response.json()
                    if sweep_list:
                        sweep_data = sweep_list[0]  # 첫 번째 설정 사용
                        print("✅ 기존 Sweep 설정 조회 성공:")
                        print(f"   - Sweep ID: {sweep_data.get('id')}")
                        print(f"   - 최소 스위프 금액: {sweep_data.get('min_sweep_amount')} TRX")
                    else:
                        print("❌ Sweep 설정 목록이 비어있습니다.")
                        return
                else:
                    print(f"❌ Sweep 목록 조회 실패: {list_response.status_code}")
                    return
            else:
                print(f"❌ Sweep 설정 생성 실패: {sweep_response.status_code}")
                print(f"   에러: {sweep_response.text}")
                return
                
            # 5. Sweep 목록 조회 API 테스트
            list_response = requests.get(f"{base_url}/api/v1/sweep/config", headers=headers)
            if list_response.status_code == 200:
                sweep_list = list_response.json()
                print(f"✅ Sweep 목록 조회 성공: {len(sweep_list)} 개 설정")
            else:
                print(f"❌ Sweep 목록 조회 실패: {list_response.status_code}")
                
            # 6. 마스터 지갑 조회 API 테스트
            master_get_response = requests.get(f"{base_url}/api/v1/sweep/wallets/master", headers=headers)
            if master_get_response.status_code == 200:
                master_get_data = master_get_response.json()
                print("✅ 마스터 지갑 조회 성공:")
                print(f"   - 마스터 주소: {master_get_data.get('collection_address')}")
                print(f"   - 생성된 주소 수: {master_get_data.get('total_addresses_generated')}")
            else:
                print(f"❌ 마스터 지갑 조회 실패: {master_get_response.status_code}")
                
            print("\n🎉 모든 기본 API 테스트 완료!")
            print(f"📊 테스트 결과:")
            print(f"   - 마스터 지갑: {master_data.get('collection_address')}")
            print(f"   - 사용자 지갑: {len(user_wallets)}개")
            print(f"   - Sweep 설정: 활성화")
            
            return {
                "master_wallet": master_data,
                "user_wallets": user_wallets,
                "sweep_config": sweep_data if 'sweep_data' in locals() else None
            }
                
        else:
            print(f"❌ 마스터 지갑 생성 실패: {response.status_code}")
            print(f"   에러: {response.text}")
            
    except Exception as e:
        print(f"❌ API 테스트 중 오류 발생: {e}")
    
    # 6. 수동 Sweep 테스트
    try:
        print("\n🚀 수동 Sweep 테스트 시작")
        
        # 사용자 주소 목록 생성
        deposit_addresses = []
        for wallet in user_wallets:
            deposit_addresses.append({
                "address": wallet.get("address"),
                "id": wallet.get("id")
            })
        
        # 배치 수동 Sweep API 호출
        batch_sweep_response = requests.post(
            f"{base_url}/api/v1/sweep/manual/batch",
            json={
                "addresses": [addr["address"] for addr in deposit_addresses[:2]], # 처음 2개 주소만 사용
                "partner_id": "test_partner_001",
                "force": True,
                "priority": "high"
            },
            headers=headers
        )
        
        if batch_sweep_response.status_code == 200:
            batch_result = batch_sweep_response.json()
            print("✅ 배치 수동 Sweep 요청 성공:")
            print(f"   - 요청 ID: {batch_result.get('request_id')}")
            print(f"   - 요청된 주소 수: {batch_result.get('total_addresses')}")
            
            # Sweep 로그 조회
            time.sleep(1)  # 로그가 생성될 시간 대기
            log_response = requests.get(
                f"{base_url}/api/v1/sweep/logs?partner_id=test_partner_001&limit=5",
                headers=headers
            )
            
            if log_response.status_code == 200:
                logs = log_response.json()
                print(f"✅ Sweep 로그 조회 성공: {len(logs)} 개 로그")
                if logs:
                    print(f"   - 최신 로그: {logs[0].get('status')}, 금액: {logs[0].get('amount')} TRX")
            else:
                print(f"❌ Sweep 로그 조회 실패: {log_response.status_code}")
                
        else:
            print(f"❌ 배치 수동 Sweep 요청 실패: {batch_sweep_response.status_code}")
            print(f"   에러: {batch_sweep_response.text}")

        print("\n✅ Sweep API 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 수동 Sweep 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    print("서버 시작 대기 중...")
    time.sleep(2)
    test_sweep_api()
