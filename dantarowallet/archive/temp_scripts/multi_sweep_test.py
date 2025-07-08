#!/usr/bin/env python3
"""
TRX 분산 전송 및 다중 Sweep 테스트
"""

import asyncio
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey
import sys
import os

# 현재 디렉토리를 Python 패스에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.sweep.hd_wallet_service import HDWalletService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def distribute_trx_and_test():
    """TRX 분산 전송 및 다중 Sweep 테스트"""
    
    async for db in get_db():
        try:
            logger.info("=== TRX 분산 전송 및 Sweep 테스트 ===")
            
            # 서비스 초기화
            hd_wallet_service = HDWalletService(db)
            tron = Tron(network='nile')
            
            test_partner_id = "test_partner_001"
            
            # 1. 모든 주소 조회
            logger.info("\n1. 모든 주소 조회...")
            addresses = await hd_wallet_service.list_deposit_addresses(test_partner_id)
            
            if not addresses or len(addresses) < 2:
                logger.error("❌ 주소가 부족합니다. 최소 2개 이상 필요합니다.")
                return
            
            source_addr = addresses[0]  # 첫 번째 주소 (TRX가 있는 주소)
            target_addrs = addresses[1:4]  # 나머지 주소들
            
            logger.info(f"📍 소스 주소: {source_addr.address}")
            for i, addr in enumerate(target_addrs, 1):
                logger.info(f"📍 타겟 주소 {i}: {addr.address}")
            
            # 2. 소스 주소 잔액 확인
            logger.info(f"\n2. 소스 주소 잔액 확인...")
            account = tron.get_account(str(source_addr.address))
            if not account:
                logger.error("❌ 소스 주소에 TRX가 없습니다. 먼저 Faucet에서 TRX를 받으세요.")
                logger.info(f"🌐 Faucet: https://nileex.io/")
                logger.info(f"📍 주소: {source_addr.address}")
                return
            
            source_balance = account.get('balance', 0)
            source_trx = source_balance / 1_000_000
            logger.info(f"💰 소스 주소 잔액: {source_trx:.6f} TRX")
            
            if source_balance < 10_000_000:  # 10 TRX 미만
                logger.warning("⚠️ 소스 주소 잔액이 부족합니다. 최소 10 TRX 필요")
                logger.info("💡 추가 TRX를 받아주세요:")
                logger.info(f"🌐 Faucet: https://nileex.io/")
                logger.info(f"📍 주소: {source_addr.address}")
                return
            
            # 3. TRX 분산 전송
            logger.info(f"\n3. TRX 분산 전송...")
            
            # 소스 주소 개인키 조회
            private_key_hex = await hd_wallet_service.get_private_key(int(source_addr.id))
            private_key = PrivateKey(bytes.fromhex(private_key_hex))
            
            # 각 주소에 3 TRX씩 전송 (3,000,000 SUN)
            transfer_amount = 3_000_000  # 3 TRX
            successful_transfers = []
            
            for i, target_addr in enumerate(target_addrs, 1):
                try:
                    logger.info(f"   💸 주소 {i}로 3 TRX 전송 중... ({target_addr.address})")
                    
                    # 트랜잭션 생성 및 전송
                    txn = (
                        tron.trx.transfer(
                            str(source_addr.address),
                            str(target_addr.address),
                            transfer_amount
                        )
                        .memo(f"Test Distribution {i}")
                        .build()
                        .sign(private_key)
                    )
                    
                    result = tron.broadcast(txn)
                    
                    if result.get('result'):
                        tx_id = result['txid']
                        logger.info(f"   ✅ 전송 성공! TxID: {tx_id}")
                        successful_transfers.append((target_addr, tx_id))
                    else:
                        logger.error(f"   ❌ 전송 실패: {result}")
                    
                    await asyncio.sleep(2)  # 트랜잭션 간격
                    
                except Exception as e:
                    logger.error(f"   ❌ 주소 {i} 전송 실패: {e}")
            
            if not successful_transfers:
                logger.error("❌ 모든 전송이 실패했습니다.")
                return
            
            logger.info(f"\n✅ {len(successful_transfers)}개 주소로 전송 완료!")
            
            # 4. 잠시 대기 (블록 확인)
            logger.info("\n4. 블록 확인 대기 중... (30초)")
            await asyncio.sleep(30)
            
            # 5. 각 주소 잔액 확인 및 Sweep 테스트
            logger.info("\n5. 다중 주소 Sweep 테스트...")
            
            for target_addr, tx_id in successful_transfers:
                try:
                    # 잔액 확인
                    account = tron.get_account(target_addr.address)
                    if account:
                        balance_sun = account.get('balance', 0)
                        balance_trx = balance_sun / 1_000_000
                        logger.info(f"   💰 {target_addr.address}: {balance_trx:.6f} TRX")
                        
                        if balance_sun > 1_100_000:  # 1.1 TRX 이상
                            await test_individual_sweep(hd_wallet_service, tron, target_addr, balance_sun)
                        else:
                            logger.warning(f"   ⚠️ 잔액 부족 (최소 1.1 TRX 필요)")
                    else:
                        logger.warning(f"   ⚠️ 아직 온체인에 반영되지 않음")
                        
                except Exception as e:
                    logger.error(f"   ❌ 주소 처리 실패: {e}")
                
                await asyncio.sleep(1)
            
            logger.info("\n🎉 다중 주소 Sweep 테스트 완료!")
            
        except Exception as e:
            logger.error(f"❌ 테스트 실패: {e}")
            raise
        finally:
            await db.close()

async def test_individual_sweep(hd_wallet_service, tron, deposit_address, balance_sun):
    """개별 주소 Sweep 테스트"""
    
    logger.info(f"\n🔄 Sweep 시작: {deposit_address.address}")
    
    try:
        # 개인키 조회
        private_key_hex = await hd_wallet_service.get_private_key(deposit_address.id)
        private_key = PrivateKey(bytes.fromhex(private_key_hex))
        
        # 수수료 계산
        fee_amount = 1_100_000  # 1.1 TRX
        sweep_amount = balance_sun - fee_amount
        
        if sweep_amount <= 0:
            logger.warning(f"   ⚠️ 잔액 부족")
            return
        
        # 마스터 주소
        master_address = "TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp"
        
        logger.info(f"   💸 Sweep 금액: {sweep_amount/1_000_000:.6f} TRX")
        
        # 트랜잭션 생성 및 전송
        txn = (
            tron.trx.transfer(
                deposit_address.address,
                master_address,
                sweep_amount
            )
            .memo("Multi Sweep Test")
            .build()
            .sign(private_key)
        )
        
        result = tron.broadcast(txn)
        
        if result.get('result'):
            tx_id = result['txid']
            logger.info(f"   ✅ Sweep 성공! TxID: {tx_id}")
            logger.info(f"   🔗 확인: https://nile.tronscan.org/#/transaction/{tx_id}")
        else:
            logger.error(f"   ❌ Sweep 실패: {result}")
            
    except Exception as e:
        logger.error(f"   ❌ Sweep 오류: {e}")

if __name__ == "__main__":
    asyncio.run(distribute_trx_and_test())

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_trx_to_test_addresses():
    """테스트 주소들에 TRX를 분산해서 보냅니다."""
    
    logger.info("=== TRX 분산 전송 및 Sweep 테스트 ===")
    
    # TRON 테스트넷 연결
    tron = Tron(network='nile')
    
    # 테스트 주소들
    test_addresses = [
        "TZ8nMgTR7t8Wqk3tTHTbDtaMkifcZ46wWL",  # 사용자 12345 (이미 사용됨)
        "TTs6DdxvL783bsLsuhSyCyKG5Uf1CqDLUo",  # 사용자 12346
        "TMzgJo6wzZSXyuJhmxmJx9cTc84QyBHgWw",  # 사용자 12347
        "TKxaUXcsmsdteoB3bvzX8rW8Xbrkc8pJY4",  # 사용자 12348
    ]
    
    # 마스터 수집 주소 (Sweep 대상)
    master_address = "TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp"
    
    logger.info("1. 현재 잔액 확인...")
    for i, address in enumerate(test_addresses, 1):
        try:
            account = tron.get_account(address)
            if account:
                balance_sun = account.get('balance', 0)
                balance_trx = balance_sun / 1_000_000
                logger.info(f"   {i}. {address}: {balance_trx:.6f} TRX")
            else:
                logger.info(f"   {i}. {address}: 0 TRX (온체인에 없음)")
        except Exception as e:
            logger.error(f"   {i}. {address}: 잔액 조회 실패 ({e})")
    
    # 마스터 주소 잔액 확인
    try:
        master_account = tron.get_account(master_address)
        if master_account:
            master_balance_sun = master_account.get('balance', 0)
            master_balance_trx = master_balance_sun / 1_000_000
            logger.info(f"\n📦 마스터 주소 {master_address}: {master_balance_trx:.6f} TRX")
            
            if master_balance_trx > 10:  # 10 TRX 이상 있으면 분산 전송
                logger.info("\n2. TRX 분산 전송 시작...")
                logger.info("⚠️  주의: 실제 전송을 위해서는 마스터 주소의 개인키가 필요합니다.")
                logger.info("현재는 시뮬레이션만 진행합니다.")
                
                # 시뮬레이션: 각 주소에 5 TRX씩 전송 예정
                send_amount_trx = 5.0
                send_amount_sun = int(send_amount_trx * 1_000_000)
                
                for i, target_address in enumerate(test_addresses[1:3], 2):  # 2,3번째 주소에만
                    logger.info(f"   → {target_address}: {send_amount_trx} TRX 전송 예정")
                
            else:
                logger.info(f"\n💡 마스터 주소 잔액이 부족합니다. ({master_balance_trx:.6f} TRX)")
                logger.info("Faucet에서 직접 다른 주소들에 TRX를 받아주세요.")
        else:
            logger.info(f"\n📦 마스터 주소 {master_address}: 온체인에 없음")
    except Exception as e:
        logger.error(f"마스터 주소 잔액 조회 실패: {e}")
    
    logger.info("\n3. Faucet으로 추가 TRX 받기 안내:")
    logger.info("🌐 https://nileex.io/")
    logger.info("\n추가 테스트용 주소들:")
    for i, addr in enumerate(test_addresses[1:3], 2):
        logger.info(f"  {i}. {addr}")
    
    logger.info("\n4. TRX를 받은 후 Sweep 테스트:")
    logger.info("python3 test_tron_transactions.py > multi_sweep_test.log 2>&1 && cat multi_sweep_test.log")

if __name__ == "__main__":
    asyncio.run(send_trx_to_test_addresses())
