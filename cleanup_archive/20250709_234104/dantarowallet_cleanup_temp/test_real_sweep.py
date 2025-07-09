#!/usr/bin/env python3
"""
실제 Sweep 기능 테스트
TRX가 있는 사용자 지갑들을 찾아서 Sweep 실행
"""
import requests
import json
import time
from tronpy import Tron

def test_real_sweep():
    """실제 Sweep 기능 테스트"""
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }
    
    print("🚀 실제 Sweep 기능 테스트 시작")
    
    # TRON 네트워크 연결
    tron = Tron(network='nile')
    
    # 1. 현재 사용자 지갑들의 잔고 확인
    print("\n🔍 사용자 지갑들의 TRX 잔고 확인")
    
    # 이전 테스트에서 생성된 사용자 주소들
    user_addresses = [
        "TCtngvMGpGKdttL44pR4xp1NG3urjBCyzj",  # test_user_001
        "TDvtx6ZgExocUPxht3sctGvjCj6gDfZ844",  # test_user_002  
        "TS1ZRcrPnzLporL9641fFpj8PUPH7eoReM",  # test_user_003
        "TLacpipkBT136j6E9XxPMYfT3nXAsvNtyB",  # test_user_004
        "TKhGe5XMAJ6brzzbWVBHGb3N2WdbcU7gRg",  # test_user_005
    ]
    
    addresses_with_balance = []
    
    for i, address in enumerate(user_addresses):
        try:
            balance_sun = tron.get_account_balance(address)
            balance_trx = balance_sun / 1_000_000
            
            print(f"  사용자 {i+1}: {address}")
            print(f"    TRX 잔고: {balance_trx:.6f} TRX")
            
            if balance_trx > 0:
                addresses_with_balance.append({
                    'address': address,
                    'balance': balance_trx
                })
                
        except Exception as e:
            print(f"    ❌ 잔고 조회 실패: {e}")
    
    print(f"\n💰 TRX가 있는 사용자 지갑: {len(addresses_with_balance)} 개")
    for addr_info in addresses_with_balance:
        print(f"  - {addr_info['address']}: {addr_info['balance']:.6f} TRX")
    
    if not addresses_with_balance:
        print("\n❌ TRX가 있는 사용자 지갑이 없습니다. 먼저 TRX를 분배해주세요.")
        return
    
    # 2. 수동 Sweep 실행
    print(f"\n🔄 {len(addresses_with_balance)} 개 지갑에 대해 수동 Sweep 실행")
    
    try:
        # 배치 수동 Sweep API 호출
        sweep_addresses = [addr['address'] for addr in addresses_with_balance]
        
        batch_sweep_response = requests.post(
            f"{base_url}/api/v1/sweep/manual/batch",
            json={
                "addresses": sweep_addresses,
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
            print(f"   - 예상 수집 금액: {batch_result.get('estimated_amount')} TRX")
            
            # 3. Sweep 진행 상황 모니터링
            print("\n⏳ Sweep 진행 상황 모니터링 (30초)")
            for i in range(6):  # 30초간 5초마다 확인
                time.sleep(5)
                
                # Sweep 로그 조회
                log_response = requests.get(
                    f"{base_url}/api/v1/sweep/logs?partner_id=test_partner_001&limit=10",
                    headers=headers
                )
                
                if log_response.status_code == 200:
                    logs = log_response.json()
                    if logs:
                        latest_log = logs[0]
                        print(f"   {i*5+5}초: 최신 로그 - {latest_log.get('status')}, "
                              f"금액: {latest_log.get('amount')} TRX, "
                              f"시간: {latest_log.get('created_at')}")
                    else:
                        print(f"   {i*5+5}초: 아직 로그가 없습니다.")
                else:
                    print(f"   {i*5+5}초: 로그 조회 실패 ({log_response.status_code})")
            
            # 4. 최종 결과 확인
            print("\n📊 최종 Sweep 결과 확인")
            
            # 목적지 지갑 잔고 확인
            master_address = "TAjGrq1zVHq8dHQGBnpV8odW33H1QZZ22H"
            try:
                final_balance_sun = tron.get_account_balance(master_address)
                final_balance_trx = final_balance_sun / 1_000_000
                print(f"   목적지 지갑 최종 잔고: {final_balance_trx:.6f} TRX")
            except:
                print("   목적지 지갑 잔고 조회 실패")
            
            # 사용자 지갑들 잔고 재확인
            print("\n   사용자 지갑들 최종 잔고:")
            for addr_info in addresses_with_balance:
                try:
                    final_user_balance_sun = tron.get_account_balance(addr_info['address'])
                    final_user_balance_trx = final_user_balance_sun / 1_000_000
                    print(f"     {addr_info['address']}: {final_user_balance_trx:.6f} TRX")
                except:
                    print(f"     {addr_info['address']}: 잔고 조회 실패")
                    
        else:
            print(f"❌ 배치 수동 Sweep 요청 실패: {batch_sweep_response.status_code}")
            print(f"   에러: {batch_sweep_response.text}")
            
    except Exception as e:
        print(f"❌ Sweep 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    print("서버 시작 대기 중...")
    time.sleep(2)
    test_real_sweep()
