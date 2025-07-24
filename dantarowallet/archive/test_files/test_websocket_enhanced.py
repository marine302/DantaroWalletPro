#!/usr/bin/env python3
"""
웹소켓 엔드포인트 확장 테스트
새로 추가된 실시간 기능들을 테스트
"""
import asyncio
import json
import logging
from typing import Dict, List, Any
import websockets

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.connections: Dict[str, Any] = {}
        
    async def connect_endpoint(self, endpoint: str, name: str):
        """특정 웹소켓 엔드포인트에 연결"""
        try:
            uri = f"{self.base_url}/api/v1/ws{endpoint}"
            websocket = await websockets.connect(uri)
            self.connections[name] = websocket
            logger.info(f"✅ Connected to {name}: {uri}")
            return websocket
        except Exception as e:
            logger.error(f"❌ Failed to connect to {name}: {e}")
            return None
    
    async def test_energy_prices(self):
        """에너지 가격 웹소켓 테스트"""
        logger.info("🔋 Testing energy prices WebSocket...")
        
        websocket = await self.connect_endpoint("/energy-prices", "energy_prices")
        if not websocket:
            return
        
        try:
            # 몇 개의 메시지를 받아보기
            for i in range(3):
                message = await asyncio.wait_for(websocket.recv(), timeout=35)
                data = json.loads(message)
                
                logger.info(f"💰 Energy prices update {i+1}:")
                logger.info(f"   Timestamp: {data['timestamp']}")
                logger.info(f"   Providers: {len(data['data']['providers'])}")
                
                if data['data']['best_price']:
                    best = data['data']['best_price']
                    logger.info(f"   Best price: {best['price_per_energy']} TRX/energy ({best['provider']})")
                
                logger.info(f"   Average price: {data['data']['average_price']:.8f} TRX/energy")
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for energy prices")
        except Exception as e:
            logger.error(f"❌ Error in energy prices test: {e}")
        finally:
            await websocket.close()
    
    async def test_system_health(self):
        """시스템 상태 웹소켓 테스트"""
        logger.info("🏥 Testing system health WebSocket...")
        
        websocket = await self.connect_endpoint("/system-health", "system_health")
        if not websocket:
            return
        
        try:
            # 2개의 메시지를 받아보기
            for i in range(2):
                message = await asyncio.wait_for(websocket.recv(), timeout=65)
                data = json.loads(message)
                
                logger.info(f"📊 System health update {i+1}:")
                logger.info(f"   Database: {data['data']['database']['status']}")
                logger.info(f"   Active partners: {data['data']['active_partners']}")
                logger.info(f"   Pending withdrawals: {data['data']['pending_withdrawals']}")
                
                energy_pools = data['data']['energy_pools']
                logger.info(f"   Energy pools: {energy_pools['total_partners']} total, "
                          f"{energy_pools['critical']} critical, {energy_pools['low']} low")
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for system health")
        except Exception as e:
            logger.error(f"❌ Error in system health test: {e}")
        finally:
            await websocket.close()
    
    async def test_onboarding_progress(self, partner_id: int = 1):
        """온보딩 진행 상황 웹소켓 테스트"""
        logger.info(f"🚀 Testing onboarding progress WebSocket for partner {partner_id}...")
        
        websocket = await self.connect_endpoint(f"/onboarding-progress/{partner_id}", "onboarding")
        if not websocket:
            return
        
        try:
            # 몇 개의 메시지를 받아보기
            for i in range(3):
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(message)
                
                progress_data = data['data']
                logger.info(f"📝 Onboarding progress update {i+1}:")
                logger.info(f"   Status: {progress_data['overall_status']}")
                logger.info(f"   Current step: {progress_data['current_step']}")
                logger.info(f"   Progress: {progress_data['progress_percentage']}%")
                
                logger.info("   Steps:")
                for step in progress_data['steps']:
                    status_emoji = {"completed": "✅", "running": "🔄", "pending": "⏳"}.get(step['status'], "❓")
                    logger.info(f"     {status_emoji} Step {step['step_number']}: {step['step_name']} ({step['status']})")
                
                completed_checklist = [item for item in progress_data['checklist'] if item['is_completed']]
                logger.info(f"   Checklist: {len(completed_checklist)}/{len(progress_data['checklist'])} completed")
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for onboarding progress")
        except Exception as e:
            logger.error(f"❌ Error in onboarding progress test: {e}")
        finally:
            await websocket.close()
    
    async def test_energy_usage(self, partner_id: int = 1):
        """에너지 사용량 웹소켓 테스트"""
        logger.info(f"⚡ Testing energy usage WebSocket for partner {partner_id}...")
        
        websocket = await self.connect_endpoint(f"/energy-usage/{partner_id}", "energy_usage")
        if not websocket:
            return
        
        try:
            # 2개의 메시지를 받아보기
            for i in range(2):
                message = await asyncio.wait_for(websocket.recv(), timeout=35)
                data = json.loads(message)
                
                usage_data = data['data']
                logger.info(f"⚡ Energy usage update {i+1}:")
                logger.info(f"   Current usage: {usage_data['current_usage']:,} energy")
                logger.info(f"   Daily usage: {usage_data['daily_usage']:,} energy")
                logger.info(f"   Monthly usage: {usage_data['monthly_usage']:,} energy")
                logger.info(f"   Remaining quota: {usage_data['remaining_quota']:,} energy")
                logger.info(f"   Usage rate: {usage_data['usage_rate']:.0f} energy/hour")
                logger.info(f"   Cost today: {usage_data['cost_today']} TRX")
                logger.info(f"   Cost month: {usage_data['cost_month']} TRX")
                
                if usage_data['alerts']:
                    logger.info("   Alerts:")
                    for alert in usage_data['alerts']:
                        level_emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(alert['level'], "❓")
                        logger.info(f"     {level_emoji} {alert['message']}")
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for energy usage")
        except Exception as e:
            logger.error(f"❌ Error in energy usage test: {e}")
        finally:
            await websocket.close()
    
    async def test_withdrawal_batch_status(self, partner_id: int = 1):
        """출금 배치 상태 웹소켓 테스트"""
        logger.info(f"💳 Testing withdrawal batch status WebSocket for partner {partner_id}...")
        
        websocket = await self.connect_endpoint(f"/withdrawal-batch-status/{partner_id}", "withdrawal_batch")
        if not websocket:
            return
        
        try:
            # 2개의 메시지를 받아보기
            for i in range(2):
                message = await asyncio.wait_for(websocket.recv(), timeout=20)
                data = json.loads(message)
                
                batch_data = data['data']
                logger.info(f"💳 Withdrawal batch status update {i+1}:")
                logger.info(f"   Total active batches: {batch_data['total_active']}")
                logger.info(f"   Pending signature: {batch_data['pending_signature']}")
                logger.info(f"   Executing: {batch_data['executing']}")
                
                if batch_data['active_batches']:
                    logger.info("   Active batches:")
                    for batch in batch_data['active_batches']:
                        logger.info(f"     Batch {batch['batch_id']}: {batch['status']} "
                                  f"({batch['progress_percentage']:.0f}% - {batch['total_amount']} TRX)")
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for withdrawal batch status")
        except Exception as e:
            logger.error(f"❌ Error in withdrawal batch status test: {e}")
        finally:
            await websocket.close()
    
    async def test_emergency_alerts(self):
        """위기 알림 웹소켓 테스트"""
        logger.info("🚨 Testing emergency alerts WebSocket...")
        
        websocket = await self.connect_endpoint("/emergency-alerts", "emergency_alerts")
        if not websocket:
            return
        
        try:
            # 2분 동안 알림을 기다림 (10분마다 테스트 알림이 발생)
            for i in range(2):
                message = await asyncio.wait_for(websocket.recv(), timeout=65)
                data = json.loads(message)
                
                alerts_data = data['data']
                logger.info(f"🚨 Emergency alerts update {i+1}:")
                logger.info(f"   Alert count: {alerts_data['alert_count']}")
                logger.info(f"   Severity: {alerts_data['severity']}")
                
                if alerts_data['alerts']:
                    logger.info("   Alerts:")
                    for alert in alerts_data['alerts']:
                        severity_emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(alert['severity'], "❓")
                        logger.info(f"     {severity_emoji} {alert['type']}: {alert['message']}")
                        if alert.get('action_required'):
                            logger.info(f"       🔧 Action required!")
                
        except asyncio.TimeoutError:
            logger.info("ℹ️ No emergency alerts received (this is normal)")
        except Exception as e:
            logger.error(f"❌ Error in emergency alerts test: {e}")
        finally:
            await websocket.close()
    
    async def test_admin_events(self):
        """관리자 이벤트 웹소켓 테스트"""
        logger.info("👨‍💼 Testing admin events WebSocket...")
        
        websocket = await self.connect_endpoint("/admin-events", "admin_events")
        if not websocket:
            return
        
        try:
            # 1분 동안 이벤트를 기다림 (5분마다 테스트 이벤트가 발생)
            for i in range(6):  # 10초 간격으로 6번 시도
                message = await asyncio.wait_for(websocket.recv(), timeout=12)
                data = json.loads(message)
                
                event_data = data['data']
                logger.info(f"👨‍💼 Admin event {i+1}:")
                logger.info(f"   Type: {event_data['type']}")
                logger.info(f"   Message: {event_data['message']}")
                logger.info(f"   Timestamp: {event_data['timestamp']}")
                
        except asyncio.TimeoutError:
            logger.info("ℹ️ No admin events received (waiting for 5-minute interval)")
        except Exception as e:
            logger.error(f"❌ Error in admin events test: {e}")
        finally:
            await websocket.close()
    
    async def test_order_status(self, order_id: int = 1):
        """주문 상태 웹소켓 테스트"""
        logger.info(f"📦 Testing order status WebSocket for order {order_id}...")
        
        websocket = await self.connect_endpoint(f"/order-status/{order_id}", "order_status")
        if not websocket:
            return
        
        try:
            # 몇 개의 메시지를 받아보기
            for i in range(3):
                message = await asyncio.wait_for(websocket.recv(), timeout=15)
                data = json.loads(message)
                
                order_data = data['data']
                logger.info(f"📦 Order status update {i+1}:")
                logger.info(f"   Order ID: {data['order_id']}")
                logger.info(f"   Type: {order_data['type']}")
                logger.info(f"   Status: {order_data['status']}")
                logger.info(f"   Progress: {order_data['progress']:.1f}%")
                
                if 'details' in order_data:
                    details = order_data['details']
                    logger.info(f"   Details: {details}")
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for order status")
        except Exception as e:
            logger.error(f"❌ Error in order status test: {e}")
        finally:
            await websocket.close()
    
    async def run_all_tests(self):
        """모든 웹소켓 엔드포인트 테스트 실행"""
        logger.info("🧪 Starting comprehensive WebSocket tests...")
        logger.info("=" * 60)
        
        tests = [
            ("Energy Prices", self.test_energy_prices()),
            ("System Health", self.test_system_health()),
            ("Order Status", self.test_order_status(1)),
            ("Onboarding Progress", self.test_onboarding_progress(1)),
            ("Energy Usage", self.test_energy_usage(1)),
            ("Withdrawal Batch Status", self.test_withdrawal_batch_status(1)),
            ("Emergency Alerts", self.test_emergency_alerts()),
            ("Admin Events", self.test_admin_events()),
        ]
        
        for test_name, test_coro in tests:
            logger.info(f"\n🔍 Running {test_name} test...")
            try:
                await test_coro
                logger.info(f"✅ {test_name} test completed")
            except Exception as e:
                logger.error(f"❌ {test_name} test failed: {e}")
            
            # 테스트 간 짧은 대기
            await asyncio.sleep(1)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 All WebSocket tests completed!")

async def check_server_status():
    """서버 상태 확인"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Server is running")
            return True
        else:
            logger.error(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    logger.info("🚀 Enhanced WebSocket Endpoint Tester")
    logger.info("Testing new real-time features...")
    
    # 서버 상태 확인
    if not await check_server_status():
        logger.error("💥 Server is not running. Please start the server first.")
        return
    
    # 웹소켓 테스터 실행
    tester = WebSocketTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"💥 Test failed with error: {e}")
