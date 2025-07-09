#!/usr/bin/env python3
"""
새로운 마스터 지갑 생성 및 TRX 분산 전송
"""

import asyncio
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """새로운 마스터 지갑 생성 및 TRX 분산 전송"""
    
    logger.info("=== 새로운 마스터 지갑 생성 ===")
    logger.info("")
    
    # 1. 새로운 지갑 생성
    logger.info("🔑 새로운 마스터 지갑 생성 중...")
    
    tron = Tron(network='nile')
    account = tron.generate_address()
    
    private_key_hex = account['private_key']
    address = account['base58check_address']
    
    logger.info(f"✅ 새로운 마스터 지갑 생성 완료:")
    logger.info(f"   📍 주소: {address}")
    logger.info(f"   🔐 개인키: {private_key_hex}")
    logger.info("")
    
    # 2. 테스트용 주소들
    target_addresses = [
        "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo",  # 주소 2
        "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",  # 주소 3
        "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",  # 주소 4
    ]
    
    tron = Tron(network='nile')
    
    logger.info("📋 계획:")
    logger.info(f"1. 새 마스터 지갑 {address}에 Faucet으로 TRX 받기")
    logger.info("2. 이 지갑에서 테스트 주소들로 TRX 분산 전송")
    logger.info("")
    
    for i, addr in enumerate(target_addresses, 2):
        logger.info(f"   주소 {i}: {addr} → 10 TRX 전송 예정")
    
    logger.info("")
    logger.info("🌐 Faucet에서 TRX 받기:")
    logger.info("https://nileex.io/")
    logger.info(f"주소: {address}")
    logger.info("")
    
    # 개인키를 파일로 저장 (임시)
    with open('new_master_key.txt', 'w') as f:
        f.write(f"Address: {address}\n")
        f.write(f"Private Key: {private_key_hex}\n")
    
    logger.info("💾 개인키 정보가 'new_master_key.txt' 파일에 저장되었습니다.")
    logger.info("")
    logger.info("⚠️  다음 단계:")
    logger.info("1. 위 주소에 Faucet으로 TRX 받기")
    logger.info("2. python3 distribute_with_new_master.py 실행")

if __name__ == "__main__":
    asyncio.run(main())
