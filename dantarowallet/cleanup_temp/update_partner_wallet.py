#!/usr/bin/env python3
"""
파트너 지갑을 TRX가 있는 마스터 지갑으로 업데이트
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def update_partner_wallet():
    """파트너 지갑을 TRX가 있는 마스터 지갑으로 업데이트"""
    print("🔄 파트너 지갑 주소 업데이트")
    
    # TRX가 있는 마스터 지갑 주소
    master_address = "TAjGrq1zVHq8dHQGBnpV8odW33H1QZZ22H"
    
    async for db in get_db():
        try:
            # 현재 파트너 지갑 확인
            current_result = await db.execute(text(
                "SELECT id, wallet_address FROM partner_wallets WHERE partner_id = 'test_partner_001'"
            ))
            current_wallet = current_result.fetchone()
            
            if current_wallet:
                print(f"📱 현재 파트너 지갑:")
                print(f"   ID: {current_wallet.id}")
                print(f"   주소: {current_wallet.wallet_address}")
                
                # 새 주소로 업데이트
                await db.execute(text(
                    "UPDATE partner_wallets SET wallet_address = :address WHERE partner_id = 'test_partner_001'"
                ), {"address": master_address})
                
                await db.commit()
                
                print(f"\n✅ 파트너 지갑 주소 업데이트 완료:")
                print(f"   새 주소: {master_address}")
                print(f"   TRX 잔고: 171.2 TRX")
                
                # 업데이트된 Sweep 설정 확인
                config_result = await db.execute(text(
                    """
                    SELECT sc.id, sc.min_sweep_amount, pw.wallet_address 
                    FROM sweep_configurations sc 
                    JOIN partner_wallets pw ON sc.destination_wallet_id = pw.id 
                    WHERE sc.partner_id = 'test_partner_001'
                    """
                ))
                config = config_result.fetchone()
                
                if config:
                    print(f"\n⚙️ 업데이트된 Sweep 설정:")
                    print(f"   설정 ID: {config.id}")
                    print(f"   목적지 주소: {config.wallet_address}")
                    print(f"   최소 Sweep 금액: {config.min_sweep_amount} TRX")
                    print(f"\n🎉 이제 Sweep이 171.2 TRX가 있는 지갑으로 전송됩니다!")
                
            else:
                print("❌ 파트너 지갑을 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(update_partner_wallet())
