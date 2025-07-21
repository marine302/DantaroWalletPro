"""
외부 에너지 공급자 초기 데이터 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.energy_provider import EnergyProvider, ProviderStatus
from app.models.energy_price import EnergyPrice
from decimal import Decimal
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_providers():
    """초기 공급자 데이터 생성"""
    async with AsyncSessionLocal() as session:
        try:
            # TronNRG 공급자 생성
            tronnrg_provider = EnergyProvider(
                id="tronnrg-1",
                name="TronNRG Pool A",
                api_endpoint="https://api.tronnrg.com/v1",
                api_key_encrypted="encrypted_api_key_placeholder",
                status=ProviderStatus.ONLINE,
                reliability_score=Decimal("99.2"),
                response_time_avg=Decimal("1.8"),
                min_order_size=1000,
                max_order_size=10000000,
                trading_fee=Decimal("0.001"),
                withdrawal_fee=Decimal("0.0005")
            )
            
            # 가격 정보 추가
            tronnrg_price = EnergyPrice(
                provider_id="tronnrg-1",
                price=Decimal("0.0041"),
                currency="TRX",
                available_energy=5000000,
                volume_24h=850000,
                change_24h=Decimal("-2.3")
            )
            
            # 두 번째 테스트 공급자
            test_provider = EnergyProvider(
                id="test-pool-1",
                name="Test Energy Pool",
                api_endpoint="https://api.test-energy.com/v1",
                api_key_encrypted="test_encrypted_key",
                status=ProviderStatus.ONLINE,
                reliability_score=Decimal("95.5"),
                response_time_avg=Decimal("2.1"),
                min_order_size=500,
                max_order_size=5000000,
                trading_fee=Decimal("0.002"),
                withdrawal_fee=Decimal("0.001")
            )
            
            test_price = EnergyPrice(
                provider_id="test-pool-1",
                price=Decimal("0.0045"),
                currency="TRX",
                available_energy=3000000,
                volume_24h=420000,
                change_24h=Decimal("1.2")
            )
            
            # 데이터베이스에 추가
            session.add_all([tronnrg_provider, test_provider, tronnrg_price, test_price])
            await session.commit()
            
            logger.info("초기 공급자 데이터가 성공적으로 생성되었습니다.")
            logger.info(f"생성된 공급자: {tronnrg_provider.name}, {test_provider.name}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"초기 데이터 생성 중 오류 발생: {e}")
            raise


async def main():
    """메인 실행 함수"""
    logger.info("외부 에너지 공급자 초기 데이터 생성을 시작합니다...")
    await create_initial_providers()
    logger.info("초기 데이터 생성이 완료되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
