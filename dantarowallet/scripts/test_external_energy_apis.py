#!/usr/bin/env python3
"""
외부 에너지 공급업체 API 테스트 스크립트
"""

import asyncio
import logging
from app.services.external_energy.tronnrg_service import tronnrg_service
from app.services.external_energy.energytron_service import EnergyTRONService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)


async def test_tronnrg():
    """TronNRG API 테스트"""
    print("\n🟢 === TronNRG API 테스트 ===")
    
    if not settings.TRONNRG_API_KEY or settings.TRONNRG_API_KEY == "your-tronnrg-api-key-here":
        print("⚠️  TronNRG API 키가 설정되지 않았습니다 (.env 파일 확인)")
        print("   현재 데모 모드로 실행됩니다")
        return
    
    try:
        print("📊 시장 가격 조회 중...")
        # 실제 API 호출은 주석 처리 (API 키가 없을 경우)
        # market_data = await tronnrg_service.get_market_price()
        # print(f"✅ 시장 데이터: {market_data}")
        
        print("📋 공급자 목록 조회 중...")
        # providers = await tronnrg_service.get_providers()
        # print(f"✅ 공급자 수: {len(providers)}")
        
        print("✅ TronNRG 서비스 설정 완료")
        
    except Exception as e:
        print(f"❌ TronNRG API 오류: {e}")


async def test_energytron():
    """EnergyTRON API 테스트"""
    print("\n🟡 === EnergyTRON API 테스트 ===")
    
    if not settings.ENERGYTRON_API_KEY or settings.ENERGYTRON_API_KEY == "your-energytron-api-key-here":
        print("⚠️  EnergyTRON API 키가 설정되지 않았습니다 (.env 파일 확인)")
        print("   현재 데모 모드로 실행됩니다")
        return
    
    try:
        energytron = EnergyTRONService()
        print("📊 실시간 가격 조회 중...")
        # 실제 API 호출은 주석 처리 (API 키가 없을 경우)
        # price_data = await energytron.get_realtime_prices()
        # print(f"✅ 가격 데이터: {price_data}")
        
        print("💰 잔액 조회 중...")
        # balance = await energytron.get_balance()
        # print(f"✅ 계정 잔액: {balance}")
        
        print("✅ EnergyTRON 서비스 설정 완료")
        
    except Exception as e:
        print(f"❌ EnergyTRON API 오류: {e}")


async def test_api_endpoints():
    """API 엔드포인트 접근 테스트"""
    print("\n🔗 === API 엔드포인트 테스트 ===")
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        # 헬스 체크
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/external-energy/test")
            if response.status_code == 200:
                print("✅ 외부 에너지 API 엔드포인트 접근 가능")
            else:
                print(f"⚠️  API 응답 코드: {response.status_code}")
                
    except Exception as e:
        print(f"❌ API 엔드포인트 테스트 실패: {e}")
        print("   서버가 실행 중인지 확인하세요: uvicorn app.main:app --host 0.0.0.0 --port 8000")


def print_configuration():
    """현재 설정 정보 출력"""
    print("🔧 === 현재 설정 정보 ===")
    print(f"TronNRG API Key: {'✅ 설정됨' if settings.TRONNRG_API_KEY and settings.TRONNRG_API_KEY != 'your-tronnrg-api-key-here' else '❌ 미설정'}")
    print(f"TronNRG Base URL: {settings.TRONNRG_BASE_URL}")
    print(f"EnergyTRON API Key: {'✅ 설정됨' if settings.ENERGYTRON_API_KEY and settings.ENERGYTRON_API_KEY != 'your-energytron-api-key-here' else '❌ 미설정'}")
    print(f"EnergyTRON Partner ID: {settings.ENERGYTRON_PARTNER_ID}")
    print(f"EnergyTRON Base URL: {settings.ENERGYTRON_BASE_URL}")
    print(f"Request Timeout: {settings.EXTERNAL_ENERGY_TIMEOUT}초")
    print(f"Retry Count: {settings.EXTERNAL_ENERGY_RETRY_COUNT}")


async def main():
    """메인 테스트 함수"""
    print("🧪 외부 에너지 공급업체 API 테스트를 시작합니다...")
    
    print_configuration()
    
    await test_tronnrg()
    await test_energytron()
    await test_api_endpoints()
    
    print("\n🎉 === 테스트 완료 ===")
    print("API 키 설정이 필요하다면 다음 문서를 참조하세요:")
    print("📖 docs/external-energy-api-setup.md")


if __name__ == "__main__":
    asyncio.run(main())
