#!/usr/bin/env python3
"""
간단한 TRON 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.sweep.hd_wallet_service import HDWalletService
from app.models.partner import Partner
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simple_test():
    """간단한 테스트"""
    logger.info("=== 간단한 TRON 테스트 시작 ===")
    
    try:
        # DB 연결 테스트
        logger.info("1. DB 연결 테스트...")
        async for db in get_db():
            logger.info("✅ DB 연결 성공")
            
            # Partner 조회 테스트
            logger.info("2. Partner 조회 테스트...")
            existing_partner = await db.get(Partner, "test_partner_001")
            if existing_partner:
                logger.info(f"✅ 기존 파트너 발견: {existing_partner.name}")
            else:
                logger.info("❓ 파트너 없음 - 새로 생성합니다")
                
                # 새 파트너 생성
                new_partner = Partner(
                    id="test_partner_001",
                    name="Test Partner",
                    display_name="테스트 파트너",
                    domain="test.example.com",
                    contact_email="test@example.com",
                    api_key="test_api_key",
                    api_secret_hash="test_secret_hash",
                    status="active",
                    onboarding_status="completed"
                )
                db.add(new_partner)
                await db.commit()
                await db.refresh(new_partner)
                logger.info(f"✅ 새 파트너 생성: {new_partner.id}")
            
            # HD Wallet 서비스 테스트
            logger.info("3. HD Wallet 서비스 테스트...")
            hd_service = HDWalletService(db)
            logger.info("✅ HD Wallet 서비스 초기화 성공")
            
            # 마스터 지갑 생성
            logger.info("4. 마스터 지갑 생성...")
            master_wallet = await hd_service.create_master_wallet("test_partner_001")
            logger.info(f"✅ 마스터 지갑: {master_wallet.id}")
            
            # 사용자 주소 생성
            logger.info("5. 사용자 주소 생성...")
            user_address = await hd_service.generate_deposit_address("test_partner_001", 12345)
            logger.info(f"✅ 생성된 주소: {user_address.address}")
            
            break
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("✅ 모든 테스트 완료!")
    return True


if __name__ == "__main__":
    result = asyncio.run(simple_test())
    if result:
        print("\n🎉 테스트 성공!")
    else:
        print("\n❌ 테스트 실패!")
