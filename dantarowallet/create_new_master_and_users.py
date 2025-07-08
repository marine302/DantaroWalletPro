#!/usr/bin/env python3
"""
새로운 마스터 지갑 생성 및 사용자 주소 10개 생성
"""
import asyncio
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.services.sweep.hd_wallet_service import HDWalletService
from app.core.database import engine as async_engine
from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 동기 엔진 생성 (기존 데이터 삭제용)
sync_engine = create_engine('sqlite:///dev.db')
SessionLocal = sessionmaker(bind=sync_engine)

async def create_new_master_and_addresses():
    """새로운 마스터 지갑 생성 및 사용자 주소 10개 생성"""
    
    # 1. 기존 데이터 삭제
    logger.info("=== 기존 Sweep 데이터 삭제 ===")
    db = SessionLocal()
    try:
        # 외래키 제약 조건 비활성화
        db.execute(text("PRAGMA foreign_keys=OFF"))
        
        # 테이블 순서대로 삭제 (외래키 의존성 고려)
        db.execute(text("DELETE FROM sweep_logs"))
        db.execute(text("DELETE FROM sweep_queues"))
        db.execute(text("DELETE FROM sweep_configurations"))
        db.execute(text("DELETE FROM user_deposit_addresses"))
        db.execute(text("DELETE FROM hd_wallet_masters"))
        
        db.commit()
        logger.info("✅ 기존 데이터 삭제 완료")
    except Exception as e:
        logger.error(f"데이터 삭제 실패: {e}")
        db.rollback()
    finally:
        db.close()
    
    # 2. 새로운 마스터 지갑 생성
    logger.info("=== 새로운 마스터 지갑 생성 ===")
    
    # AsyncSession 생성
    from app.core.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    
    # 비동기 엔진 및 세션 생성
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{settings.DATABASE_URL.split('///')[-1]}")
    AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as async_db:
        try:
            hd_service = HDWalletService(async_db)
            
            # 새로운 마스터 지갑 생성
            master_wallet = await hd_service.create_master_wallet("test_partner_001")
            logger.info(f"✅ 마스터 지갑 생성 완료 - ID: {master_wallet.id}")
            
            # 마스터 수집 주소 생성 (인덱스 0)
            master_address_data = await hd_service.generate_deposit_address(
                "test_partner_001", 
                0  # user_id를 int로 변경
            )
            master_collection_address = master_address_data.address
            logger.info(f"✅ 마스터 수집 주소: {master_collection_address}")
            
            # 3. 사용자 입금 주소 10개 생성
            logger.info("=== 사용자 입금 주소 10개 생성 ===")
            user_addresses = []
            
            for i in range(1, 11):  # 1~10번 사용자
                user_id = i  # str에서 int로 변경
                address_data = await hd_service.generate_deposit_address(
                    "test_partner_001", 
                    user_id
                )
                user_addresses.append({
                    'user_id': user_id,
                    'address': address_data.address,
                    'index': address_data.derivation_index
                })
                logger.info(f"  {i:2d}. {address_data.address} (사용자: {user_id})")
            
            await async_db.commit()
            
            # 4. 모든 주소 정보 출력
            logger.info("=== 생성 완료 요약 ===")
            logger.info(f"마스터 수집 주소: {master_collection_address}")
            logger.info(f"사용자 주소 개수: {len(user_addresses)}개")
            logger.info("")
            logger.info("=== 다음 단계 안내 ===")
            logger.info(f"1. 마스터 수집 주소({master_collection_address})에 200 TRX 전송")
            logger.info("2. python3 distribute_to_users.py 실행하여 각 사용자에게 20 TRX씩 분산")
            logger.info("3. python3 test_user_sweep.py 실행하여 Sweep 테스트")
            
            return master_collection_address, user_addresses
            
        except Exception as e:
            logger.error(f"마스터 지갑 생성 실패: {e}")
            await async_db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(create_new_master_and_addresses())
