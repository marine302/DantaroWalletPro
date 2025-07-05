"""
기본 Energy Pool 설정 스크립트
"""
import asyncio
import os
import sys
from decimal import Decimal

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.energy_pool import EnergyPool
from app.services.energy_pool_service import EnergyPoolService
from sqlalchemy import update


async def setup_default_energy_pool():
    """기본 에너지 풀 설정"""
    print("🔋 기본 Energy Pool 설정 시작...")

    async with AsyncSessionLocal() as db:
        energy_service = EnergyPoolService(db)

        # 기존 풀 확인
        existing_pool = await energy_service.get_default_energy_pool()
        if existing_pool:
            print(f"✅ 기본 Energy Pool이 이미 존재합니다.")
            print(f"   - Pool ID: {existing_pool.id}")
            print(f"   - Wallet: {existing_pool.wallet_address}")
            return

        # 새 풀 생성 (테스트용 주소)
        test_wallet_address = "TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy"  # 테스트 주소

        try:
            new_pool = await energy_service.create_default_energy_pool(
                test_wallet_address
            )
            pool_id = new_pool.id
            print(f"✅ 기본 Energy Pool 생성 완료! (ID: {pool_id})")

            # 테스트용 에너지 값 업데이트 (SQL Update 사용)
            await db.execute(
                update(EnergyPool)
                .where(EnergyPool.id == pool_id)
                .values(
                    total_frozen_trx=Decimal("1000"),
                    frozen_for_energy=Decimal("800"),
                    frozen_for_bandwidth=Decimal("200"),
                    available_energy=1000000,  # 100만 에너지
                    available_bandwidth=50000,  # 5만 대역폭
                )
            )
            await db.commit()

            print(f"   - Wallet: {new_pool.wallet_address}")
            print(f"   - 총 Freeze TRX: 1,000")
            print(f"   - 사용 가능한 에너지: 1,000,000")
            print(f"   - 사용 가능한 대역폭: 50,000")

            # 테스트용 가격 정보 추가
            await energy_service.record_energy_price(
                trx_price_usd=Decimal("0.12"),  # TRX 가격 $0.12
                energy_per_trx=1000,  # TRX당 1000 에너지
                bandwidth_per_trx=250,  # TRX당 250 대역폭
                source="Initial Setup",
            )
            print("✅ 초기 가격 정보 기록 완료")

            # 테스트용 사용 로그 몇 개 추가
            for i in range(5):
                await energy_service.log_energy_usage(
                    energy_pool_id=pool_id,
                    transaction_hash=f"TEST_TX_{i+1:03d}",
                    transaction_type="USDT_TRANSFER",
                    energy_consumed=13000,  # USDT 전송 표준 에너지
                    bandwidth_consumed=268,  # 표준 대역폭
                    from_address="TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy",
                    to_address=f"TTest{i+1}Address12345678901234567890",
                    amount=Decimal("100"),
                    asset="USDT",
                )

            print("✅ 테스트용 사용 로그 5개 생성 완료")
            print("\n🎉 Energy Pool 설정이 완료되었습니다!")
            print("   관리자 대시보드에서 /admin/energy 페이지를 확인하세요.")

        except Exception as e:
            print(f"❌ Energy Pool 생성 중 오류: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(setup_default_energy_pool())
