#!/usr/bin/env python3
"""
TRON 테스트넷 주소 잔액 확인 스크립트
"""

import asyncio
import logging
from tronpy import Tron

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TRON 테스트넷 설정 (공개 노드 사용)
async def check_balance(address: str) -> float:
    """특정 주소의 TRX 잔액을 확인합니다."""
    try:
        # 공개 테스트넷 노드 사용
        tron = Tron(network='nile')
        account = tron.get_account(address)
        
        if account:
            balance_sun = account.get('balance', 0)
            balance_trx = balance_sun / 1_000_000  # SUN to TRX
            return balance_trx
        else:
            logger.warning(f"Account not found on-chain: {address}")
            return 0.0
            
    except Exception as e:
        logger.error(f"Balance check failed for {address}: {e}")
        return 0.0

async def main():
    """메인 실행 함수"""
    # 생성된 테스트 주소들
    test_addresses = [
        "TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL",  # 사용자 12345
        "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo",  # 사용자 12346
        "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",  # 사용자 12347
        "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",  # 사용자 12348
    ]
    
    logger.info("=== TRON 테스트넷 잔액 확인 ===")
    logger.info("Faucet: https://nileex.io/")
    logger.info("")
    
    total_balance = 0.0
    funded_addresses = []
    
    for i, address in enumerate(test_addresses, 1):
        logger.info(f"{i}. {address} 잔액 확인 중...")
        balance = await check_balance(address)
        
        if balance > 0:
            logger.info(f"   ✅ 잔액: {balance:.6f} TRX")
            total_balance += balance
            funded_addresses.append((address, balance))
        else:
            logger.info(f"   ⚠️  잔액: 0 TRX (온체인에 없거나 빈 주소)")
        
        await asyncio.sleep(0.5)  # API 호출 간격
    
    logger.info("")
    logger.info(f"총 잔액: {total_balance:.6f} TRX")
    logger.info(f"TRX가 있는 주소: {len(funded_addresses)}개")
    
    if funded_addresses:
        logger.info("")
        logger.info("🎉 Sweep 테스트 준비 완료!")
        logger.info("다음 명령어로 Sweep 테스트를 실행하세요:")
        logger.info("python3 test_tron_transactions.py > sweep_test.log 2>&1")
    else:
        logger.info("")
        logger.info("💡 아직 TRX가 없습니다. Faucet에서 TRX를 받아주세요:")
        logger.info("https://nileex.io/")
        logger.info("")
        logger.info("권장 주소:")
        for i, addr in enumerate(test_addresses[:2], 1):
            logger.info(f"  {i}. {addr}")

if __name__ == "__main__":
    asyncio.run(main())
