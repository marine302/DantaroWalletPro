#!/usr/bin/env python3
"""
마스터 지갑에서 테스트 주소들로 TRX 분산 전송
"""

import asyncio
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """마스터 지갑에서 테스트 주소들로 TRX 분산 전송"""
    
    logger.info("=== 마스터 지갑에서 TRX 분산 전송 ===")
    logger.info("")
    
    # 마스터 지갑 정보 (테스트용)
    master_address = "TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp"
    
    # 테스트 주소들 (2, 3, 4번 주소)
    target_addresses = [
        "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo",  # 주소 2 (사용자 12346)
        "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",  # 주소 3 (사용자 12347)
        "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",  # 주소 4 (사용자 12348)
    ]
    
    send_amount = 100  # 각 주소당 100 TRX
    
    tron = Tron(network='nile')
    
    # 마스터 지갑 잔액 확인
    logger.info(f"📋 마스터 지갑: {master_address}")
    try:
        account = tron.get_account(master_address)
        if account:
            balance_sun = account.get('balance', 0)
            balance_trx = balance_sun / 1_000_000
            logger.info(f"   💰 현재 잔액: {balance_trx:.6f} TRX")
            
            if balance_trx < send_amount * len(target_addresses) + 10:  # 수수료 여유분 포함
                logger.error(f"   ❌ 잔액 부족. 필요: {send_amount * len(target_addresses) + 10} TRX")
                return
        else:
            logger.error("   ❌ 마스터 지갑을 찾을 수 없습니다.")
            return
    except Exception as e:
        logger.error(f"   ❌ 마스터 지갑 조회 실패: {e}")
        return
    
    logger.info("")
    logger.info("⚠️  실제 전송을 위해서는 마스터 지갑의 개인키가 필요합니다.")
    logger.info("현재는 시뮬레이션만 진행합니다.")
    logger.info("")
    
    # 각 주소로 전송 시뮬레이션
    for i, address in enumerate(target_addresses, 2):
        logger.info(f"📤 주소 {i}로 {send_amount} TRX 전송 예정:")
        logger.info(f"   📍 수신자: {address}")
        logger.info(f"   💸 금액: {send_amount} TRX")
        
        # 실제 전송은 개인키가 있을 때만 가능
        # 지금은 계획만 표시
        logger.info(f"   ✅ 전송 준비 완료")
        logger.info("")
    
    logger.info("💡 실제 전송 후 다음 명령어로 Sweep 테스트:")
    logger.info("python3 test_tron_transactions.py > multi_sweep_result.log 2>&1")
    logger.info("")
    
    # 대안: Faucet 방법 안내
    logger.info("🌐 또는 각 주소에 직접 Faucet으로 TRX 받기:")
    logger.info("Faucet: https://nileex.io/")
    logger.info("")
    for i, address in enumerate(target_addresses, 2):
        logger.info(f"   {i}. {address}")

if __name__ == "__main__":
    asyncio.run(main())
