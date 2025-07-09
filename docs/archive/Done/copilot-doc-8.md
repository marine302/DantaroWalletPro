# Copilot 문서 #8: 기본 모니터링 시스템

## 목표
1인 운영을 위한 자동화된 모니터링 시스템을 구축합니다. 로그 수집, 메트릭 모니터링, 알림 시스템, 간단한 대시보드를 포함합니다.

## 전제 조건
- Copilot 문서 #1-6이 완료되어 있어야 합니다.
- Telegram Bot이 설정되어 있어야 합니다.
- 기본 애플리케이션이 실행 중이어야 합니다.

## 상세 지시사항

### 1. 메트릭 수집 미들웨어 (app/middleware/metrics.py)

```python
import time
import psutil
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)
        self.active_requests = 0
        self.start_time = datetime.utcnow()
        
        # 시스템 메트릭
        self.cpu_percent = 0
        self.memory_percent = 0
        self.disk_percent = 0
        
        # 백그라운드로 시스템 메트릭 수집
        asyncio.create_task(self._collect_system_metrics())
    
    async def _collect_system_metrics(self):
        """시스템 메트릭 주기적 수집"""
        while True:
            try:
                self.cpu_percent = psutil.cpu_percent(interval=1)
                self.memory_percent = psutil.virtual_memory().percent
                self.disk_percent = psutil.disk_usage('/').percent
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
            
            await asyncio.sleep(30)  # 30초마다 수집
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """요청 기록"""
        key = f"{method}:{path}"
        self.request_count[key] += 1
        self.request_duration[key].append(duration)
        
        # 최근 1시간 데이터만 유지
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.request_duration[key] = [
            d for d in self.request_duration[key][-1000:]  # 최대 1000개
        ]
        
        if status_code >= 400:
            self.error_count[key] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """현재 메트릭 반환"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # 요청 통계 계산
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # 응답 시간 통계
        all_durations = []
        for durations in self.request_duration.values():
            all_durations.extend(durations)
        
        avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
        p95_duration = sorted(all_durations)[int(len(all_durations) * 0.95)] if all_durations else 0
        p99_duration = sorted(all_durations)[int(len(all_durations) * 0.99)] if all_durations else 0
        
        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(error_rate, 2),
            "active_requests": self.active_requests,
            "avg_response_time_ms": round(avg_duration * 1000, 2),
            "p95_response_time_ms": round(p95_duration * 1000, 2),
            "p99_response_time_ms": round(p99_duration * 1000, 2),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "endpoint_stats": self._get_endpoint_stats()
        }
    
    def _get_endpoint_stats(self) -> list:
        """엔드포인트별 통계"""
        stats = []
        for endpoint, count in self.request_count.items():
            durations = self.request_duration[endpoint]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            stats.append({
                "endpoint": endpoint,
                "count": count,
                "errors": self.error_count.get(endpoint, 0),
                "avg_duration_ms": round(avg_duration * 1000, 2)
            })
        
        return sorted(stats, key=lambda x: x["count"], reverse=True)[:10]

# 글로벌 메트릭 수집기
metrics_collector = MetricsCollector()

class MetricsMiddleware(BaseHTTPMiddleware):
    """메트릭 수집 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 활성 요청 수 증가
        metrics_collector.active_requests += 1
        
        start_time = time.time()
        response = None
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # 메트릭 기록
            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
        
        finally:
            # 활성 요청 수 감소
            metrics_collector.active_requests -= 1
```

### 2. 헬스체크 서비스 (app/services/health_service.py)

```python
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import aioredis
from app.core.database import engine
from app.core.tron import TronService
from app.middleware.metrics import metrics_collector
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthService:
    """헬스체크 서비스"""
    
    def __init__(self):
        self.checks = {
            "database": self.check_database,
            "redis": self.check_redis,
            "tron": self.check_tron,
            "disk_space": self.check_disk_space,
            "memory": self.check_memory
        }
    
    async def check_database(self) -> Dict[str, Any]:
        """데이터베이스 연결 체크"""
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "message": "Database is accessible"
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Redis 연결 체크"""
        try:
            from app.core.config import settings
            redis = aioredis.from_url(settings.REDIS_URL)
            await redis.ping()
            await redis.close()
            return {
                "status": "healthy",
                "message": "Redis is accessible"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }
    
    async def check_tron(self) -> Dict[str, Any]:
        """TRON 네트워크 연결 체크"""
        try:
            tron = TronService()
            block_number = tron.get_block_number()
            return {
                "status": "healthy" if block_number > 0 else "unhealthy",
                "message": f"Latest block: {block_number}"
            }
        except Exception as e:
            logger.error(f"TRON health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """디스크 공간 체크"""
        disk_percent = metrics_collector.disk_percent
        status = "healthy" if disk_percent < 80 else "warning" if disk_percent < 90 else "critical"
        
        return {
            "status": status,
            "message": f"Disk usage: {disk_percent}%"
        }
    
    async def check_memory(self) -> Dict[str, Any]:
        """메모리 사용량 체크"""
        memory_percent = metrics_collector.memory_percent
        status = "healthy" if memory_percent < 80 else "warning" if memory_percent < 90 else "critical"
        
        return {
            "status": status,
            "message": f"Memory usage: {memory_percent}%"
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """전체 헬스 상태 조회"""
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = result
                
                if result["status"] == "unhealthy":
                    overall_status = "unhealthy"
                elif result["status"] == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                elif result["status"] == "critical":
                    overall_status = "critical"
                    
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    "status": "error",
                    "message": str(e)
                }
                overall_status = "critical"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "metrics": metrics_collector.get_metrics()
        }
```

### 3. 알림 서비스 (app/services/alert_service.py)

```python
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertService:
    """알림 서비스"""
    
    def __init__(self):
        self.telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID
        self.alert_history = []
        self.rate_limits = {}  # 알림 속도 제한
        
    async def send_telegram_message(self, message: str) -> bool:
        """Telegram 메시지 전송"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": self.telegram_chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                )
                
                if response.status_code == 200:
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send Telegram message: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def _check_rate_limit(self, alert_type: str, threshold_minutes: int = 5) -> bool:
        """알림 속도 제한 체크"""
        now = datetime.utcnow()
        last_sent = self.rate_limits.get(alert_type)
        
        if last_sent and (now - last_sent) < timedelta(minutes=threshold_minutes):
            return False
        
        self.rate_limits[alert_type] = now
        return True
    
    async def send_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        alert_type: Optional[str] = None
    ):
        """알림 전송"""
        # 속도 제한 체크
        if alert_type and not self._check_rate_limit(alert_type):
            logger.debug(f"Alert {alert_type} rate limited")
            return
        
        # 이모지 매핑
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        # Telegram 메시지 포맷
        telegram_message = f"""
{emoji_map[level]} <b>{title}</b>

{message}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        # 알림 기록
        self.alert_history.append({
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow(),
            "sent": False
        })
        
        # Telegram 전송
        sent = await self.send_telegram_message(telegram_message)
        self.alert_history[-1]["sent"] = sent
        
        # 최근 100개만 유지
        self.alert_history = self.alert_history[-100:]
    
    async def check_metrics_and_alert(self, metrics: Dict[str, Any]):
        """메트릭 기반 자동 알림"""
        # CPU 사용률 체크
        if metrics["cpu_percent"] > 90:
            await self.send_alert(
                "High CPU Usage",
                f"CPU usage is at {metrics['cpu_percent']}%",
                AlertLevel.CRITICAL,
                "high_cpu"
            )
        elif metrics["cpu_percent"] > 80:
            await self.send_alert(
                "CPU Usage Warning",
                f"CPU usage is at {metrics['cpu_percent']}%",
                AlertLevel.WARNING,
                "cpu_warning"
            )
        
        # 메모리 사용률 체크
        if metrics["memory_percent"] > 90:
            await self.send_alert(
                "High Memory Usage",
                f"Memory usage is at {metrics['memory_percent']}%",
                AlertLevel.CRITICAL,
                "high_memory"
            )
        
        # 디스크 사용률 체크
        if metrics["disk_percent"] > 90:
            await self.send_alert(
                "Low Disk Space",
                f"Disk usage is at {metrics['disk_percent']}%",
                AlertLevel.CRITICAL,
                "low_disk"
            )
        
        # 에러율 체크
        if metrics["error_rate"] > 10:
            await self.send_alert(
                "High Error Rate",
                f"Error rate is at {metrics['error_rate']}%",
                AlertLevel.ERROR,
                "high_error_rate"
            )
        
        # 응답 시간 체크
        if metrics["p99_response_time_ms"] > 1000:
            await self.send_alert(
                "Slow Response Time",
                f"P99 response time is {metrics['p99_response_time_ms']}ms",
                AlertLevel.WARNING,
                "slow_response"
            )

# 글로벌 알림 서비스 인스턴스
alert_service = AlertService()
```

### 4. 모니터링 대시보드 엔드포인트 (app/api/v1/endpoints/monitoring.py)

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import json

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction, TransactionStatus
from app.services.health_service import HealthService
from app.services.alert_service import alert_service
from app.middleware.metrics import metrics_collector

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """상세 헬스체크 (관리자 전용)"""
    health_service = HealthService()
    return await health_service.get_health_status()

@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """메트릭 조회 (관리자 전용)"""
    metrics = metrics_collector.get_metrics()
    
    # 자동 알림 체크
    await alert_service.check_metrics_and_alert(metrics)
    
    return metrics

@router.get("/alerts/history")
async def get_alert_history(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """알림 이력 조회"""
    return {
        "alerts": alert_service.alert_history[-50:],  # 최근 50개
        "total": len(alert_service.alert_history)
    }

@router.post("/alerts/test")
async def test_alert(
    level: str = "info",
    current_user: User = Depends(deps.get_current_admin_user)
):
    """알림 테스트"""
    await alert_service.send_alert(
        "Test Alert",
        "This is a test alert from DantaroWallet monitoring system",
        level=level
    )
    return {"message": "Test alert sent"}

@router.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard(
    request: Request,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """모니터링 대시보드 (간단한 HTML)"""
    # 기본 통계
    total_users = await db.execute(select(func.count(User.id)))
    total_users = total_users.scalar()
    
    # 최근 24시간 트랜잭션
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_tx_count = await db.execute(
        select(func.count(Transaction.id)).filter(
            Transaction.created_at > yesterday
        )
    )
    recent_tx_count = recent_tx_count.scalar()
    
    # 메트릭
    metrics = metrics_collector.get_metrics()
    
    # 헬스 상태
    health_service = HealthService()
    health_status = await health_service.get_health_status()
    
    return templates.TemplateResponse(
        "monitoring_dashboard.html",
        {
            "request": request,
            "total_users": total_users,
            "recent_tx_count": recent_tx_count,
            "metrics": metrics,
            "health_status": health_status,
            "current_time": datetime.utcnow()
        }
    )

@router.get("/logs/recent")
async def get_recent_logs(
    lines: int = 100,
    current_user: User = Depends(deps.get_current_admin_user)
):
    """최근 로그 조회"""
    try:
        with open("logs/app.log", "r") as f:
            logs = f.readlines()[-lines:]
        
        # JSON 로그 파싱
        parsed_logs = []
        for log in logs:
            try:
                parsed_logs.append(json.loads(log))
            except:
                parsed_logs.append({"message": log.strip()})
        
        return {
            "logs": parsed_logs,
            "count": len(parsed_logs)
        }
    except FileNotFoundError:
        return {"logs": [], "count": 0, "error": "Log file not found"}
```

### 5. 모니터링 대시보드 템플릿 (app/templates/monitoring_dashboard.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DantaroWallet Monitoring Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric {
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
        }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-unhealthy { color: #dc3545; }
        .status-critical { color: #dc3545; font-weight: bold; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .refresh-info {
            text-align: right;
            color: #666;
            font-size: 14px;
        }
    </style>
    <script>
        // Auto refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</head>
<body>
    <div class="container">
        <h1>DantaroWallet Monitoring Dashboard</h1>
        <div class="refresh-info">
            Last updated: {{ current_time.strftime('%Y-%m-%d %H:%M:%S') }} UTC
            (Auto-refresh in 30s)
        </div>

        <!-- System Status -->
        <div class="card">
            <h2>System Status: 
                <span class="status-{{ health_status.status }}">
                    {{ health_status.status.upper() }}
                </span>
            </h2>
            <div>
                {% for check_name, check_result in health_status.checks.items() %}
                <div class="metric">
                    <div class="metric-label">{{ check_name }}</div>
                    <div class="metric-value status-{{ check_result.status }}">
                        {{ check_result.status }}
                    </div>
                    <div style="font-size: 12px; color: #666;">
                        {{ check_result.message }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Key Metrics -->
        <div class="card">
            <h2>Key Metrics</h2>
            <div>
                <div class="metric">
                    <div class="metric-label">Total Users</div>
                    <div class="metric-value">{{ total_users }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">24h Transactions</div>
                    <div class="metric-value">{{ recent_tx_count }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Active Requests</div>
                    <div class="metric-value">{{ metrics.active_requests }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Error Rate</div>
                    <div class="metric-value">{{ metrics.error_rate }}%</div>
                </div>
            </div>
        </div>

        <!-- Performance Metrics -->
        <div class="card">
            <h2>Performance</h2>
            <div>
                <div class="metric">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{{ metrics.avg_response_time_ms }}ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">P95 Response Time</div>
                    <div class="metric-value">{{ metrics.p95_response_time_ms }}ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">P99 Response Time</div>
                    <div class="metric-value">{{ metrics.p99_response_time_ms }}ms</div>
                </div>
            </div>
        </div>

        <!-- System Resources -->
        <div class="card">
            <h2>System Resources</h2>
            <div>
                <div class="metric">
                    <div class="metric-label">CPU Usage</div>
                    <div class="metric-value">{{ metrics.cpu_percent }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Memory Usage</div>
                    <div class="metric-value">{{ metrics.memory_percent }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Disk Usage</div>
                    <div class="metric-value">{{ metrics.disk_percent }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Uptime</div>
                    <div class="metric-value">
                        {{ (metrics.uptime_seconds // 3600) }}h
                    </div>
                </div>
            </div>
        </div>

        <!-- Top Endpoints -->
        <div class="card">
            <h2>Top Endpoints</h2>
            <table>
                <thead>
                    <tr>
                        <th>Endpoint</th>
                        <th>Requests</th>
                        <th>Errors</th>
                        <th>Avg Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {% for stat in metrics.endpoint_stats[:10] %}
                    <tr>
                        <td>{{ stat.endpoint }}</td>
                        <td>{{ stat.count }}</td>
                        <td>{{ stat.errors }}</td>
                        <td>{{ stat.avg_duration_ms }}ms</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
```

### 6. 일일 리포트 생성 태스크 (app/tasks/daily_report.py)

```python
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.transaction import Transaction, TransactionStatus
from app.models.balance import Balance
from app.services.alert_service import alert_service, AlertLevel
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DailyReportTask:
    """일일 리포트 생성 태스크"""
    
    async def generate_daily_report(self):
        """일일 리포트 생성"""
        async with AsyncSessionLocal() as db:
            try:
                yesterday = datetime.utcnow().date() - timedelta(days=1)
                today = datetime.utcnow().date()
                
                # 신규 가입자 수
                new_users = await db.execute(
                    select(func.count(User.id)).filter(
                        and_(
                            User.created_at >= yesterday,
                            User.created_at < today
                        )
                    )
                )
                new_users_count = new_users.scalar() or 0
                
                # 활성 사용자 수 (트랜잭션 발생)
                active_users = await db.execute(
                    select(func.count(func.distinct(Transaction.user_id))).filter(
                        and_(
                            Transaction.created_at >= yesterday,
                            Transaction.created_at < today
                        )
                    )
                )
                active_users_count = active_users.scalar() or 0
                
                # 트랜잭션 통계
                tx_stats = await db.execute(
                    select(
                        Transaction.type,
                        func.count(Transaction.id),
                        func.sum(Transaction.amount)
                    ).filter(
                        and_(
                            Transaction.created_at >= yesterday,
                            Transaction.created_at < today,
                            Transaction.status == TransactionStatus.COMPLETED
                        )
                    ).group_by(Transaction.type)
                )
                
                tx_summary = {}
                total_volume = Decimal("0")
                for tx_type, count, volume in tx_stats:
                    tx_summary[tx_type] = {
                        "count": count,
                        "volume": str(volume or 0)
                    }
                    total_volume += volume or Decimal("0")
                
                # 총 잔고
                total_balance = await db.execute(
                    select(func.sum(Balance.amount))
                )
                total_balance = total_balance.scalar() or Decimal("0")
                
                # 리포트 생성
                report = f"""
📊 <b>Daily Report - {yesterday}</b>

👥 <b>Users</b>
• New signups: {new_users_count}
• Active users: {active_users_count}

💰 <b>Transactions</b>
• Total volume: {total_volume} USDT
• By type:
"""
                for tx_type, stats in tx_summary.items():
                    report += f"\n  - {tx_type}: {stats['count']} txs, {stats['volume']} USDT"
                
                report += f"\n\n💎 <b>Total Balance</b>: {total_balance} USDT"
                
                # 리포트 전송
                await alert_service.send_alert(
                    "Daily Report",
                    report,
                    AlertLevel.INFO,
                    "daily_report"
                )
                
                logger.info(f"Daily report generated for {yesterday}")
                
            except Exception as e:
                logger.error(f"Error generating daily report: {e}")
                await alert_service.send_alert(
                    "Daily Report Error",
                    f"Failed to generate daily report: {str(e)}",
                    AlertLevel.ERROR,
                    "daily_report_error"
                )
    
    async def run_forever(self):
        """매일 UTC 00:00에 실행"""
        while True:
            try:
                # 다음 자정까지 대기
                now = datetime.utcnow()
                next_midnight = (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_midnight - now).total_seconds()
                
                logger.info(f"Daily report task waiting {wait_seconds} seconds until next run")
                await asyncio.sleep(wait_seconds)
                
                # 리포트 생성
                await self.generate_daily_report()
                
            except Exception as e:
                logger.error(f"Error in daily report task: {e}")
                await asyncio.sleep(3600)  # 에러 시 1시간 후 재시도
```

### 7. 백그라운드 태스크 매니저 (app/core/background.py)

```python
import asyncio
from typing import List, Callable
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """백그라운드 태스크 관리자"""
    
    def __init__(self):
        self.tasks: List[asyncio.Task] = []
    
    def add_task(self, coro_func: Callable, name: str):
        """백그라운드 태스크 추가"""
        task = asyncio.create_task(coro_func())
        task.set_name(name)
        self.tasks.append(task)
        logger.info(f"Background task '{name}' started")
    
    async def startup(self):
        """애플리케이션 시작 시 태스크 실행"""
        from app.tasks.daily_report import DailyReportTask
        
        # 일일 리포트 태스크
        daily_report = DailyReportTask()
        self.add_task(daily_report.run_forever, "daily_report")
        
        # 추가 태스크들을 여기에 등록
        
    async def shutdown(self):
        """애플리케이션 종료 시 태스크 정리"""
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Background task '{task.get_name()}' cancelled")

# 글로벌 태스크 매니저
background_tasks = BackgroundTaskManager()
```

### 8. 메인 애플리케이션 업데이트 (app/main.py 수정)

메인 애플리케이션에 모니터링 미들웨어와 백그라운드 태스크 추가:

```python
# 기존 imports에 추가
from app.middleware.metrics import MetricsMiddleware
from app.core.background import background_tasks

# lifespan 함수 수정
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # 백그라운드 태스크 시작
    await background_tasks.startup()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # 백그라운드 태스크 종료
    await background_tasks.shutdown()

# 미들웨어 추가 (CORS 미들웨어 다음에)
app.add_middleware(MetricsMiddleware)

# 템플릿 디렉토리 생성 필요
import os
os.makedirs("app/templates", exist_ok=True)
```

### 9. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, balance, wallet, monitoring  # monitoring 추가

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])  # 추가

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 10. 환경 변수 추가 (.env)

```env
# 기존 변수들...

# Telegram Alerts
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
```

### 11. 설정 파일 업데이트 (app/core/config.py)

```python
class Settings(BaseSettings):
    # 기존 설정들...
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # 기존 설정 계속...
```

### 12. 의존성 추가 (pyproject.toml)

```toml
# dependencies 섹션에 추가
psutil = "^5.9.6"
aioredis = "^2.0.1"
jinja2 = "^3.1.2"
```

## 실행 및 검증

1. 의존성 설치:
   ```bash
   poetry add psutil aioredis jinja2
   ```

2. 서버 재시작:
   ```bash
   make dev
   ```

3. 모니터링 대시보드 접속:
   http://localhost:8000/api/v1/monitoring/dashboard

4. 알림 테스트:
   ```bash
   # 테스트 알림 전송
   curl -X POST http://localhost:8000/api/v1/monitoring/alerts/test \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"level": "info"}'
   ```

## 검증 포인트

- [ ] 메트릭이 정상적으로 수집되는가?
- [ ] 헬스체크가 모든 컴포넌트를 확인하는가?
- [ ] 모니터링 대시보드가 표시되는가?
- [ ] Telegram 알림이 전송되는가?
- [ ] 자동 알림이 임계값 초과 시 발송되는가?
- [ ] 일일 리포트가 생성되는가?
- [ ] 로그가 JSON 형식으로 저장되는가?
- [ ] 시스템 리소스 모니터링이 작동하는가?

이 문서를 완료하면 1인 운영에 필요한 기본적인 모니터링 시스템이 구축되며, 시스템 상태를 실시간으로 파악하고 문제 발생 시 즉시 알림을 받을 수 있습니다.