#!/usr/bin/env python3
"""
메인 시스템 API 테스트 스크립트 (동기 버전)
Sweep 자동화 시스템을 직접 테스트합니다.
"""
import sys
import os
import json
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

print("🔧 메인 시스템 API 테스트 시작")
print("=" * 50)

def test_main_system():
    """메인 시스템의 Sweep API 기능을 직접 테스트"""
    
    # 동기 DB 연결 설정
    engine = create_engine('sqlite:///dev.db')
    SessionLocal = sessionmaker(bind=engine)
    
    print("\n1️⃣ 기존 데이터 정리 중...")
    
    # 기존 데이터 정리
    db = SessionLocal()
    try:
        # 기존 마스터 지갑과 주소들 삭제
        from app.models.sweep import HDWalletMaster, UserDepositAddress
        db.query(UserDepositAddress).delete()
        db.query(HDWalletMaster).delete() 
        db.commit()
        print("✅ 기존 데이터 정리 완료")
    except Exception as e:
        print(f"❌ 데이터 정리 오류: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n2️⃣ 새로운 마스터 지갑 생성 중...")
    
    # 동기 방식으로 새 마스터 지갑 생성
    db = SessionLocal()
    try:
        from app.core.encryption import EncryptionService
        from mnemonic import Mnemonic
        from tronpy import Tron
        from tronpy.keys import PrivateKey
        
        # TronPy로 간단하게 새 주소들 생성 (HD가 아닌 독립 주소들)
        tron = Tron(network='nile')  # 테스트넷
        encryption_service = EncryptionService()
        
        # 임시 시드 (실제로는 사용하지 않음)
        mnemo = Mnemonic("english")
        seed_phrase = mnemo.generate(strength=128)
        
        print(f"🔑 새 시드 생성됨 (12단어)")
        
        # 시드 암호화
        encrypted_seed, salt = encryption_service.encrypt(seed_phrase)
        encrypted_seed_with_salt = f"{encrypted_seed}:{salt}"
        
        # TronPy로 마스터 수집 주소 생성
        master_account = tron.generate_address()
        master_collection_address = master_account['base58check_address']
        master_private_key_hex = master_account['private_key']
        
        # public_key는 임시로 private_key로 설정 (테스트용)
        public_key_hex = master_private_key_hex[:64]  # 처음 64자만 사용
        
        # 마스터 지갑 DB에 저장 (public_key 포함)
        master_wallet = HDWalletMaster(
            partner_id="test_partner_001",
            encrypted_seed=encrypted_seed_with_salt,
            public_key=public_key_hex,  # public_key 추가
            derivation_path="m/44'/195'/0'/0",
            encryption_method="AES-256-GCM",
            key_version=1,
            last_index=0,
            total_addresses_generated=0
        )
        
        db.add(master_wallet)
        db.commit()
        db.refresh(master_wallet)
        
        print(f"✅ 새 마스터 지갑 생성됨 (ID: {master_wallet.id})")
        
        # TronPy로 마스터 수집 주소 생성
        master_account = tron.generate_address()
        master_collection_address = master_account['base58check_address']
        master_private_key_hex = master_account['private_key']
        
        # 마스터 수집 주소 개인키 암호화
        encrypted_master_key, master_salt = encryption_service.encrypt(master_private_key_hex)
        encrypted_master_key_with_salt = f"{encrypted_master_key}:{master_salt}"
        
        # 마스터 수집 주소를 DB에 저장
        master_address_record = UserDepositAddress(
            hd_wallet_id=master_wallet.id,
            user_id="master_collection",
            address=master_collection_address,
            derivation_index=0,
            encrypted_private_key=encrypted_master_key_with_salt,
            is_active=True,
            is_monitored=True,
            min_sweep_amount=0.1
        )
        
        db.add(master_address_record)
        
        print(f"📍 마스터 수집 주소: {master_collection_address}")
        
        print("\n3️⃣ 사용자 지갑 10개 생성 중...")
        
        # 사용자 지갑 10개 생성
        user_addresses = []
        for i in range(1, 11):  # 1번부터 10번까지
            user_id = f"test_user_{i:03d}"
            
            # TronPy로 사용자 주소 생성
            user_account = tron.generate_address()
            user_address = user_account['base58check_address']
            user_private_key_hex = user_account['private_key']
            
            # 사용자 개인키 암호화
            encrypted_user_key, user_salt = encryption_service.encrypt(user_private_key_hex)
            encrypted_user_key_with_salt = f"{encrypted_user_key}:{user_salt}"
            
            # 사용자 주소를 DB에 저장
            user_address_record = UserDepositAddress(
                hd_wallet_id=master_wallet.id,
                user_id=user_id,
                address=user_address,
                derivation_index=i,
                encrypted_private_key=encrypted_user_key_with_salt,
                is_active=True,
                is_monitored=True,
                min_sweep_amount=0.1
            )
            
            db.add(user_address_record)
            user_addresses.append(user_address_record)
            print(f"  👤 사용자 {i}: {user_address} (ID: {user_id})")
        
        # 마스터 지갑 정보 업데이트 (SQLAlchemy text() 사용)
        from sqlalchemy import text
        db.execute(
            text("UPDATE hd_wallet_masters SET last_index = 10, total_addresses_generated = 11 WHERE id = :id"),
            {"id": master_wallet.id}
        )
        
        db.commit()
        
        print(f"\n✅ 총 {len(user_addresses)}개 사용자 지갑 생성 완료")
        print(f"📋 마스터 수집 주소: {master_collection_address}")
        
        # 결과를 파일에 저장
        result = {
            "timestamp": datetime.now().isoformat(),
            "master_wallet_id": master_wallet.id,
            "master_collection_address": master_collection_address,
            "seed_phrase": seed_phrase,  # 테스트용으로만 저장
            "user_addresses": [
                {
                    "index": addr.derivation_index,
                    "user_id": addr.user_id, 
                    "address": addr.address
                }
                for addr in user_addresses
            ]
        }
        
        with open("api_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print("\n📝 결과가 api_test_result.json에 저장되었습니다.")
        print("\n4️⃣ 다음 단계:")
        print(f"   1. 마스터 주소({master_collection_address})에 TRX 200개 전송")
        print("   2. 분산 전송 스크립트 실행")
        print("   3. Sweep 테스트 실행")
        
        return result
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    result = test_main_system()
    
    if result:
        print("\n🎉 메인 시스템 API 테스트 성공!")
    else:
        print("\n❌ 메인 시스템 API 테스트 실패!")
