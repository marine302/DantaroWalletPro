#!/usr/bin/env python3
"""
TRON 테스트넷 실제 트랜잭션 테스트
생성된 주소들로 실제 TRX 송금 및 Sweep 테스트
"""
import asyncio
import sys
import os
from decimal import Decimal

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.sweep.hd_wallet_service import HDWalletService
from app.services.sweep.sweep_service import SweepService
from app.models.partner import Partner
from tronpy import Tron
from tronpy.keys import PrivateKey
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tron_transactions():
    """실제 TRON 테스트넷 트랜잭션 테스트"""
    
    async for db in get_db():
        try:
            logger.info("=== TRON 테스트넷 트랜잭션 테스트 시작 ===")
            
            # 서비스 초기화
            hd_wallet_service = HDWalletService(db)
            sweep_service = SweepService(db)
            tron = Tron(network='nile')  # 테스트넷
            
            # 테스트 파트너 ID
            test_partner_id = "test_partner_001"
            
            # 1. 생성된 주소 목록 조회
            logger.info("\n1. 생성된 주소 목록 조회...")
            addresses = await hd_wallet_service.list_deposit_addresses(test_partner_id)
            
            if not addresses:
                logger.error("❌ 생성된 주소가 없습니다. 먼저 test_tron_integration.py를 실행하세요.")
                return
            
            logger.info(f"✅ 총 {len(addresses)}개 주소 발견:")
            for addr in addresses:
                logger.info(f"   - {addr.address} (사용자: {addr.user_id})")
            
            # 2. 각 주소의 잔액 조회
            logger.info("\n2. 주소별 TRX 잔액 조회...")
            for addr in addresses:
                try:
                    # check_balance.py와 동일한 방식 사용
                    account = tron.get_account(str(addr.address))
                    if account:
                        balance_sun = account.get('balance', 0)
                        balance_trx = balance_sun / 1_000_000  # SUN to TRX
                        logger.info(f"   - {addr.address}: {balance_trx:.6f} TRX")
                        
                        if balance_sun > 0:
                            logger.info(f"     💰 잔액 발견! {balance_trx:.6f} TRX")
                            
                            # 3. 실제 Sweep 테스트 (잔액이 있는 경우)
                            await test_sweep_transaction(
                                hd_wallet_service, 
                                sweep_service, 
                                tron, 
                                addr, 
                                int(balance_sun)  # SUN 단위로 전달
                            )
                    else:
                        logger.warning(f"   - {addr.address}: 잔액 조회 실패 (account not found on-chain)")
                    
                except Exception as e:
                    logger.warning(f"   - {addr.address}: 잔액 조회 실패 ({e})")
            
            # 4. 테스트넷 TRX 받기 안내
            logger.info("\n4. 테스트넷 TRX 받기 안내...")
            logger.info("📋 테스트를 위해 다음 주소들에 TRX를 받으세요:")
            logger.info("🌐 TRON Nile 테스트넷 Faucet: https://nileex.io/")
            logger.info("")
            
            for i, addr in enumerate(addresses[:2], 1):  # 처음 2개 주소만 표시
                logger.info(f"  {i}. {addr.address}")
            
            logger.info("\n💡 TRX를 받은 후 이 스크립트를 다시 실행하면 실제 Sweep 테스트가 진행됩니다.")
            
        except Exception as e:
            logger.error(f"❌ 트랜잭션 테스트 실패: {e}")
            raise
        finally:
            await db.close()


async def test_sweep_transaction(
    hd_wallet_service: HDWalletService,
    sweep_service: SweepService,
    tron: Tron,
    deposit_address,
    balance: int
):
    """실제 Sweep 트랜잭션 테스트"""
    
    logger.info(f"\n🔄 Sweep 테스트 시작: {deposit_address.address}")
    
    try:
        # 개인키 조회
        private_key_hex = await hd_wallet_service.get_private_key(deposit_address.id)
        private_key = PrivateKey(bytes.fromhex(private_key_hex))
        
        # 수수료 계산 (1 TRX = 1,000,000 sun)
        fee_amount = 1_100_000  # 1.1 TRX (수수료 여유분 포함)
        sweep_amount = balance - fee_amount
        
        if sweep_amount <= 0:
            logger.warning(f"   ⚠️ 잔액이 부족합니다. 최소 {fee_amount/1_000_000:.1f} TRX 필요")
            return
        
        # 마스터 지갑 주소 (임시로 첫 번째 주소 사용)
        # 실제 환경에서는 파트너별 마스터 수집 주소를 사용해야 함
        master_address = "TGzz8gjYiYRqpfmDwnLxfgPuLVNmpCswVp"  # 테스트용 주소
        
        logger.info(f"   💸 Sweep 금액: {sweep_amount/1_000_000:.6f} TRX")
        logger.info(f"   📍 수집 주소: {master_address}")
        
        # 트랜잭션 생성 및 전송
        txn = (
            tron.trx.transfer(
                deposit_address.address,
                master_address,
                sweep_amount
            )
            .memo("Auto Sweep Test")
            .build()
            .sign(private_key)
        )
        
        # 트랜잭션 전송
        result = tron.broadcast(txn)
        
        if result.get('result'):
            tx_id = result['txid']
            logger.info(f"   ✅ Sweep 성공! TxID: {tx_id}")
            logger.info(f"   🔗 트랜잭션 확인: https://nile.tronscan.org/#/transaction/{tx_id}")
            
            # DB 업데이트 (Sweep 기록)
            await update_sweep_record(deposit_address, sweep_amount, tx_id)
            
        else:
            logger.error(f"   ❌ Sweep 실패: {result}")
            
    except Exception as e:
        logger.error(f"   ❌ Sweep 오류: {e}")


async def update_sweep_record(deposit_address, amount: int, tx_id: str):
    """Sweep 기록 업데이트"""
    try:
        # 실제 환경에서는 SweepLog 테이블에 기록
        # 현재는 로그만 출력
        logger.info(f"   📝 Sweep 기록 저장: {amount/1_000_000:.6f} TRX, TxID: {tx_id}")
    except Exception as e:
        logger.error(f"   ❌ Sweep 기록 저장 실패: {e}")


def main():
    """메인 함수"""
    try:
        asyncio.run(test_tron_transactions())
    except KeyboardInterrupt:
        logger.info("\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"❌ 실행 중 오류: {e}")


if __name__ == "__main__":
    main()
