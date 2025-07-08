#!/usr/bin/env python3
"""
TRON 지갑 트랜잭션 내역 조회
"""

import asyncio
import logging
from datetime import datetime
from tronpy import Tron

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """TRON 지갑 트랜잭션 내역 조회"""
    
    logger.info("=== TRON 지갑 트랜잭션 내역 조회 ===")
    logger.info("")
    
    # 테스트 주소들
    addresses = {
        "주소 1 (사용자 12345)": "TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL",
        "주소 2 (사용자 12346)": "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo", 
        "주소 3 (사용자 12347)": "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",
        "주소 4 (사용자 12348)": "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",
        "마스터 수집 주소": "TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp"
    }
    
    tron = Tron(network='nile')
    
    for name, address in addresses.items():
        logger.info(f"📋 {name}: {address}")
        
        try:
            # 현재 잔액 조회
            account = tron.get_account(address)
            if account:
                balance_sun = account.get('balance', 0)
                balance_trx = balance_sun / 1_000_000
                logger.info(f"   💰 현재 잔액: {balance_trx:.6f} TRX")
                
                # 트랜잭션 히스토리는 API 제한으로 생략
                # 대신 기록된 정보로 표시
                if address == "TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL":
                    logger.info("   📊 알려진 트랜잭션:")
                    logger.info("     1. Faucet에서 2000 TRX 수신")
                    logger.info("     2. 마스터 주소로 1998.9 TRX Sweep 전송")
                    
            else:
                logger.info("   💰 잔액: 0 TRX (온체인에 없음)")
                logger.info("   📊 트랜잭션 내역 없음")
                
        except Exception as e:
            logger.error(f"   ❌ 조회 실패: {e}")
            
        logger.info("")
        await asyncio.sleep(0.5)  # API 호출 간격
    
    # 로그에서 기록된 Sweep 트랜잭션 정보
    logger.info("📋 기록된 Sweep 트랜잭션:")
    logger.info("   ✅ TxID: 538aae60c25690dc7e35a69732c98a6a89fbd966c94470b2d9ea81da47f843c7")
    logger.info("   💸 금액: 1998.900000 TRX")
    logger.info("   📍 송신: TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL")
    logger.info("   📍 수신: TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp")
    logger.info("   🔗 확인: https://nile.tronscan.org/#/transaction/538aae60c25690dc7e35a69732c98a6a89fbd966c94470b2d9ea81da47f843c7")

if __name__ == "__main__":
    asyncio.run(main())
