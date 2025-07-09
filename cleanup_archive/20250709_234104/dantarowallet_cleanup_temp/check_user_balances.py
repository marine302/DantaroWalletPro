#!/usr/bin/env python3
"""
사용자 지갑들의 TRX 잔고 확인
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def check_user_wallets_balance():
    """사용자 지갑들의 TRX 잔고 확인"""
    print("🔍 사용자 지갑들의 TRX 잔고 확인")
    
    async for db in get_db():
        try:
            # 사용자 지갑 주소 조회
            result = await db.execute(text(
                "SELECT id, user_id, address FROM user_deposit_addresses WHERE is_active = 1 ORDER BY id"
            ))
            addresses = result.fetchall()
            
            print(f"\n📱 사용자 지갑 잔고 확인 ({len(addresses)} 개):")
            
            total_balance = 0
            wallets_with_balance = 0
            
            for addr in addresses:
                try:
                    # curl로 잔고 조회
                    import subprocess
                    cmd = f'curl -s "https://nile.trongrid.io/v1/accounts/{addr.address}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        import json
                        data = json.loads(result.stdout)
                        if data.get('data'):
                            balance_sun = data['data'][0].get('balance', 0)
                            balance_trx = balance_sun / 1_000_000
                            
                            print(f"  - ID: {addr.id}, 사용자: {addr.user_id}")
                            print(f"    주소: {addr.address}")
                            print(f"    잔고: {balance_trx:.6f} TRX")
                            
                            total_balance += balance_trx
                            if balance_trx > 0:
                                wallets_with_balance += 1
                        else:
                            print(f"  - ID: {addr.id}, 사용자: {addr.user_id}")
                            print(f"    주소: {addr.address}")
                            print(f"    잔고: 0.000000 TRX (계정 없음)")
                    
                except Exception as e:
                    print(f"    ❌ 잔고 조회 실패: {e}")
            
            print(f"\n💰 총 잔고 요약:")
            print(f"   총 지갑 수: {len(addresses)}")
            print(f"   TRX가 있는 지갑: {wallets_with_balance}")
            print(f"   총 TRX 잔고: {total_balance:.6f} TRX")
            
            if wallets_with_balance > 0:
                print(f"\n✅ Sweep 가능한 지갑이 {wallets_with_balance}개 있습니다!")
                return True
            else:
                print(f"\n❌ TRX가 있는 사용자 지갑이 없습니다.")
                return False
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_user_wallets_balance())
