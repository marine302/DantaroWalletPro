#!/usr/bin/env python3
"""
WebSocket 연결 테스트 스크립트
"""
import asyncio
import websockets
import json

async def test_energy_prices_websocket():
    """에너지 가격 WebSocket 테스트"""
    uri = "ws://localhost:8001/api/v1/ws/energy/prices"
    
    try:
        print("🔌 에너지 가격 WebSocket 연결 시도...")
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공!")
            
            # 초기 메시지 수신
            initial_message = await websocket.recv()
            data = json.loads(initial_message)
            print(f"📨 초기 메시지: {data.get('type')}")
            print(f"📊 데이터: {json.dumps(data.get('data', {}), indent=2)}")
            
            # keepalive 메시지 전송
            await websocket.send("ping")
            
            # 실시간 업데이트 몇 개 수신
            for i in range(3):
                print(f"\n⏳ 업데이트 {i+1} 대기 중...")
                message = await websocket.recv()
                data = json.loads(message)
                print(f"📨 수신: {data.get('type')}")
                if data.get('type') == 'price_update':
                    print(f"💰 TronNRG 가격: {data.get('data', {}).get('tronnrg', {}).get('price_per_energy')}")
                    print(f"💰 EnergyTRON 가격: {data.get('data', {}).get('energytron', {}).get('price_per_energy')}")
                
    except Exception as e:
        print(f"❌ 연결 실패: {e}")


async def test_system_health_websocket():
    """시스템 상태 WebSocket 테스트"""
    uri = "ws://localhost:8001/api/v1/ws/system/health"
    
    try:
        print("\n🔌 시스템 상태 WebSocket 연결 시도...")
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공!")
            
            # 초기 메시지 수신
            initial_message = await websocket.recv()
            data = json.loads(initial_message)
            print(f"📨 초기 메시지: {data.get('type')}")
            print(f"🏥 시스템 상태: {data.get('data', {}).get('status')}")
            print(f"📊 온라인 공급업체: {data.get('data', {}).get('online_providers')}")
            
            # keepalive 메시지 전송
            await websocket.send("ping")
            
    except Exception as e:
        print(f"❌ 연결 실패: {e}")


async def main():
    """메인 테스트 함수"""
    print("🚀 WebSocket 연결 테스트 시작")
    print("=" * 50)
    
    # 에너지 가격 WebSocket 테스트
    await test_energy_prices_websocket()
    
    # 시스템 상태 WebSocket 테스트  
    await test_system_health_websocket()
    
    print("\n✅ WebSocket 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
