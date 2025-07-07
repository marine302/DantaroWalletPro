# Copilot 문서 #25: 에너지 부족 대응 시스템 구현

## 목표
TRON 에너지 풀이 부족한 상황에서도 사용자의 출금 서비스가 중단되지 않도록 다양한 대응 방안을 구현합니다.

## 상세 지시사항

### 1. 에너지 부족 대응 전략

#### 1.1 대응 옵션 모델
```python
# app/models/energy_fallback.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, JSON, Enum
from decimal import Decimal
import enum

class FallbackOption(enum.Enum):
    TRX_PAYMENT = "trx_payment"  # TRX로 수수료 직접 지불
    QUEUE_WAIT = "queue_wait"  # 에너지 충전 대기
    EXTERNAL_POOL = "external_pool"  # 외부 에너지 풀 사용
    POSTPONE = "postpone"  # 출금 연기

class EnergyFallbackConfig(Base):
    __tablename__ = "energy_fallback_configs"
    
    id = Column(Integer, primary_key=True)
    
    # TRX 직접 결제 설정
    trx_payment_enabled = Column(Boolean, default=True)
    trx_payment_markup = Column(Numeric(5, 2), default=1.5)  # 150% (50% 마크업)
    trx_payment_min_balance = Column(Numeric(20, 6), default=10)  # 최소 TRX 잔액
    
    # 대기열 설정
    queue_enabled = Column(Boolean, default=True)
    queue_max_wait_hours = Column(Integer, default=24)  # 최대 대기 시간
    queue_priority_fee = Column(Numeric(20, 6), default=5)  # 우선 처리 수수료
    
    # 외부 풀 설정
    external_pool_enabled = Column(Boolean, default=False)
    external_pool_providers = Column(JSON, default=list)  # 외부 제공자 목록
    external_pool_max_premium = Column(Numeric(5, 2), default=2.0)  # 최대 프리미엄
    
    # 알림 설정
    alert_threshold = Column(Integer, default=20)  # 에너지 20% 미만 시 알림
    critical_threshold = Column(Integer, default=10)  # 위급 상황 임계값
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WithdrawalQueue(Base):
    __tablename__ = "withdrawal_queues"
    
    id = Column(Integer, primary_key=True)
    withdrawal_id = Column(Integer, ForeignKey("withdrawals.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 대기열 정보
    queue_position = Column(Integer, nullable=False)
    priority_level = Column(Integer, default=0)  # 0=일반, 1=우선, 2=긴급
    estimated_energy_required = Column(Integer, nullable=False)
    
    # 상태
    status = Column(String(20), default="waiting")  # waiting, processing, completed, cancelled
    queued_at = Column(DateTime, default=datetime.utcnow)
    estimated_process_time = Column(DateTime)
    processed_at = Column(DateTime)
    
    # 관계
    withdrawal = relationship("Withdrawal", back_populates="queue_entry")
    user = relationship("User")

class EnergyPurchaseOrder(Base):
    __tablename__ = "energy_purchase_orders"
    
    id = Column(Integer, primary_key=True)
    provider_name = Column(String(100), nullable=False)
    
    # 구매 정보
    energy_amount = Column(Integer, nullable=False)
    price_per_energy = Column(Numeric(20, 8), nullable=False)
    total_cost_trx = Column(Numeric(20, 6), nullable=False)
    
    # 상태
    status = Column(String(20), default="pending")  # pending, completed, failed
    order_id = Column(String(100))  # 외부 주문 ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
```

### 2. 에너지 부족 감지 및 대응 서비스

#### 2.1 에너지 부족 대응 매니저
```python
# app/services/energy/fallback_manager.py
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import asyncio

class EnergyFallbackManager:
    def __init__(self, db_session, redis_client, energy_service, tron_client):
        self.db = db_session
        self.redis = redis_client
        self.energy_service = energy_service
        self.tron = tron_client
        
    async def check_energy_availability(
        self,
        required_energy: int,
        pool_id: int = 1
    ) -> Tuple[bool, Optional[str], Dict]:
        """에너지 가용성 확인 및 대안 제시"""
        # 현재 에너지 상태 확인
        pool_status = await self.energy_service.check_pool_status(pool_id)
        available_energy = pool_status['available_energy']
        
        if available_energy >= required_energy:
            return True, None, {"method": "energy_pool"}
            
        # 에너지 부족 - 대안 확인
        logger.warning(f"에너지 부족: 필요 {required_energy}, 가용 {available_energy}")
        
        # 대응 옵션 조회
        config = await self.get_fallback_config()
        options = []
        
        # 옵션 1: TRX 직접 결제
        if config.trx_payment_enabled:
            trx_cost = await self.calculate_trx_payment_cost(required_energy)
            options.append({
                "method": "trx_payment",
                "cost_trx": float(trx_cost),
                "cost_usd": float(trx_cost * await self.get_trx_price()),
                "immediate": True,
                "description": "TRX로 네트워크 수수료 직접 지불"
            })
            
        # 옵션 2: 대기열
        if config.queue_enabled:
            wait_time = await self.estimate_queue_wait_time(required_energy)
            options.append({
                "method": "queue_wait",
                "estimated_wait_minutes": wait_time,
                "immediate": False,
                "description": f"약 {wait_time}분 후 처리 예정"
            })
            
        # 옵션 3: 외부 에너지 풀
        if config.external_pool_enabled:
            external_options = await self.check_external_pools(required_energy)
            options.extend(external_options)
            
        if not options:
            return False, "no_options_available", {}
            
        return False, "energy_insufficient", {"options": options}
        
    async def execute_fallback_option(
        self,
        withdrawal_id: int,
        option: str,
        user_choice: Dict
    ) -> Dict:
        """선택된 대안 실행"""
        if option == FallbackOption.TRX_PAYMENT.value:
            return await self.execute_trx_payment(withdrawal_id, user_choice)
            
        elif option == FallbackOption.QUEUE_WAIT.value:
            return await self.add_to_queue(withdrawal_id, user_choice)
            
        elif option == FallbackOption.EXTERNAL_POOL.value:
            return await self.use_external_pool(withdrawal_id, user_choice)
            
        else:
            raise ValueError(f"알 수 없는 대안 옵션: {option}")
            
    async def execute_trx_payment(
        self,
        withdrawal_id: int,
        user_choice: Dict
    ) -> Dict:
        """TRX로 수수료 직접 지불"""
        withdrawal = await self.db.get(Withdrawal, withdrawal_id)
        if not withdrawal:
            raise ValueError("출금 요청을 찾을 수 없습니다")
            
        # 필요한 TRX 계산
        required_energy = await self.estimate_withdrawal_energy(withdrawal)
        trx_cost = await self.calculate_trx_payment_cost(required_energy)
        
        # 사용자 TRX 잔액 확인
        user_trx_balance = await self.get_user_trx_balance(withdrawal.user_id)
        if user_trx_balance < trx_cost:
            raise ValueError(f"TRX 잔액 부족: 필요 {trx_cost}, 보유 {user_trx_balance}")
            
        try:
            # TRX 차감
            await self.deduct_user_trx(withdrawal.user_id, trx_cost)
            
            # 출금 실행 (TRX 수수료 사용)
            tx_result = await self.execute_withdrawal_with_trx(
                withdrawal,
                trx_fee=trx_cost
            )
            
            # 기록 저장
            await self.record_trx_payment(
                withdrawal_id=withdrawal_id,
                trx_amount=trx_cost,
                tx_id=tx_result['tx_id']
            )
            
            return {
                "success": True,
                "method": "trx_payment",
                "tx_id": tx_result['tx_id'],
                "trx_fee_paid": float(trx_cost),
                "message": "TRX 수수료로 출금이 처리되었습니다"
            }
            
        except Exception as e:
            # 실패 시 TRX 환불
            await self.refund_user_trx(withdrawal.user_id, trx_cost)
            raise
            
    async def add_to_queue(
        self,
        withdrawal_id: int,
        user_choice: Dict
    ) -> Dict:
        """출금 요청을 대기열에 추가"""
        withdrawal = await self.db.get(Withdrawal, withdrawal_id)
        
        # 우선순위 결정
        priority_level = 0
        if user_choice.get('priority', False):
            # 우선 처리 수수료 지불
            config = await self.get_fallback_config()
            await self.charge_priority_fee(
                withdrawal.user_id,
                config.queue_priority_fee
            )
            priority_level = 1
            
        # 현재 큐 위치 계산
        queue_position = await self.get_next_queue_position(priority_level)
        
        # 예상 처리 시간 계산
        estimated_time = await self.estimate_processing_time(
            queue_position,
            await self.estimate_withdrawal_energy(withdrawal)
        )
        
        # 대기열에 추가
        queue_entry = WithdrawalQueue(
            withdrawal_id=withdrawal_id,
            user_id=withdrawal.user_id,
            queue_position=queue_position,
            priority_level=priority_level,
            estimated_energy_required=await self.estimate_withdrawal_energy(withdrawal),
            estimated_process_time=estimated_time
        )
        
        self.db.add(queue_entry)
        await self.db.commit()
        
        # 사용자에게 알림
        await self.send_queue_notification(withdrawal.user_id, queue_entry)
        
        return {
            "success": True,
            "method": "queue_wait",
            "queue_position": queue_position,
            "estimated_wait_time": estimated_time.isoformat(),
            "priority": priority_level > 0,
            "message": f"출금이 대기열 {queue_position}번째에 추가되었습니다"
        }
```

### 3. 대기열 처리 시스템

#### 3.1 대기열 프로세서
```python
# app/services/energy/queue_processor.py
from typing import List, Optional
import asyncio
from datetime import datetime, timedelta

class WithdrawalQueueProcessor:
    def __init__(self, db_session, energy_service, withdrawal_service):
        self.db = db_session
        self.energy_service = energy_service
        self.withdrawal_service = withdrawal_service
        self.processing = False
        
    async def start_processing(self):
        """대기열 처리 시작"""
        self.processing = True
        
        while self.processing:
            try:
                # 에너지 상태 확인
                pool_status = await self.energy_service.check_pool_status()
                
                if pool_status['status'] in ['ACTIVE', 'LOW']:
                    # 처리 가능한 항목 선택
                    items = await self.get_processable_items(
                        pool_status['available_energy']
                    )
                    
                    if items:
                        await self.process_queue_items(items)
                        
                # 30초 대기
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"대기열 처리 오류: {str(e)}")
                await asyncio.sleep(60)  # 오류 시 1분 대기
                
    async def get_processable_items(
        self,
        available_energy: int
    ) -> List[WithdrawalQueue]:
        """처리 가능한 대기열 항목 조회"""
        # 우선순위와 대기 시간을 고려한 쿼리
        query = select(WithdrawalQueue).where(
            WithdrawalQueue.status == "waiting"
        ).order_by(
            WithdrawalQueue.priority_level.desc(),
            WithdrawalQueue.queued_at.asc()
        )
        
        result = await self.db.execute(query)
        all_items = result.scalars().all()
        
        # 에너지 한도 내에서 처리 가능한 항목 선택
        selected_items = []
        total_energy_needed = 0
        
        for item in all_items:
            if total_energy_needed + item.estimated_energy_required <= available_energy:
                selected_items.append(item)
                total_energy_needed += item.estimated_energy_required
            else:
                # 더 이상 처리할 수 없음
                break
                
        return selected_items
        
    async def process_queue_items(self, items: List[WithdrawalQueue]):
        """대기열 항목 처리"""
        for item in items:
            try:
                # 상태 업데이트
                item.status = "processing"
                await self.db.commit()
                
                # 출금 처리
                withdrawal = item.withdrawal
                result = await self.withdrawal_service.process_withdrawal(
                    withdrawal_id=withdrawal.id,
                    use_energy_pool=True
                )
                
                # 완료 처리
                item.status = "completed"
                item.processed_at = datetime.utcnow()
                
                # 사용자 알림
                await self.notify_user_completion(item)
                
            except Exception as e:
                logger.error(f"대기열 항목 처리 실패 {item.id}: {str(e)}")
                item.status = "failed"
                
            await self.db.commit()
            
    async def update_queue_positions(self):
        """대기열 위치 업데이트"""
        # 처리된 항목 제거 후 위치 재계산
        waiting_items = await self.db.execute(
            select(WithdrawalQueue)
            .where(WithdrawalQueue.status == "waiting")
            .order_by(
                WithdrawalQueue.priority_level.desc(),
                WithdrawalQueue.queued_at.asc()
            )
        )
        
        position = 1
        for item in waiting_items.scalars():
            item.queue_position = position
            position += 1
            
            # 예상 시간 재계산
            item.estimated_process_time = await self.estimate_processing_time(
                position,
                item.estimated_energy_required
            )
            
        await self.db.commit()
```

### 4. 외부 에너지 풀 연동

#### 4.1 외부 풀 연동 서비스
```python
# app/services/energy/external_pool_service.py
import httpx
from typing import Dict, List, Optional

class ExternalEnergyPoolService:
    def __init__(self, config: Dict):
        self.providers = {
            "justlend": JustLendProvider(),
            "energy_rental": EnergyRentalProvider(),
            "tron_energy_market": TronEnergyMarketProvider()
        }
        self.http_client = httpx.AsyncClient()
        
    async def check_external_availability(
        self,
        required_energy: int
    ) -> List[Dict]:
        """외부 에너지 풀 가용성 확인"""
        available_options = []
        
        for provider_name, provider in self.providers.items():
            try:
                availability = await provider.check_availability(required_energy)
                
                if availability['available']:
                    available_options.append({
                        "provider": provider_name,
                        "energy_available": availability['energy_available'],
                        "price_per_energy": availability['price_per_energy'],
                        "total_cost": availability['total_cost'],
                        "delivery_time": availability['delivery_time'],
                        "reliability_score": provider.reliability_score
                    })
                    
            except Exception as e:
                logger.error(f"외부 풀 확인 실패 {provider_name}: {str(e)}")
                continue
                
        # 가격순 정렬
        available_options.sort(key=lambda x: x['total_cost'])
        
        return available_options
        
    async def rent_energy(
        self,
        provider_name: str,
        energy_amount: int,
        target_address: str
    ) -> Dict:
        """외부 풀에서 에너지 대여"""
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"알 수 없는 제공자: {provider_name}")
            
        try:
            # 주문 생성
            order = await provider.create_order(
                energy_amount=energy_amount,
                receiver_address=target_address,
                duration_hours=1  # 1시간 대여
            )
            
            # 주문 기록
            purchase_order = EnergyPurchaseOrder(
                provider_name=provider_name,
                energy_amount=energy_amount,
                price_per_energy=order['price_per_energy'],
                total_cost_trx=order['total_cost'],
                order_id=order['order_id']
            )
            
            self.db.add(purchase_order)
            await self.db.commit()
            
            # 주문 완료 대기
            result = await provider.wait_for_completion(order['order_id'])
            
            if result['status'] == 'completed':
                purchase_order.status = 'completed'
                purchase_order.completed_at = datetime.utcnow()
                await self.db.commit()
                
                return {
                    "success": True,
                    "provider": provider_name,
                    "energy_received": energy_amount,
                    "cost": float(order['total_cost']),
                    "order_id": order['order_id']
                }
            else:
                raise Exception(f"주문 실패: {result['error']}")
                
        except Exception as e:
            logger.error(f"에너지 대여 실패: {str(e)}")
            raise

class JustLendProvider:
    """JustLend 에너지 제공자"""
    def __init__(self):
        self.api_base = "https://api.justlend.org"
        self.reliability_score = 0.95
        
    async def check_availability(self, required_energy: int) -> Dict:
        # JustLend API 호출 구현
        pass
        
    async def create_order(self, **kwargs) -> Dict:
        # 주문 생성 구현
        pass
```

### 5. 사용자 API 엔드포인트

#### 5.1 에너지 상태 및 대안 확인
```python
# app/api/v1/endpoints/energy_fallback.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

router = APIRouter()

@router.get("/energy/status", response_model=EnergyStatusResponse)
async def check_energy_status(
    current_user: User = Depends(get_current_user),
    energy_service: EnergyPoolManager = Depends(get_energy_service)
):
    """현재 에너지 풀 상태 확인"""
    pool_status = await energy_service.check_pool_status()
    
    # 사용자 친화적 정보로 변환
    if pool_status['usage_percentage'] < 80:
        service_status = "정상"
        message = "출금 서비스가 정상 운영 중입니다"
    elif pool_status['usage_percentage'] < 90:
        service_status = "주의"
        message = "에너지가 부족해지고 있습니다. 대기 시간이 발생할 수 있습니다"
    else:
        service_status = "제한"
        message = "에너지 부족으로 대체 옵션을 사용해야 할 수 있습니다"
        
    return {
        "service_status": service_status,
        "message": message,
        "energy_available_percentage": 100 - pool_status['usage_percentage'],
        "alternative_options_available": pool_status['usage_percentage'] > 90
    }

@router.post("/withdrawals/{withdrawal_id}/check-options", response_model=WithdrawalOptionsResponse)
async def check_withdrawal_options(
    withdrawal_id: int,
    current_user: User = Depends(get_current_user),
    fallback_manager: EnergyFallbackManager = Depends(get_fallback_manager)
):
    """출금 처리 옵션 확인"""
    withdrawal = await get_user_withdrawal(withdrawal_id, current_user.id)
    
    # 필요 에너지 계산
    required_energy = await fallback_manager.estimate_withdrawal_energy(withdrawal)
    
    # 옵션 확인
    available, reason, details = await fallback_manager.check_energy_availability(
        required_energy
    )
    
    if available:
        return {
            "can_process_immediately": True,
            "reason": "sufficient_energy",
            "options": [{
                "method": "standard",
                "description": "표준 처리 (에너지 풀 사용)",
                "cost": 0,
                "immediate": True
            }]
        }
    else:
        return {
            "can_process_immediately": False,
            "reason": reason,
            "options": details.get('options', []),
            "recommendation": "TRX 직접 결제를 추천합니다"
        }

@router.post("/withdrawals/{withdrawal_id}/process-with-option")
async def process_withdrawal_with_option(
    withdrawal_id: int,
    option: ProcessWithOptionRequest,
    current_user: User = Depends(get_current_user),
    fallback_manager: EnergyFallbackManager = Depends(get_fallback_manager)
):
    """선택한 옵션으로 출금 처리"""
    withdrawal = await get_user_withdrawal(withdrawal_id, current_user.id)
    
    if withdrawal.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="이미 처리된 출금입니다"
        )
        
    try:
        result = await fallback_manager.execute_fallback_option(
            withdrawal_id=withdrawal_id,
            option=option.method,
            user_choice=option.dict()
        )
        
        return {
            "success": True,
            "result": result,
            "message": f"{option.method} 방식으로 처리되었습니다"
        }
        
    except Exception as e:
        logger.error(f"대안 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/withdrawals/queue/my-position", response_model=QueuePositionResponse)
async def get_my_queue_position(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """내 출금 대기열 위치 확인"""
    query = select(WithdrawalQueue).where(
        WithdrawalQueue.user_id == current_user.id,
        WithdrawalQueue.status == "waiting"
    )
    
    result = await db.execute(query)
    queue_entries = result.scalars().all()
    
    if not queue_entries:
        return {
            "in_queue": False,
            "entries": []
        }
        
    return {
        "in_queue": True,
        "entries": [
            {
                "withdrawal_id": entry.withdrawal_id,
                "position": entry.queue_position,
                "priority": entry.priority_level > 0,
                "estimated_time": entry.estimated_process_time,
                "queued_at": entry.queued_at
            }
            for entry in queue_entries
        ]
    }
```

### 6. 모니터링 및 알림

#### 6.1 에너지 부족 알림 시스템
```python
# app/services/notifications/energy_alerts.py
from typing import List, Dict
import asyncio

class EnergyAlertSystem:
    def __init__(self, notification_service, energy_service):
        self.notification_service = notification_service
        self.energy_service = energy_service
        self.alert_history = {}
        
    async def monitor_and_alert(self):
        """에너지 상태 모니터링 및 알림"""
        while True:
            try:
                # 모든 활성 풀 확인
                pools = await self.energy_service.get_all_active_pools()
                
                for pool in pools:
                    status = await self.energy_service.check_pool_status(pool.id)
                    await self.check_and_send_alerts(pool, status)
                    
                await asyncio.sleep(300)  # 5분마다
                
            except Exception as e:
                logger.error(f"에너지 모니터링 오류: {str(e)}")
                await asyncio.sleep(600)  # 오류 시 10분 대기
                
    async def check_and_send_alerts(self, pool, status):
        """알림 조건 확인 및 발송"""
        usage_percentage = status['usage_percentage']
        pool_id = pool.id
        
        # 이전 알림 확인 (중복 방지)
        last_alert = self.alert_history.get(pool_id, {})
        
        # 위급 상황 (90% 이상 사용)
        if usage_percentage >= 90 and last_alert.get('level') != 'critical':
            await self.send_critical_alert(pool, status)
            self.alert_history[pool_id] = {
                'level': 'critical',
                'time': datetime.utcnow()
            }
            
        # 경고 상황 (80% 이상 사용)
        elif usage_percentage >= 80 and last_alert.get('level') not in ['warning', 'critical']:
            await self.send_warning_alert(pool, status)
            self.alert_history[pool_id] = {
                'level': 'warning',
                'time': datetime.utcnow()
            }
            
        # 정상 복귀
        elif usage_percentage < 70 and last_alert.get('level'):
            await self.send_recovery_alert(pool, status)
            self.alert_history[pool_id] = {}
            
    async def send_critical_alert(self, pool, status):
        """위급 알림 발송"""
        message = f"""
        🚨 **에너지 풀 위급 상황**
        
        풀 이름: {pool.pool_name}
        사용률: {status['usage_percentage']:.1f}%
        남은 에너지: {status['available_energy']:,}
        
        즉시 조치가 필요합니다:
        1. 추가 TRX 동결
        2. 외부 에너지 구매
        3. 서비스 일시 제한
        """
        
        # 관리자 전체에게 알림
        await self.notification_service.send_admin_alert(
            title="에너지 풀 위급",
            message=message,
            priority="critical"
        )
        
        # 슬랙/디스코드 웹훅
        await self.notification_service.send_webhook(
            url=settings.CRITICAL_ALERT_WEBHOOK,
            data={"text": message}
        )
```

### 7. 프론트엔드 연동을 위한 WebSocket

#### 7.1 실시간 에너지 상태 전송
```python
# app/websocket/energy_status.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class EnergyStatusWebSocket:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "admin": set(),
            "user": set()
        }
        
    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections[client_type].add(websocket)
        
        # 초기 상태 전송
        initial_status = await self.get_current_status()
        await websocket.send_json(initial_status)
        
    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].discard(websocket)
        
    async def broadcast_energy_update(self, update_data: Dict):
        """에너지 상태 업데이트 브로드캐스트"""
        # 관리자에게는 상세 정보
        admin_message = json.dumps({
            "type": "energy_update",
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for connection in self.active_connections["admin"]:
            try:
                await connection.send_text(admin_message)
            except:
                self.active_connections["admin"].discard(connection)
                
        # 사용자에게는 간단한 정보
        user_message = json.dumps({
            "type": "energy_update",
            "data": {
                "service_available": update_data['usage_percentage'] < 90,
                "alternative_required": update_data['usage_percentage'] >= 90,
                "message": self.get_user_friendly_message(update_data)
            }
        })
        
        for connection in self.active_connections["user"]:
            try:
                await connection.send_text(user_message)
            except:
                self.active_connections["user"].discard(connection)
```

## 검증 포인트

- [ ] 에너지 부족 시 대안이 제시되는가?
- [ ] TRX 직접 결제가 정상 작동하는가?
- [ ] 대기열 시스템이 우선순위대로 작동하는가?
- [ ] 외부 에너지 풀 연동이 가능한가?
- [ ] 실시간 알림이 발송되는가?
- [ ] WebSocket으로 상태가 업데이트되는가?
- [ ] 사용자가 옵션을 선택할 수 있는가?
- [ ] 대기열 처리가 자동으로 진행되는가?

이 시스템을 통해 에너지가 부족한 상황에서도 사용자에게 다양한 대안을 제공하여 서비스 연속성을 보장할 수 있습니다.