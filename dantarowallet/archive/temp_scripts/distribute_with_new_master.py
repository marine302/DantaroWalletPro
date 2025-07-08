#!/usr/bin/env python3
"""
새로운 마스터 지갑에서 테스트 주소들로 TRX 분산 전송
"""

import asyncio
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """새로운 마스터 지갑에서 TRX 분산 전송"""
    
    logger.info("=== 새로운 마스터 지갑에서 TRX 분산 전송 ===")
    logger.info("")
    
    # 새로 생성한 마스터 지갑 정보
    master_address = "TWXpiL2jnPWAsCUQxUuqRnJxzopYybpMhg"
    master_private_key_hex = "915b575f73cd077b00c648248191a7c4405a919f2ca2f06076fdd271a0dc2953"
    
    # 테스트용 주소들
    target_addresses = [
        "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo",  # 주소 2
        "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",  # 주소 3
        "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",  # 주소 4
    ]
    
    send_amount_trx = 10  # 각 주소당 10 TRX
    send_amount_sun = int(send_amount_trx * 1_000_000)
    
    tron = Tron(network='nile')
    
    # 1. 마스터 지갑 잔액 확인
    logger.info(f"📋 마스터 지갑: {master_address}")
    try:
        account = tron.get_account(master_address)
        if account:
            balance_sun = account.get('balance', 0)
            balance_trx = balance_sun / 1_000_000
            logger.info(f"   💰 현재 잔액: {balance_trx:.6f} TRX")
            
            if balance_sun < (send_amount_sun * len(target_addresses) + 5_000_000):  # 수수료 여유분 5 TRX
                logger.error(f"   ❌ 잔액 부족. 필요: {(send_amount_trx * len(target_addresses)) + 5} TRX")
                logger.info("   🌐 Faucet에서 TRX를 더 받아주세요: https://nileex.io/")
                return
        else:
            logger.error("   ❌ 마스터 지갑을 찾을 수 없습니다. Faucet에서 TRX를 받아주세요.")
            return
    except Exception as e:
        logger.error(f"   ❌ 마스터 지갑 조회 실패: {e}")
        return
    
    logger.info("")
    logger.info(f"📤 {len(target_addresses)}개 주소로 각각 {send_amount_trx} TRX 전송 시작")
    logger.info("")
    
    # 2. 개인키 로드
    private_key = PrivateKey(bytes.fromhex(master_private_key_hex))
    
    # 3. 각 주소로 전송
    successful_transfers = 0
    for i, target_addr in enumerate(target_addresses, 1):
        logger.info(f"📤 전송 {i}/{len(target_addresses)}: {target_addr}")
        logger.info(f"   💸 금액: {send_amount_trx} TRX")
        
        try:
            # 트랜잭션 생성
            txn = (
                tron.trx.transfer(
                    master_address,
                    target_addr,
                    send_amount_sun
                )
                .memo(f"Multi-Sweep Test Distribution {i}")
                .build()
                .sign(private_key)
            )
            
            # 트랜잭션 전송
            result = tron.broadcast(txn)
            
            if result.get('result'):
                tx_id = result['txid']
                logger.info(f"   ✅ 전송 성공! TxID: {tx_id}")
                logger.info(f"   🔗 확인: https://nile.tronscan.org/#/transaction/{tx_id}")
                successful_transfers += 1
            else:
                logger.error(f"   ❌ 전송 실패: {result}")
                
        except Exception as e:
            logger.error(f"   ❌ 전송 실패: {e}")
        
        logger.info("")
        await asyncio.sleep(3)  # 트랜잭션 간격
    
    logger.info(f"🎉 분산 전송 완료: {successful_transfers}/{len(target_addresses)} 성공")
    logger.info("")
    
    if successful_transfers > 0:
        logger.info("⏰ 5분 후 잔액 확인 및 다중 Sweep 테스트를 진행하세요:")
        logger.info("python3 check_balance.py > final_multi_balance.log 2>&1 && cat final_multi_balance.log")
        logger.info("python3 test_tron_transactions.py > final_multi_sweep.log 2>&1 && cat final_multi_sweep.log")
    else:
        logger.info("⚠️  전송에 실패했습니다. 마스터 지갑 잔액을 확인하고 다시 시도하세요.")

if __name__ == "__main__":
    asyncio.run(main())
