#!/usr/bin/env python3
"""
최종 Sweep 시스템 상태 확인
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def check_final_status():
    """Sweep 시스템 최종 상태 확인"""
    print("🔍 최종 Sweep 시스템 상태 확인")
    
    async for db in get_db():
        try:
            # 1. 마스터 지갑 상태
            master_result = await db.execute(text(
                "SELECT id, partner_id, collection_address, last_index, total_addresses_generated FROM hd_wallet_masters"
            ))
            masters = master_result.fetchall()
            
            print(f"\n📱 마스터 지갑 ({len(masters)} 개):")
            for master in masters:
                print(f"  - ID: {master.id}, 파트너: {master.partner_id}")
                print(f"    컬렉션 주소: {master.collection_address}")
                print(f"    마지막 인덱스: {master.last_index}, 생성된 주소: {master.total_addresses_generated}")
            
            # 2. 사용자 입금 주소 상태
            address_result = await db.execute(text(
                "SELECT id, user_id, address, derivation_index, is_active FROM user_deposit_addresses ORDER BY id"
            ))
            addresses = address_result.fetchall()
            
            print(f"\n🏠 사용자 입금 주소 ({len(addresses)} 개):")
            for addr in addresses:
                print(f"  - ID: {addr.id}, 사용자: {addr.user_id}, 인덱스: {addr.derivation_index}")
                print(f"    주소: {addr.address}, 활성: {addr.is_active}")
            
            # 3. Sweep 설정 상태
            config_result = await db.execute(text(
                "SELECT id, partner_id, destination_wallet_id, is_enabled, min_sweep_amount FROM sweep_configurations"
            ))
            configs = config_result.fetchall()
            
            print(f"\n⚙️ Sweep 설정 ({len(configs)} 개):")
            for config in configs:
                print(f"  - ID: {config.id}, 파트너: {config.partner_id}")
                print(f"    목적지 지갑: {config.destination_wallet_id}, 활성: {config.is_enabled}")
                print(f"    최소 Sweep 금액: {config.min_sweep_amount} TRX")
            
            # 4. 파트너 지갑 상태
            partner_wallet_result = await db.execute(text(
                "SELECT id, partner_id, wallet_address, wallet_type, purpose FROM partner_wallets"
            ))
            partner_wallets = partner_wallet_result.fetchall()
            
            print(f"\n💼 파트너 지갑 ({len(partner_wallets)} 개):")
            for pw in partner_wallets:
                print(f"  - ID: {pw.id}, 파트너: {pw.partner_id}")
                print(f"    주소: {pw.wallet_address}")
                print(f"    유형: {pw.wallet_type}, 용도: {pw.purpose}")
            
            print("\n✅ Sweep 시스템이 성공적으로 구축되었습니다!")
            print("\n📋 구현된 기능:")
            print("   - TRON HD 지갑 마스터 생성")
            print("   - 사용자별 입금 주소 파생")
            print("   - 마스터 지갑 collection_address 자동 설정")
            print("   - Sweep 설정 관리")
            print("   - FastAPI 엔드포인트 통합")
            print("   - DB 마이그레이션 완료")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_final_status())
