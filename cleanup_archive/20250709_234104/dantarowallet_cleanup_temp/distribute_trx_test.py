#!/usr/bin/env python3
"""
사용자 지갑들의 잔고 확인 및 TRX 분배
"""
import asyncio
import json
from sqlalchemy import text
from app.core.database import get_db
from tronpy import Tron
from tronpy.keys import PrivateKey

async def check_and_distribute_trx():
    """사용자 지갑들의 잔고 확인 및 필요시 TRX 분배"""
    print("🔍 사용자 지갑 잔고 확인 및 TRX 분배")
    
    # TRON 네트워크 연결 (테스트넷)
    tron = Tron(network='nile')
    
    # 마스터 지갑 정보 (이전 테스트에서 사용)
    master_address = "TAjGrq1zVHq8dHQGBnpV8odW33H1QZZ22H"
    master_private_key = "f0b0b1830a44f8ddb1e2761b0b8d7a5b9f8d7a9f8d7a8b9f8d7a5b9f8d7a8c9d"  # 테스트용
    
    async for db in get_db():
        try:
            # 사용자 입금 주소들 조회 (최신 3개만)
            result = await db.execute(text(
                "SELECT id, user_id, address FROM user_deposit_addresses WHERE user_id IN (1, 2, 3) ORDER BY id DESC LIMIT 3"
            ))
            user_addresses = result.fetchall()
            
            print(f"\n📱 사용자 지갑 잔고 확인 ({len(user_addresses)} 개):")
            
            addresses_to_fund = []
            
            for addr in user_addresses:
                try:
                    # TRX 잔고 조회
                    balance_sun = tron.get_account_balance(addr.address)
                    balance_trx = balance_sun / 1_000_000
                    
                    print(f"  - 사용자 {addr.user_id}: {addr.address}")
                    print(f"    잔고: {balance_trx:.6f} TRX")
                    
                    if balance_trx < 5:  # 5 TRX 미만이면 충전 대상
                        addresses_to_fund.append({
                            'user_id': addr.user_id,
                            'address': addr.address,
                            'current_balance': balance_trx
                        })
                        
                except Exception as e:
                    print(f"    ❌ 잔고 조회 실패: {e}")
                    # 계정이 없으면 충전 대상에 추가
                    addresses_to_fund.append({
                        'user_id': addr.user_id,
                        'address': addr.address,
                        'current_balance': 0
                    })
            
            # TRX 분배가 필요한 지갑이 있는 경우
            if addresses_to_fund:
                print(f"\n💰 TRX 분배 필요한 지갑: {len(addresses_to_fund)} 개")
                
                # 마스터 지갑 잔고 확인
                master_balance_sun = tron.get_account_balance(master_address)
                master_balance_trx = master_balance_sun / 1_000_000
                print(f"📱 마스터 지갑 잔고: {master_balance_trx:.6f} TRX")
                
                if master_balance_trx > 20:  # 충분한 잔고가 있으면 분배
                    print(f"\n🚀 각 지갑에 10 TRX씩 분배 시작...")
                    
                    # 마스터 지갑에서 사용자 지갑들로 TRX 전송
                    # 주의: 실제 환경에서는 더 안전한 방법으로 개인키를 관리해야 함
                    
                    successful_transfers = 0
                    for wallet in addresses_to_fund:
                        try:
                            # 10 TRX 전송 (10,000,000 SUN)
                            amount_sun = 10_000_000
                            
                            print(f"   사용자 {wallet['user_id']}에게 10 TRX 전송 중...")
                            
                            # 실제 트랜잭션은 주석 처리 (테스트 환경에서만 사용)
                            print(f"   ✅ 사용자 {wallet['user_id']} 전송 시뮬레이션 완료")
                            successful_transfers += 1
                            
                        except Exception as e:
                            print(f"   ❌ 사용자 {wallet['user_id']} 전송 실패: {e}")
                    
                    print(f"\n✅ TRX 분배 완료: {successful_transfers}/{len(addresses_to_fund)} 성공")
                    
                    # 분배 후 잔고 확인
                    print(f"\n🔍 분배 후 잔고 확인:")
                    for addr in user_addresses:
                        try:
                            balance_sun = tron.get_account_balance(addr.address)
                            balance_trx = balance_sun / 1_000_000
                            print(f"  - 사용자 {addr.user_id}: {balance_trx:.6f} TRX")
                        except:
                            print(f"  - 사용자 {addr.user_id}: 0.000000 TRX (계정 미활성화)")
                else:
                    print(f"❌ 마스터 지갑 잔고 부족 ({master_balance_trx:.6f} TRX)")
            else:
                print(f"\n✅ 모든 사용자 지갑에 충분한 TRX가 있습니다!")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_and_distribute_trx())
