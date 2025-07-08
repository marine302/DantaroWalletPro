#!/usr/bin/env python3
"""
마스터 지갑 생성 및 collection_address 필드 디버깅
"""
import asyncio
import os
import sys
from pprint import pprint

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import AsyncSession, async_sessionmaker, engine
from app.services.sweep.hd_wallet_service import HDWalletService


async def test_master_wallet():
    """마스터 지갑 생성 및 collection_address 필드 디버깅"""
    print("🔍 마스터 지갑 collection_address 필드 디버깅")
    
    # 세션 팩토리 생성
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    # 세션 생성
    async with session_factory() as db:
        # 테스트용 파트너 ID
        test_partner_id = "test_partner_001"
        
        # 1. 기존 마스터 지갑 삭제 (테스트용)
        print("1️⃣ 기존 마스터 지갑 삭제 중...")
        try:
            await db.execute(
                text("DELETE FROM hd_wallet_masters WHERE partner_id = :partner_id"),
                {"partner_id": test_partner_id}
            )
            await db.commit()
            print("✅ 기존 마스터 지갑 삭제 완료")
        except Exception as e:
            print(f"❌ 기존 마스터 지갑 삭제 실패: {e}")
        
        # 2. 마스터 지갑 생성
        print("2️⃣ 새 마스터 지갑 생성 중...")
        try:
            hd_service = HDWalletService(db)
            new_master = await hd_service.create_master_wallet(test_partner_id)
            
            # SQLAlchemy 모델 객체 출력
            print("✅ 마스터 지갑 생성 성공")
            print(f"▶️ ID: {new_master.id}")
            print(f"▶️ 파트너 ID: {new_master.partner_id}")
            print(f"▶️ 공개키: {new_master.public_key}")
            print(f"▶️ 컬렉션 주소: {new_master.collection_address}")
            
        except Exception as e:
            print(f"❌ 마스터 지갑 생성 실패: {e}")
            return
        
        # 3. DB에 직접 확인
        print("3️⃣ DB에서 마스터 지갑 직접 조회 중...")
        try:
            # 직접 SQL로 조회
            result = await db.execute(
                text("SELECT id, partner_id, public_key, collection_address FROM hd_wallet_masters WHERE partner_id = :partner_id"),
                {"partner_id": test_partner_id}
            )
            db_data = result.fetchone()
            
            if db_data:
                print("✅ DB 조회 성공")
                print(f"▶️ ID: {db_data.id}")
                print(f"▶️ 파트너 ID: {db_data.partner_id}")
                print(f"▶️ 공개키: {db_data.public_key}")
                print(f"▶️ 컬렉션 주소: {db_data.collection_address}")
                
                # collection_address 값이 None인지 확인
                if db_data.collection_address is None:
                    print("⚠️ 컬렉션 주소가 None 값입니다!")
                elif not db_data.collection_address:
                    print("⚠️ 컬렉션 주소가 빈 문자열입니다!")
                else:
                    print("✅ 컬렉션 주소가 정상적으로 설정되어 있습니다.")
            else:
                print("❌ DB에서 마스터 지갑을 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"❌ DB 조회 실패: {e}")
        
        # 4. HDWalletService.get_master_wallet_stats 테스트
        print("4️⃣ get_master_wallet_stats 메소드 테스트 중...")
        try:
            stats = await hd_service.get_master_wallet_stats(test_partner_id)
            print("✅ 통계 조회 성공")
            print(f"▶️ ID: {stats.get('id')}")
            print(f"▶️ 파트너 ID: {stats.get('partner_id')}")
            print(f"▶️ 컬렉션 주소: {stats.get('collection_address')}")
            
            # 반환된 데이터 전체 확인
            print("\n📋 반환된 전체 데이터:")
            pprint(stats)
            
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")


if __name__ == "__main__":
    asyncio.run(test_master_wallet())
