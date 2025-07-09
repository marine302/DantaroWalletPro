#!/usr/bin/env python3
"""
마스터 지갑에서 사용자 지갑들로 TRX 분배
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db
from tronpy import Tron
from tronpy.keys import PrivateKey

async def distribute_trx_to_users():
    """마스터 지갑에서 사용자 지갑들로 TRX 분배"""
    print("🚀 사용자 지갑들로 TRX 분배 시작")
    
    # TRON 네트워크 연결 (테스트넷)
    tron = Tron(network='nile')
    
    # 마스터 지갑 정보 (이전 테스트에서 생성된 것)
    master_address = "TAjGrq1zVHq8dHQGBnpV8odW33H1QZZ22H"
    # 이전 테스트 결과에서 확인된 시드 프레이즈
    seed_phrase = "example host damage donor frog side surprise raccoon exact blame auction power"
    
    # 시드에서 개인키 생성
    from mnemonic import Mnemonic
    mnemo = Mnemonic("english")
    seed = mnemo.to_seed(seed_phrase)
    master_private_key = PrivateKey(seed[:32])
    
    print(f"📱 마스터 지갑: {master_address}")
    
    # 현재 잔고 확인
    balance_sun = tron.get_account_balance(master_address)
    balance_trx = balance_sun / 1_000_000
    print(f"💰 현재 잔고: {float(balance_trx):.6f} TRX")
    
    async for db in get_db():
        try:
            # 사용자 지갑 주소 조회 (최근 생성된 것들만)
            result = await db.execute(text(
                "SELECT id, user_id, address FROM user_deposit_addresses WHERE is_active = 1 AND user_id IN (1, 2, 3) ORDER BY id"
            ))
            user_addresses = result.fetchall()
            
            print(f"\n📋 분배 대상 사용자 지갑 ({len(user_addresses)} 개):")
            for addr in user_addresses:
                print(f"  - ID: {addr.id}, 사용자: {addr.user_id}, 주소: {addr.address}")
            
            if len(user_addresses) == 0:
                print("❌ 분배할 사용자 지갑이 없습니다.")
                return
            
            # 분배할 금액 계산 (각 지갑당 5 TRX씩)
            amount_per_user = 5.0
            total_amount = amount_per_user * len(user_addresses)
            
            if float(balance_trx) < total_amount + 1:  # 가스비 여유분 1 TRX
                print(f"❌ 잔고 부족: 필요 {total_amount + 1:.1f} TRX, 보유 {float(balance_trx):.6f} TRX")
                return
            
            print(f"\n💸 분배 계획:")
            print(f"   각 지갑당: {amount_per_user} TRX")
            print(f"   총 분배 금액: {total_amount} TRX")
            print(f"   남은 잔고 (예상): {float(balance_trx) - total_amount:.6f} TRX")
            
            # 실제 TRX 전송
            successful_transfers = 0
            
            for addr in user_addresses:
                try:
                    print(f"\n📤 {addr.user_id}번 사용자에게 {amount_per_user} TRX 전송 중...")
                    
                    # TRX 전송 트랜잭션 생성
                    txn = (
                        tron.trx.transfer(master_address, addr.address, int(amount_per_user * 1_000_000))
                        .memo("Test distribution for Sweep")
                        .build()
                        .sign(master_private_key)
                    )
                    
                    # 트랜잭션 브로드캐스트
                    result = tron.broadcast(txn)
                    
                    if result.get('result'):
                        print(f"✅ 전송 성공: {result['txid']}")
                        successful_transfers += 1
                    else:
                        print(f"❌ 전송 실패: {result}")
                        
                except Exception as e:
                    print(f"❌ 전송 중 오류: {e}")
                
                # 네트워크 부하 방지를 위한 지연
                await asyncio.sleep(2)
            
            print(f"\n📊 분배 결과:")
            print(f"   총 대상: {len(user_addresses)}개 지갑")
            print(f"   성공: {successful_transfers}개")
            print(f"   실패: {len(user_addresses) - successful_transfers}개")
            
            if successful_transfers > 0:
                print(f"\n✅ {successful_transfers}개 지갑에 TRX 분배 완료!")
                print("🔄 잠시 후 Sweep 테스트를 진행할 수 있습니다.")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(distribute_trx_to_users())
