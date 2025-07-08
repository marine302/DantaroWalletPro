#!/usr/bin/env python3
"""
HD 지갑에서 다른 주소들로 TRX 분산 전송
"""

import asyncio
import logging
from typing import List
from tronpy import Tron
from tronpy.keys import PrivateKey

from app.core.database import get_db
from app.services.sweep.hd_wallet_service import HDWalletService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def distribute_trx_from_source():
    """첫 번째 주소에서 나머지 주소들로 TRX 분산 전송"""
    
    async for db in get_db():
        try:
            logger.info("=== HD 지갑 TRX 분산 전송 ===")
            logger.info("")
            
            # 서비스 초기화
            hd_wallet_service = HDWalletService(db)
            tron = Tron(network='nile')
            
            # 테스트 파트너 ID
            test_partner_id = "test_partner_001"
            
            # 1. 모든 주소 조회
            addresses = await hd_wallet_service.list_deposit_addresses(test_partner_id)
            if not addresses or len(addresses) < 2:
                logger.error("❌ 충분한 주소가 없습니다.")
                return
            
            # 2. 첫 번째 주소를 소스로 사용 (가장 많은 TRX가 있을 것으로 예상)
            source_address = None
            source_balance = 0
            source_address_id = None
            
            logger.info("📋 각 주소 잔액 확인:")
            for addr in addresses:
                try:
                    account = tron.get_account(str(addr.address))
                    if account:
                        balance_sun = account.get('balance', 0)
                        balance_trx = balance_sun / 1_000_000
                        logger.info(f"   {addr.address}: {balance_trx:.6f} TRX (사용자: {addr.user_id})")
                        
                        # 가장 잔액이 많은 주소를 소스로 선택
                        if balance_sun > source_balance:
                            source_balance = balance_sun
                            source_address = addr
                            source_address_id = getattr(addr, 'id')  # SQLAlchemy 객체에서 값 추출
                    else:
                        logger.info(f"   {addr.address}: 0 TRX (사용자: {addr.user_id})")
                        
                except Exception as e:
                    logger.warning(f"   {addr.address}: 조회 실패 ({e})")
            
            if not source_address or source_balance < 10_000_000:  # 10 TRX 미만
                logger.error("❌ 전송할 충분한 TRX가 있는 주소가 없습니다. (최소 10 TRX 필요)")
                return
            
            logger.info("")
            logger.info(f"📤 소스 주소: {source_address.address}")
            logger.info(f"💰 소스 잔액: {source_balance/1_000_000:.6f} TRX")
            
            # 3. 나머지 주소들에 TRX 전송
            target_addresses = [addr for addr in addresses if getattr(addr, 'id') != source_address_id]
            send_amount_trx = 2  # 각 주소당 2 TRX (적은 양으로 테스트)
            send_amount_sun = int(send_amount_trx * 1_000_000)
            
            logger.info("")
            logger.info(f"📋 {len(target_addresses)}개 주소로 각각 {send_amount_trx} TRX 전송 예정")
            
            # 소스 주소의 개인키 조회
            logger.info("🔐 소스 주소 개인키 조회 중...")
            if source_address_id is None:
                logger.error("❌ 소스 주소 ID를 찾을 수 없습니다.")
                return
            private_key_hex = await hd_wallet_service.get_private_key(int(source_address_id))
            private_key = PrivateKey(bytes.fromhex(private_key_hex))
            
            logger.info("✅ 개인키 조회 성공")
            logger.info("")
            
            # 4. 각 주소로 전송
            successful_transfers = 0
            for i, target_addr in enumerate(target_addresses, 1):
                logger.info(f"📤 전송 {i}/{len(target_addresses)}: {target_addr.address}")
                logger.info(f"   💸 금액: {send_amount_trx} TRX")
                
                try:
                    # 트랜잭션 생성
                    txn = (
                        tron.trx.transfer(
                            str(source_address.address),
                            str(target_addr.address),
                            send_amount_sun
                        )
                        .memo(f"Distribution Test {i}")
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
                await asyncio.sleep(2)  # 트랜잭션 간격
            
            logger.info(f"🎉 전송 완료: {successful_transfers}/{len(target_addresses)} 성공")
            logger.info("")
            logger.info("⏰ 3분 후 잔액 확인 및 Sweep 테스트를 진행하세요:")
            logger.info("python3 check_balance.py > final_balance.log 2>&1 && cat final_balance.log")
            logger.info("python3 test_tron_transactions.py > multi_sweep_final.log 2>&1 && cat multi_sweep_final.log")
            
        except Exception as e:
            logger.error(f"❌ 분산 전송 실패: {e}")
            raise
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(distribute_trx_from_source())
