#!/usr/bin/env python3
"""
Sweep 테스트 스크립트 (메인 시스템용)
모든 사용자 주소에서 마스터 수집 주소로 TRX Sweep
"""
import sys
import os
import json
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.encryption import EncryptionService
from tronpy import Tron
from tronpy.keys import PrivateKey

print("🧹 Sweep 테스트 시작")
print("=" * 50)

def sweep_test():
    """모든 사용자 주소에서 마스터 주소로 Sweep"""
    
    # 결과 파일에서 주소 정보 로드
    try:
        with open("api_test_result.json", "r") as f:
            result = json.load(f)
    except FileNotFoundError:
        print("❌ api_test_result.json 파일을 찾을 수 없습니다.")
        return False
    
    master_address = result["master_collection_address"]
    user_addresses = result["user_addresses"]
    
    print(f"📍 마스터 수집 주소: {master_address}")
    print(f"👥 사용자 주소 수: {len(user_addresses)}개")
    print()
    
    # TRON 네트워크 연결
    tron = Tron(network='nile')  # 테스트넷
    
    # DB 연결
    engine = create_engine('sqlite:///dev.db')
    SessionLocal = sessionmaker(bind=engine)
    encryption_service = EncryptionService()
    
    print("🔍 각 사용자 주소 잔액 확인 및 Sweep 시작...")
    
    successful_sweeps = 0
    total_swept = 0.0
    fee_amount = 1.1 * 1_000_000  # 수수료 여유분 1.1 TRX
    
    for i, user_info in enumerate(user_addresses, 1):
        user_address = user_info["address"]
        user_id = user_info["user_id"]
        
        print(f"\n{i:2d}. {user_id} ({user_address})")
        
        try:
            # 잔액 확인
            balance = tron.get_account_balance(user_address)
            print(f"    💰 잔액: {balance} TRX")
            
            if balance <= 1.5:  # 최소 Sweep 가능 잔액
                print(f"    ⚠️ 잔액이 부족합니다 (최소 1.5 TRX 필요)")
                continue
            
            # DB에서 개인키 조회
            db = SessionLocal()
            try:
                from app.models.sweep import UserDepositAddress
                
                user_record = db.query(UserDepositAddress).filter_by(
                    address=user_address
                ).first()
                
                if not user_record:
                    print(f"    ❌ 주소 레코드를 찾을 수 없습니다")
                    continue
                
                # 개인키 복호화
                encrypted_parts = user_record.encrypted_private_key.split(':')
                encrypted_key = encrypted_parts[0]
                salt = encrypted_parts[1]
                
                private_key_hex = encryption_service.decrypt(encrypted_key, salt)
                private_key = PrivateKey(bytes.fromhex(private_key_hex))
                
            except Exception as e:
                print(f"    ❌ 개인키 조회 실패: {e}")
                continue
            finally:
                db.close()
            
            # Sweep 금액 계산 (수수료 제외)
            balance_sun = int(balance * 1_000_000)
            sweep_amount = balance_sun - int(fee_amount)
            
            if sweep_amount <= 0:
                print(f"    ⚠️ Sweep 불가 (수수료 부족)")
                continue
            
            sweep_trx = sweep_amount / 1_000_000
            print(f"    💸 Sweep 금액: {sweep_trx:.6f} TRX")
            
            # Sweep 트랜잭션 생성 및 전송
            txn = (
                tron.trx.transfer(
                    user_address,
                    master_address,
                    sweep_amount
                )
                .memo(f"Sweep from {user_id}")
                .build()
                .sign(private_key)
            )
            
            # 트랜잭션 브로드캐스트
            receipt = tron.broadcast(txn)
            tx_id = receipt['txid']
            
            print(f"    ✅ Sweep 성공! TxID: {tx_id}")
            print(f"    🔗 확인: https://nile.tronscan.org/#/transaction/{tx_id}")
            
            successful_sweeps += 1
            total_swept += sweep_trx
            
            # 다음 Sweep 전 잠시 대기
            import time
            time.sleep(2)
            
        except Exception as e:
            print(f"    ❌ Sweep 실패: {e}")
            continue
    
    print(f"\n📊 Sweep 테스트 완료!")
    print(f"   ✅ 성공: {successful_sweeps}/{len(user_addresses)}개")
    print(f"   💰 총 Sweep량: {total_swept:.6f} TRX")
    
    # 마스터 주소 최종 잔액 확인
    try:
        final_balance = tron.get_account_balance(master_address)
        print(f"   📍 마스터 최종 잔액: {final_balance} TRX")
    except Exception as e:
        print(f"   ❌ 마스터 잔액 확인 실패: {e}")
    
    # Sweep 결과 로그 저장
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "master_address": master_address,
        "total_users": len(user_addresses),
        "successful_sweeps": successful_sweeps,
        "total_swept_trx": total_swept,
        "sweep_details": []
    }
    
    with open("sweep_test_log.json", "w") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\n📝 Sweep 테스트 로그가 sweep_test_log.json에 저장되었습니다.")
    
    if successful_sweeps > 0:
        print("\n🎉 Sweep 테스트 성공!")
        print("메인 시스템의 Sweep 자동화가 정상 작동합니다!")
        return True
    else:
        print(f"\n❌ 모든 Sweep이 실패했습니다.")
        return False

if __name__ == "__main__":
    success = sweep_test()
    if success:
        print("\n✅ Sweep 테스트 성공!")
    else:
        print("\n❌ Sweep 테스트 실패!")
