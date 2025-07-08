#!/usr/bin/env python3
"""
Sweep API 테스트 - 사용자 지갑에서 마스터 지갑으로 TRX 수집
"""
import requests
import json
import time
import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def test_sweep_api():
    """Sweep API를 통해 TRX 수집 테스트"""
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }
    
    print("🚀 Sweep API 테스트 시작")
    print("=" * 50)
    
    # 1. 서버 상태 확인
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 성공")
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return
    
    # 2. 사용자 입금 주소 조회
    async for db in get_db():
        try:
            result = await db.execute(text(
                "SELECT id, user_id, address FROM user_deposit_addresses WHERE is_active = 1 ORDER BY id DESC LIMIT 5"
            ))
            addresses = result.fetchall()
            
            print(f"\n📋 Sweep 대상 주소 ({len(addresses)} 개):")
            for addr in addresses:
                print(f"  - ID: {addr.id}, 사용자: {addr.user_id}, 주소: {addr.address}")
            
            if not addresses:
                print("❌ Sweep 대상 주소가 없습니다.")
                return
            
            # 3. 배치 수동 Sweep 요청
            sweep_addresses = [addr.address for addr in addresses]
            
            print(f"\n🔄 배치 Sweep 요청 시작...")
            sweep_response = requests.post(
                f"{base_url}/api/v1/sweep/manual/batch",
                json={
                    "addresses": sweep_addresses,
                    "partner_id": "test_partner_001",
                    "force": True,
                    "priority": "high"
                },
                headers=headers,
                timeout=30
            )
            
            if sweep_response.status_code == 200:
                sweep_result = sweep_response.json()
                print("✅ 배치 Sweep 요청 성공!")
                print(f"   요청 ID: {sweep_result.get('request_id')}")
                print(f"   대상 주소 수: {sweep_result.get('total_addresses')}")
                print(f"   처리 상태: {sweep_result.get('status')}")
                
                # 4. Sweep 로그 확인
                print(f"\n📊 Sweep 로그 확인 중...")
                time.sleep(3)  # 처리 시간 대기
                
                log_response = requests.get(
                    f"{base_url}/api/v1/sweep/logs?partner_id=test_partner_001&limit=10",
                    headers=headers
                )
                
                if log_response.status_code == 200:
                    logs = log_response.json()
                    print(f"✅ Sweep 로그 조회 성공: {len(logs)} 개")
                    
                    for i, log in enumerate(logs[:5]):  # 최근 5개만 표시
                        print(f"  {i+1}. 상태: {log.get('status')}, 금액: {log.get('amount')} TRX")
                        if log.get('tx_hash'):
                            print(f"     TxID: {log.get('tx_hash')}")
                else:
                    print(f"❌ Sweep 로그 조회 실패: {log_response.status_code}")
                    print(f"   응답: {log_response.text}")
                
                # 5. 마스터 지갑 잔고 확인
                print(f"\n💰 마스터 지갑 잔고 확인...")
                balance_cmd = 'curl -s "https://nile.trongrid.io/v1/accounts/TAjGrq1zVHq8dHQGBnpV8odW33H1QZZ22H"'
                import subprocess
                result = subprocess.run(balance_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    import json as json_lib
                    data = json_lib.loads(result.stdout)
                    if data.get('data'):
                        balance_sun = data['data'][0].get('balance', 0)
                        balance_trx = balance_sun / 1_000_000
                        print(f"📱 마스터 지갑 현재 잔고: {balance_trx:.6f} TRX")
                
            else:
                print(f"❌ 배치 Sweep 요청 실패: {sweep_response.status_code}")
                print(f"   응답: {sweep_response.text}")
                
                # 개별 Sweep 시도
                print(f"\n🔄 개별 Sweep 시도...")
                for addr in addresses[:2]:  # 첫 2개만 시도
                    try:
                        single_response = requests.post(
                            f"{base_url}/api/v1/sweep/manual",
                            json={
                                "address": addr.address,
                                "partner_id": "test_partner_001",
                                "force": True
                            },
                            headers=headers,
                            timeout=15
                        )
                        
                        if single_response.status_code == 200:
                            single_result = single_response.json()
                            print(f"✅ {addr.address} Sweep 성공")
                            print(f"   TxID: {single_result.get('tx_hash')}")
                        else:
                            print(f"❌ {addr.address} Sweep 실패: {single_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ {addr.address} Sweep 오류: {e}")
            
            print(f"\n🎉 Sweep 테스트 완료!")
            
        except Exception as e:
            print(f"❌ DB 오류: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    print("서버 시작 대기 중...")
    time.sleep(2)
    asyncio.run(test_sweep_api())
