# Copilot 문서 #22: 지원 시스템 및 모니터링

## 목표
파트너사를 효과적으로 지원하고 전체 시스템을 모니터링할 수 있는 통합 지원 시스템을 구축합니다.

## 상세 지시사항

### 1. 티켓 시스템 구축

#### 1.1 티켓 모델 정의
```python
# app/models/support.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50))  # api, billing, technical, etc.
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    assigned_to = Column(Integer, ForeignKey("admin_users.id"))
    
    # 관계
    partner = relationship("Partner", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket")
    
class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"))
    sender_id = Column(Integer)  # partner user or admin
    sender_type = Column(String(20))  # 'partner' or 'admin'
    message = Column(Text, nullable=False)
    attachments = Column(JSON)
    
    ticket = relationship("SupportTicket", back_populates="messages")
```

#### 1.2 티켓 API 엔드포인트
```python
# app/api/v1/endpoints/support.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter()

@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket: TicketCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """파트너사 지원 티켓 생성"""
    # 우선순위 자동 설정
    if "urgent" in ticket.title.lower() or "critical" in ticket.description.lower():
        ticket.priority = TicketPriority.HIGH
        
    # 카테고리 자동 분류
    ticket.category = classify_ticket(ticket.title, ticket.description)
    
    # 티켓 생성 및 알림
    new_ticket = await create_support_ticket(db, partner.id, ticket)
    await notify_support_team(new_ticket)
    
    return new_ticket

@router.get("/tickets/{ticket_id}/messages")
async def get_ticket_messages(
    ticket_id: int,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """티켓 메시지 조회"""
    messages = await get_ticket_conversation(db, ticket_id, partner.id)
    return messages
```

### 2. 실시간 시스템 상태 모니터링

#### 2.1 모니터링 대시보드 구현
```python
# app/monitoring/dashboard.py
from datetime import datetime, timedelta
import asyncio

class SystemMonitor:
    def __init__(self):
        self.metrics = {
            "api_health": [],
            "database_health": [],
            "energy_pool_status": [],
            "transaction_volume": [],
            "error_rates": []
        }
        
    async def collect_metrics(self):
        """실시간 메트릭 수집"""
        while True:
            metrics = {
                "timestamp": datetime.utcnow(),
                "api_response_time": await self.check_api_health(),
                "db_connection_pool": await self.check_db_health(),
                "energy_usage": await self.check_energy_status(),
                "active_partners": await self.count_active_partners(),
                "transaction_stats": await self.get_transaction_stats()
            }
            
            await self.store_metrics(metrics)
            await self.check_alerts(metrics)
            
            await asyncio.sleep(60)  # 1분마다 수집
            
    async def check_alerts(self, metrics):
        """임계값 기반 알림"""
        alerts = []
        
        # API 응답 시간 체크
        if metrics["api_response_time"] > 1000:  # 1초 이상
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": "API response time degraded"
            })
            
        # 에너지 풀 체크
        if metrics["energy_usage"]["available_percentage"] < 20:
            alerts.append({
                "type": "energy",
                "severity": "critical",
                "message": "Energy pool running low"
            })
            
        # 알림 발송
        for alert in alerts:
            await self.send_alert(alert)
```

#### 2.2 웹소켓 기반 실시간 모니터링
```python
# app/websocket/monitoring.py
from fastapi import WebSocket, WebSocketDisconnect
import json

class MonitoringWebSocket:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast_metrics(self, metrics: dict):
        """모든 연결된 클라이언트에 메트릭 전송"""
        message = json.dumps({
            "type": "metrics_update",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 연결 끊김 처리
                self.active_connections.remove(connection)

# WebSocket 엔드포인트
@app.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket):
    monitor = MonitoringWebSocket()
    await monitor.connect(websocket)
    
    try:
        while True:
            # 클라이언트 메시지 대기
            data = await websocket.receive_text()
            
            # 요청된 메트릭 전송
            if data == "get_metrics":
                metrics = await get_current_metrics()
                await websocket.send_json(metrics)
                
    except WebSocketDisconnect:
        monitor.disconnect(websocket)
```

### 3. 자동 알림 시스템

#### 3.1 알림 채널 관리
```python
# app/services/notifications.py
from abc import ABC, abstractmethod
import httpx
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any

class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, message: Dict[str, Any]):
        pass

class EmailNotification(NotificationChannel):
    def __init__(self, smtp_config: dict):
        self.smtp_config = smtp_config
        
    async def send(self, message: Dict[str, Any]):
        """이메일 알림 발송"""
        msg = MIMEText(message["body"])
        msg["Subject"] = message["subject"]
        msg["From"] = self.smtp_config["from"]
        msg["To"] = message["to"]
        
        with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as s:
            s.starttls()
            s.login(self.smtp_config["username"], self.smtp_config["password"])
            s.send_message(msg)

class WebhookNotification(NotificationChannel):
    async def send(self, message: Dict[str, Any]):
        """웹훅 알림 발송"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                message["webhook_url"],
                json={
                    "event": message["event"],
                    "data": message["data"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()

class SlackNotification(NotificationChannel):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    async def send(self, message: Dict[str, Any]):
        """Slack 알림 발송"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json={
                    "text": message["text"],
                    "attachments": message.get("attachments", [])
                }
            )
            response.raise_for_status()
```

#### 3.2 알림 규칙 엔진
```python
# app/services/alert_rules.py
from typing import List, Dict, Any
import json

class AlertRule:
    def __init__(self, rule_config: dict):
        self.name = rule_config["name"]
        self.condition = rule_config["condition"]
        self.channels = rule_config["channels"]
        self.cooldown = rule_config.get("cooldown", 300)  # 5분 기본값
        self.last_triggered = {}
        
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """규칙 평가"""
        # 조건 평가 (예: "energy_pool.available < 20")
        try:
            return eval(self.condition, {"metrics": metrics})
        except:
            return False
            
    def should_trigger(self, partner_id: int) -> bool:
        """쿨다운 체크"""
        last_time = self.last_triggered.get(partner_id)
        if not last_time:
            return True
            
        return (datetime.utcnow() - last_time).seconds > self.cooldown

class AlertManager:
    def __init__(self):
        self.rules = []
        self.notification_channels = {}
        
    def load_rules(self, rules_config: List[dict]):
        """알림 규칙 로드"""
        for rule_config in rules_config:
            self.rules.append(AlertRule(rule_config))
            
    async def process_metrics(self, partner_id: int, metrics: Dict[str, Any]):
        """메트릭 기반 알림 처리"""
        for rule in self.rules:
            if rule.evaluate(metrics) and rule.should_trigger(partner_id):
                await self.trigger_alert(partner_id, rule, metrics)
                rule.last_triggered[partner_id] = datetime.utcnow()
                
    async def trigger_alert(self, partner_id: int, rule: AlertRule, metrics: Dict[str, Any]):
        """알림 발송"""
        for channel_name in rule.channels:
            channel = self.notification_channels.get(channel_name)
            if channel:
                await channel.send({
                    "partner_id": partner_id,
                    "rule": rule.name,
                    "metrics": metrics,
                    "timestamp": datetime.utcnow()
                })
```

### 4. 성능 최적화 도구

#### 4.1 성능 프로파일링
```python
# app/monitoring/profiler.py
import time
import functools
from typing import Callable
import statistics

class PerformanceProfiler:
    def __init__(self):
        self.metrics = {}
        
    def profile(self, name: str):
        """데코레이터로 함수 성능 측정"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # 메트릭 기록
                    if name not in self.metrics:
                        self.metrics[name] = []
                    self.metrics[name].append(duration)
                    
                    # 로깅 (느린 작업)
                    if duration > 1.0:  # 1초 이상
                        logger.warning(f"Slow operation: {name} took {duration:.2f}s")
                        
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Operation failed: {name} after {duration:.2f}s", exc_info=e)
                    raise
                    
            return wrapper
        return decorator
        
    def get_stats(self, name: str) -> dict:
        """성능 통계 반환"""
        if name not in self.metrics:
            return {}
            
        times = self.metrics[name]
        return {
            "count": len(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "p95": statistics.quantiles(times, n=20)[18],  # 95th percentile
            "p99": statistics.quantiles(times, n=100)[98]  # 99th percentile
        }

# 사용 예제
profiler = PerformanceProfiler()

@profiler.profile("create_wallet")
async def create_wallet(user_id: int):
    # 지갑 생성 로직
    pass
```

### 5. 보안 모니터링

#### 5.1 보안 이벤트 추적
```python
# app/security/monitoring.py
from typing import Dict, Any
import hashlib

class SecurityMonitor:
    def __init__(self):
        self.suspicious_patterns = [
            r"union.*select",  # SQL injection
            r"<script.*?>",    # XSS
            r"\.\.\/",         # Path traversal
        ]
        
    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int],
        ip_address: str,
        details: Dict[str, Any]
    ):
        """보안 이벤트 로깅"""
        event = {
            "timestamp": datetime.utcnow(),
            "type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "hash": self.generate_event_hash(event_type, user_id, ip_address)
        }
        
        # 데이터베이스에 저장
        await save_security_event(event)
        
        # 심각한 이벤트는 즉시 알림
        if event_type in ["MULTIPLE_FAILED_LOGINS", "SUSPICIOUS_PATTERN", "UNAUTHORIZED_ACCESS"]:
            await self.alert_security_team(event)
            
    def generate_event_hash(self, event_type: str, user_id: int, ip: str) -> str:
        """이벤트 해시 생성 (중복 감지용)"""
        data = f"{event_type}:{user_id}:{ip}:{datetime.utcnow().date()}"
        return hashlib.sha256(data.encode()).hexdigest()
        
    async def check_rate_limit(self, user_id: int, action: str) -> bool:
        """비정상적인 요청 빈도 체크"""
        key = f"rate_limit:{user_id}:{action}"
        count = await redis.incr(key)
        
        if count == 1:
            await redis.expire(key, 60)  # 1분 윈도우
            
        limits = {
            "login": 5,
            "withdrawal": 3,
            "api_call": 100
        }
        
        if count > limits.get(action, 100):
            await self.log_security_event(
                "RATE_LIMIT_EXCEEDED",
                user_id,
                request.client.host,
                {"action": action, "count": count}
            )
            return False
            
        return True
```

## 검증 포인트

- [ ] 티켓 시스템이 정상 작동하는가?
- [ ] 실시간 모니터링 대시보드가 표시되는가?
- [ ] WebSocket 연결이 안정적인가?
- [ ] 알림이 설정된 채널로 전송되는가?
- [ ] 성능 프로파일링 데이터가 수집되는가?
- [ ] 보안 이벤트가 기록되는가?
- [ ] 자동 알림 규칙이 작동하는가?
- [ ] 시스템 상태가 실시간으로 업데이트되는가?