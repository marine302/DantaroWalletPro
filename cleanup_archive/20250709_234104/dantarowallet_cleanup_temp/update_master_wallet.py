#!/usr/bin/env python3
"""
기존 마스터 지갑들의 잔고 확인 및 업데이트
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db
from tronpy import Tron

async def check_master_wallets_balance():
    """기존 마스터 지갑들의 TRX 잔고 확인"""
    print("🔍 기존 마스터 지갑들의 TRX 잔고 확인")
    
    # TRON 네트워크 연결 (테스트넷)
    tron = Tron(network='nile')
    
    async for db in get_db():
        try:
            # 모든 마스터 지갑 조회
            result = await db.execute(text(
                "SELECT id, partner_id, collection_address FROM hd_wallet_masters"
            ))
            masters = result.fetchall()
            
            print(f"\n📱 마스터 지갑 잔고 확인 ({len(masters)} 개):")
            
            wallets_with_balance = []
            
            for master in masters:
                if master.collection_address:
                    try:
                        # TRX 잔고 조회
                        balance = tron.get_account_balance(master.collection_address)
                        balance_trx = balance / 1_000_000  # SUN을 TRX로 변환
                        
                        print(f"  - ID: {master.id}, 파트너: {master.partner_id}")
                        print(f"    주소: {master.collection_address}")
                        print(f"    TRX 잔고: {balance_trx:.6f} TRX")
                        
                        if balance_trx > 0:
                            wallets_with_balance.append({
                                'id': master.id,
                                'partner_id': master.partner_id,
                                'address': master.collection_address,
                                'balance': balance_trx
                            })
                            
                    except Exception as e:
                        print(f"    ❌ 잔고 조회 실패: {e}")
                else:
                    print(f"  - ID: {master.id}, 파트너: {master.partner_id}")
                    print(f"    ❌ collection_address가 없음")
            
            print(f"\n💰 TRX 잔고가 있는 지갑 ({len(wallets_with_balance)} 개):")
            for wallet in wallets_with_balance:
                print(f"  - ID: {wallet['id']}, 잔고: {wallet['balance']:.6f} TRX")
                print(f"    주소: {wallet['address']}")
            
            # 가장 많은 잔고를 가진 지갑 선택
            if wallets_with_balance:
                best_wallet = max(wallets_with_balance, key=lambda x: x['balance'])
                print(f"\n🏆 선택된 지갑: ID {best_wallet['id']} (잔고: {best_wallet['balance']:.6f} TRX)")
                
                # 파트너 지갑 테이블에서 해당 주소로 업데이트
                await db.execute(text(
                    "UPDATE partner_wallets SET wallet_address = :address WHERE partner_id = 'test_partner_001'"
                ), {"address": best_wallet['address']})
                
                await db.commit()
                print(f"✅ 파트너 지갑 주소를 {best_wallet['address']}로 업데이트 완료")
                
                # 현재 설정 확인
                config_result = await db.execute(text(
                    "SELECT pw.wallet_address, sc.min_sweep_amount FROM sweep_configurations sc "
                    "JOIN partner_wallets pw ON sc.destination_wallet_id = pw.id "
                    "WHERE sc.partner_id = 'test_partner_001'"
                ))
                config = config_result.fetchone()
                
                if config:
                    print(f"\n⚙️ 현재 Sweep 설정:")
                    print(f"   목적지 주소: {config.wallet_address}")
                    print(f"   최소 Sweep 금액: {config.min_sweep_amount} TRX")
                    
                return best_wallet
            else:
                print("\n❌ TRX 잔고가 있는 마스터 지갑을 찾을 수 없습니다.")
                return None
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_master_wallets_balance())
