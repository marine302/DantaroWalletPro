#!/usr/bin/env python3
"""
실제 마스터 지갑 설정 및 TRX 분산 전송
"""

import asyncio
import logging
from tronpy import Tron

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """실제 마스터 지갑에서 테스트 주소들로 TRX 분산 전송 방법 안내"""
    
    logger.info("=== 마스터 지갑 TRX 분산 전송 방안 ===")
    logger.info("")
    
    # 현재 상황 분석
    tron = Tron(network='nile')
    
    # 마스터 지갑 잔액 확인
    master_address = "TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp"
    logger.info(f"📋 마스터 지갑: {master_address}")
    
    try:
        account = tron.get_account(master_address)
        if account:
            balance_sun = account.get('balance', 0)
            balance_trx = balance_sun / 1_000_000
            logger.info(f"   💰 현재 잔액: {balance_trx:.6f} TRX")
        else:
            logger.info(f"   💰 잔액: 0 TRX")
    except Exception as e:
        logger.error(f"   ❌ 조회 실패: {e}")
    
    logger.info("")
    logger.info("🎯 해결 방안:")
    logger.info("")
    
    logger.info("방법 1: 직접 Faucet으로 각 주소에 TRX 받기")
    logger.info("   - 각 주소마다 https://nileex.io/ 에서 개별적으로 TRX 받기")
    logger.info("   - 시간이 오래 걸리지만 확실한 방법")
    logger.info("")
    
    logger.info("방법 2: 첫 번째 주소를 임시 마스터로 사용")
    logger.info("   - TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL 주소에 추가 TRX 받기")
    logger.info("   - 이 주소에서 다른 주소들로 분산 전송")
    logger.info("   - 우리가 개인키를 가지고 있어서 전송 가능")
    logger.info("")
    
    logger.info("방법 3: 외부 지갑에서 직접 전송")
    logger.info("   - 개인 지갑(예: TronLink)에서 테스트 주소들로 직접 전송")
    logger.info("   - 가장 빠르고 확실한 방법")
    logger.info("")
    
    # 테스트 주소들 표시
    test_addresses = [
        "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo",  # 주소 2
        "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",  # 주소 3
        "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",  # 주소 4
    ]
    
    logger.info("📋 TRX가 필요한 테스트 주소들:")
    for i, addr in enumerate(test_addresses, 2):
        logger.info(f"   주소 {i}: {addr}")
    
    logger.info("")
    logger.info("💡 권장 방법: 방법 2 (첫 번째 주소를 임시 마스터로 사용)")
    logger.info("1. TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL 에 Faucet으로 200 TRX 받기")
    logger.info("2. python3 distribute_from_hd.py 실행")
    logger.info("3. python3 test_tron_transactions.py 로 다중 Sweep 테스트")

if __name__ == "__main__":
    asyncio.run(main())
