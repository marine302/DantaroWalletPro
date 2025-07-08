#!/usr/bin/env python3
"""
TRX 분산 전송 스크립트 (메인 시스템용)
마스터 수집 주소에서 사용자 주소들로 TRX를 20개씩 분산 전송
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

print("💸 TRX 분산 전송 시작")
print("=" * 50)

def distribute_trx():
    """마스터 주소에서 사용자 주소들로 TRX 분산 전송"""
    
    # 결과 파일에서 주소 정보 로드
    try:
        with open("api_test_result.json", "r") as f:
            result = json.load(f)
    except FileNotFoundError:
        print("❌ api_test_result.json 파일을 찾을 수 없습니다.")
        print("먼저 api_test_main.py를 실행하여 지갑들을 생성하세요.")
        return False
    
    master_address = result["master_collection_address"]
    user_addresses = result["user_addresses"]
    
    print(f"📍 마스터 수집 주소: {master_address}")
    print(f"👥 사용자 주소 수: {len(user_addresses)}개")
    print()
    
    # TRON 네트워크 연결
    tron = Tron(network='nile')  # 테스트넷
    
    # 마스터 주소 잔액 확인
    try:
        master_balance = tron.get_account_balance(master_address)
        print(f"💰 마스터 주소 현재 잔액: {master_balance} TRX")
        
        if master_balance < 200:
            print(f"❌ 잔액이 부족합니다. 최소 200 TRX가 필요합니다.")
            print(f"🌐 Faucet에서 TRX를 받으세요: https://nileex.io/")
            return False
            
    except Exception as e:
        print(f"❌ 마스터 주소 잔액 확인 실패: {e}")
        return False
    
    # DB에서 마스터 주소의 개인키 조회
    engine = create_engine('sqlite:///dev.db')
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        from app.models.sweep import UserDepositAddress
        
        # 마스터 수집 주소 레코드 조회
        master_record = db.query(UserDepositAddress).filter_by(
            address=master_address,
            user_id="master_collection"
        ).first()
        
        if not master_record:
            print(f"❌ 마스터 주소 레코드를 찾을 수 없습니다: {master_address}")
            return False
        
        # 개인키 복호화
        encryption_service = EncryptionService()
        encrypted_parts = master_record.encrypted_private_key.split(':')
        encrypted_key = encrypted_parts[0]
        salt = encrypted_parts[1]
        
        master_private_key_hex = encryption_service.decrypt(encrypted_key, salt)
        master_private_key = PrivateKey(bytes.fromhex(master_private_key_hex))
        
        print("🔑 마스터 주소 개인키 복호화 성공")
        
    except Exception as e:
        print(f"❌ 마스터 주소 개인키 조회 실패: {e}")
        return False
    finally:
        db.close()
    
    print(f"\n🚀 분산 전송 시작 (각 주소로 20 TRX씩)...")
    
    # 각 사용자 주소로 20 TRX씩 전송
    successful_transfers = 0
    transfer_amount = 20 * 1_000_000  # 20 TRX in SUN
    
    for i, user_info in enumerate(user_addresses, 1):
        user_address = user_info["address"]
        user_id = user_info["user_id"]
        
        try:
            print(f"  {i:2d}. {user_id} ({user_address}) 전송 중...")
            
            # 트랜잭션 생성 및 전송
            txn = (
                tron.trx.transfer(
                    master_address,
                    user_address,
                    transfer_amount
                )
                .memo(f"Distribute to {user_id}")
                .build()
                .sign(master_private_key)
            )
            
            # 트랜잭션 브로드캐스트
            receipt = tron.broadcast(txn)
            tx_id = receipt['txid']
            
            print(f"      ✅ 성공! TxID: {tx_id}")
            print(f"      🔗 확인: https://nile.tronscan.org/#/transaction/{tx_id}")
            
            successful_transfers += 1
            
            # 다음 전송 전 잠시 대기
            import time
            time.sleep(2)
            
        except Exception as e:
            print(f"      ❌ 실패: {e}")
            continue
    
    print(f"\n📊 분산 전송 완료!")
    print(f"   ✅ 성공: {successful_transfers}/{len(user_addresses)}개")
    print(f"   💸 총 전송량: {successful_transfers * 20} TRX")
    
    # 마스터 주소 최종 잔액 확인
    try:
        final_balance = tron.get_account_balance(master_address)
        print(f"   💰 마스터 잔액(최종): {final_balance} TRX")
    except:
        pass
    
    # 결과 로그 저장
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "master_address": master_address,
        "total_users": len(user_addresses),
        "successful_transfers": successful_transfers,
        "amount_per_user": 20,
        "total_amount_sent": successful_transfers * 20
    }
    
    with open("distribute_log.json", "w") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\n📝 분산 전송 로그가 distribute_log.json에 저장되었습니다.")
    
    if successful_transfers == len(user_addresses):
        print("\n🎉 모든 사용자에게 TRX 분산 전송이 완료되었습니다!")
        print("다음 단계: Sweep 테스트를 실행하세요.")
        return True
    else:
        print(f"\n⚠️ 일부 전송이 실패했습니다. ({successful_transfers}/{len(user_addresses)})")
        return False

if __name__ == "__main__":
    success = distribute_trx()
    if success:
        print("\n✅ 분산 전송 성공!")
    else:
        print("\n❌ 분산 전송 실패!")
