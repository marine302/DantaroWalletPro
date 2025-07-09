#!/usr/bin/env python3
"""
DB에 있는 파트너 지갑 확인
"""
import asyncio
import os
import sys
from sqlalchemy import text

from app.core.database import get_db
from app.models.partner_wallet import PartnerWallet, WalletType, WalletPurpose
from app.models.partner import Partner

async def check_partner_wallets():
    """파트너 지갑 확인"""
    print("🔍 파트너 지갑 확인")
    
    async for db in get_db():
        try:
            # 파트너 확인
            partner_result = await db.execute(text(
                "SELECT id, name FROM partners WHERE id = 'test_partner_001'"
            ))
            partner = partner_result.fetchone()
            
            if not partner:
                print("⚠️ 테스트 파트너가 없습니다. 생성합니다.")
                await db.execute(text(
                    "INSERT INTO partners (id, name) VALUES ('test_partner_001', 'Test Partner')"
                ))
                await db.commit()
                print("✅ 테스트 파트너 생성 완료")
            else:
                print(f"✅ 테스트 파트너 확인: {partner.id} - {partner.name}")
                
            # 파트너 지갑 확인 및 강제 재생성
            print("⚠️ 기존 파트너 지갑 삭제")
            await db.execute(text(
                "DELETE FROM partner_wallets WHERE partner_id = 'test_partner_001'"
            ))
            await db.commit()
            print("✅ 기존 지갑 삭제 완료")
            
            wallet_result = await db.execute(text(
                "SELECT id, wallet_address, wallet_type, purpose FROM partner_wallets WHERE partner_id = 'test_partner_001'"
            ))
            wallets = wallet_result.fetchall()
            
            # 항상 생성
            print("⚠️ 파트너 지갑이 없습니다. 생성합니다.")
            # 테스트용 지갑 생성
            await db.execute(text(
                """
                INSERT INTO partner_wallets 
                (partner_id, wallet_type, wallet_address, wallet_name, purpose) 
                VALUES 
                ('test_partner_001', 'INTERNAL', 'TYourTestWalletAddressForSweepDestination123', 'Test Sweep Destination', 'SWEEP_DESTINATION')
                """
            ))
            await db.commit()
            print("✅ 테스트 파트너 지갑 생성 완료")
            
            # 생성된 지갑 정보 확인
            wallet_result = await db.execute(text(
                "SELECT id, wallet_address, wallet_type, purpose FROM partner_wallets WHERE partner_id = 'test_partner_001'"
            ))
            wallets = wallet_result.fetchall()
                
            print(f"🔍 파트너 지갑 목록 ({len(wallets)} 개):")
            for wallet in wallets:
                print(f"  - ID: {wallet.id}, 주소: {wallet.wallet_address}, 유형: {wallet.wallet_type}, 용도: {wallet.purpose}")
            
            if wallets:
                print(f"✅ Sweep 테스트에 사용할 지갑 ID: {wallets[0].id}")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_partner_wallets())
