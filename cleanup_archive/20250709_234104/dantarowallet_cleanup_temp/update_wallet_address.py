#!/usr/bin/env python3
"""
기존 TRX가 있는 마스터 지갑으로 설정 변경
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def update_to_funded_wallet():
    """TRX가 있는 기존 마스터 지갑으로 설정 변경"""
    
    # 이전 테스트에서 TRX가 있던 마스터 지갑 주소
    funded_address = "TAjGrq1zVHq8dHQGBnpV8odW33H1QZZ22H"
    
    print(f"🔄 파트너 지갑을 TRX가 있는 주소로 변경: {funded_address}")
    
    async for db in get_db():
        try:
            # 파트너 지갑 주소 업데이트
            await db.execute(text(
                "UPDATE partner_wallets SET wallet_address = :address WHERE partner_id = 'test_partner_001'"
            ), {"address": funded_address})
            
            await db.commit()
            print(f"✅ 파트너 지갑 주소 업데이트 완료")
            
            # 현재 설정 확인
            config_result = await db.execute(text(
                "SELECT pw.wallet_address, sc.min_sweep_amount, sc.is_enabled FROM sweep_configurations sc "
                "JOIN partner_wallets pw ON sc.destination_wallet_id = pw.id "
                "WHERE sc.partner_id = 'test_partner_001'"
            ))
            config = config_result.fetchone()
            
            if config:
                print(f"\n⚙️ 업데이트된 Sweep 설정:")
                print(f"   목적지 주소: {config.wallet_address}")
                print(f"   최소 Sweep 금액: {config.min_sweep_amount} TRX")
                print(f"   활성화 상태: {config.is_enabled}")
                print(f"\n💡 이 주소는 이전 테스트에서 TRX 분배에 사용된 주소입니다.")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(update_to_funded_wallet())
