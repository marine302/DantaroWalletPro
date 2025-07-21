# 외부 에너지 공급자 API 통합 - 백엔드 구현 요구사항

**작성일**: 2025년 7월 21일  
**우선순위**: 높음 🔥  
**예상 소요 시간**: 1-2주  
**담당**: 백엔드 개발팀

---

## 📋 **개요**

현재 프론트엔드에서 직접 외부 에너지 공급자 API를 호출하고 있어 보안, 성능, 관리 측면에서 문제가 발생하고 있습니다. 이를 백엔드로 이관하여 안전하고 효율적인 시스템을 구축해야 합니다.

## 🚨 **현재 문제점**

### 1. 보안 문제
- API 키가 프론트엔드에 노출됨
- 클라이언트 사이드에서 직접 외부 API 호출
- Rate limiting 우회 불가능

### 2. 성능 및 안정성
- 각 클라이언트마다 별도 API 호출
- 캐싱 불가능
- 네트워크 지연 시 UX 저하

### 3. 관리의 어려움
- API 키 로테이션 어려움
- 로그 및 모니터링 부족
- 오류 추적 어려움

---

## 🎯 **구현 요구사항**

### **1. API 엔드포인트 설계**

#### **1.1 공급자 관리**
```http
GET /api/v1/external-energy/providers
```
**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "id": "tronnrg-1",
      "name": "TronNRG Pool A",
      "status": "online",
      "pricePerEnergy": 0.0041,
      "availableEnergy": 5000000,
      "reliability": 99.2,
      "avgResponseTime": 1.8,
      "minOrderSize": 1000,
      "maxOrderSize": 10000000,
      "fees": {
        "tradingFee": 0.001,
        "withdrawalFee": 0.0005
      },
      "lastUpdated": "2025-07-21T10:30:00Z"
    }
  ]
}
```

```http
GET /api/v1/external-energy/providers/{provider_id}
```

```http
POST /api/v1/external-energy/providers/{provider_id}/refresh
```

#### **1.2 시장 데이터**
```http
GET /api/v1/external-energy/market/summary
```
**응답 예시:**
```json
{
  "success": true,
  "data": {
    "bestPrice": 0.0038,
    "bestProvider": "TronNRG Pool A",
    "totalProviders": 12,
    "activeProviders": 9,
    "avgPrice": 0.0042,
    "priceChange24h": -2.3,
    "totalVolume": 850000,
    "lastUpdated": "2025-07-21T10:30:00Z"
  }
}
```

```http
GET /api/v1/external-energy/market/prices/realtime
```

```http
WebSocket /ws/external-energy/prices
```
**WebSocket 메시지 형식:**
```json
{
  "type": "price_update",
  "providerId": "tronnrg-1",
  "price": 0.0041,
  "change24h": 2.5,
  "timestamp": "2025-07-21T10:30:00Z"
}
```

#### **1.3 주문 관리**
```http
POST /api/v1/external-energy/orders
```
**요청 예시:**
```json
{
  "providerId": "tronnrg-1",
  "amount": 1000000,
  "orderType": "market",
  "duration": 3,
  "priceLimit": 0.0042
}
```

```http
GET /api/v1/external-energy/orders/{order_id}
```

```http
GET /api/v1/external-energy/orders?page=1&limit=20&status=pending
```

---

## 🗄️ **데이터베이스 설계**

### **1. 공급자 테이블 (energy_providers)**
```sql
CREATE TABLE energy_providers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    status ENUM('online', 'offline', 'maintenance') DEFAULT 'online',
    reliability_score DECIMAL(5,2) DEFAULT 0.00,
    response_time_avg DECIMAL(8,2) DEFAULT 0.00,
    min_order_size BIGINT DEFAULT 0,
    max_order_size BIGINT DEFAULT 0,
    trading_fee DECIMAL(8,6) DEFAULT 0.000000,
    withdrawal_fee DECIMAL(8,6) DEFAULT 0.000000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### **2. 가격 히스토리 (energy_prices)**
```sql
CREATE TABLE energy_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider_id VARCHAR(50) NOT NULL,
    price DECIMAL(12,8) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TRX',
    available_energy BIGINT DEFAULT 0,
    volume_24h BIGINT DEFAULT 0,
    change_24h DECIMAL(8,4) DEFAULT 0.0000,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_provider_timestamp (provider_id, timestamp),
    FOREIGN KEY (provider_id) REFERENCES energy_providers(id)
);
```

### **3. 주문 관리 (energy_orders)**
```sql
CREATE TABLE energy_orders (
    id VARCHAR(50) PRIMARY KEY,
    provider_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    amount BIGINT NOT NULL,
    price DECIMAL(12,8) NOT NULL,
    total_cost DECIMAL(16,8) NOT NULL,
    order_type ENUM('market', 'limit') NOT NULL,
    status ENUM('pending', 'filled', 'cancelled', 'failed') DEFAULT 'pending',
    duration INT DEFAULT 1,
    trading_fee DECIMAL(16,8) DEFAULT 0.00000000,
    withdrawal_fee DECIMAL(16,8) DEFAULT 0.00000000,
    external_order_id VARCHAR(100),
    transaction_hash VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP NULL,
    INDEX idx_user_status (user_id, status),
    INDEX idx_provider_status (provider_id, status),
    FOREIGN KEY (provider_id) REFERENCES energy_providers(id)
);
```

---

## 🔧 **기술 구현 요구사항**

### **1. 외부 API 연동**

#### **1.1 TronNRG API 연동**
**참고 파일**: `frontend/super-admin-dashboard/src/services/tron-nrg-service.ts`

**주요 기능:**
- 실시간 가격 조회
- 공급자 정보 조회  
- 주문 생성 및 추적
- WebSocket 가격 스트림

**API 엔드포인트:**
```
GET https://api.tronnrg.com/v1/market/price
GET https://api.tronnrg.com/v1/market/data
GET https://api.tronnrg.com/v1/providers
POST https://api.tronnrg.com/v1/orders
WebSocket wss://api.tronnrg.com/v1/stream/price
```

#### **1.2 EnergyTron API 연동**
**참고 파일**: `frontend/super-admin-dashboard/src/services/energytron-service.ts`

**주요 기능:**
- 실시간 가격 및 가용 에너지 조회
- 공급자 정보 조회  
- 주문 생성 및 추적
- WebSocket 가격 및 가용 에너지 스트림

**API 엔드포인트:**
```
GET https://api.energytron.com/v1/market/data
GET https://api.energytron.com/v1/providers
POST https://api.energytron.com/v1/orders
WebSocket wss://api.energytron.com/v1/stream/price
```

#### **1.3 향후 추가 예정 공급자**
- JustLend Energy API
- P2P Energy Trading API
- 기타 에너지 거래소 API

### **2. 캐싱 전략**

#### **2.1 Redis 캐싱**
```python
# 실시간 가격 캐싱 (30초 TTL)
CACHE_KEY_PRICE = "energy:price:{provider_id}"
CACHE_TTL_PRICE = 30

# 공급자 정보 캐싱 (5분 TTL)
CACHE_KEY_PROVIDER = "energy:provider:{provider_id}"
CACHE_TTL_PROVIDER = 300

# 시장 요약 캐싱 (1분 TTL)
CACHE_KEY_MARKET_SUMMARY = "energy:market:summary"
CACHE_TTL_MARKET_SUMMARY = 60
```

#### **2.2 캐시 무효화 전략**
- 가격 업데이트 시 자동 무효화
- 공급자 상태 변경 시 무효화
- 수동 새로고침 API 제공

### **3. 백그라운드 작업**

#### **3.1 주기적 데이터 업데이트**
```python
# Celery 작업 예시
@celery.task
def update_energy_prices():
    """모든 공급자의 가격 정보 업데이트 (30초마다)"""
    
@celery.task
def update_provider_status():
    """공급자 상태 및 성능 지표 업데이트 (5분마다)"""
    
@celery.task
def process_pending_orders():
    """대기 중인 주문 상태 확인 및 업데이트 (1분마다)"""
```

#### **3.2 Cron 스케줄**
```bash
# 30초마다 가격 업데이트
*/30 * * * * python manage.py update_energy_prices

# 5분마다 공급자 상태 확인
*/5 * * * * python manage.py update_provider_status

# 1분마다 주문 상태 확인
* * * * * python manage.py process_pending_orders
```

### **4. WebSocket 구현**

#### **4.1 실시간 가격 브로드캐스트**
```python
# Django Channels 예시
class EnergyPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("energy_prices", self.channel_name)
        await self.accept()
    
    async def price_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
```

#### **4.2 주문 상태 알림**
```python
class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope['user'].id
        await self.channel_layer.group_add(f"orders_{user_id}", self.channel_name)
        await self.accept()
```

---

## 🔒 **보안 요구사항**

### **1. API 키 관리**
```python
# 암호화된 API 키 저장
from cryptography.fernet import Fernet

def encrypt_api_key(api_key: str) -> str:
    key = os.getenv('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    key = os.getenv('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.decrypt(encrypted_key.encode()).decode()
```

### **2. Rate Limiting**
```python
# Django Rate Limiting 예시
@ratelimit(key='ip', rate='100/h')
@ratelimit(key='user', rate='1000/h')
def energy_providers_view(request):
    pass
```

### **3. 입력값 검증**
```python
from marshmallow import Schema, fields, validate

class OrderCreateSchema(Schema):
    provider_id = fields.String(required=True, validate=validate.Length(max=50))
    amount = fields.Integer(required=True, validate=validate.Range(min=1))
    order_type = fields.String(validate=validate.OneOf(['market', 'limit']))
    price_limit = fields.Decimal(validate=validate.Range(min=0), allow_none=True)
```

---

## 📊 **모니터링 및 로깅**

### **1. 로깅 요구사항**
```python
import logging

# API 호출 로깅
logger.info(f"External API call: {provider_id} - {endpoint}")

# 에러 로깅
logger.error(f"API call failed: {provider_id} - {error}")

# 주문 로깅
logger.info(f"Order created: {order_id} - User: {user_id}")
```

### **2. 메트릭 수집**
- API 응답 시간
- 성공/실패율
- 공급자별 성능 지표
- 주문 처리 시간

---

## 🚀 **마이그레이션 계획**

### **Phase 1: 백엔드 API 구현 (1주)**
1. 데이터베이스 테이블 생성
2. 기본 CRUD API 구현
3. TronNRG API 연동
4. 캐싱 시스템 구축

### **Phase 2: 프론트엔드 연동 (3-5일)**
1. 기존 `tron-nrg-service.ts` 수정
2. 백엔드 API 호출로 변경
3. WebSocket 연결 구현
4. 에러 핸들링 개선

### **Phase 3: 추가 공급자 연동 (1주)**
1. JustLend API 연동
2. P2P Energy API 연동
3. 공급자 비교 기능 강화

---

## 📁 **참고 파일**

### **프론트엔드 파일 (구현 참고용)**
- `frontend/super-admin-dashboard/src/services/tron-nrg-service.ts` - 기존 TronNRG API 구현
- `frontend/super-admin-dashboard/src/app/energy/external-market/page.tsx` - 공급자 목록 페이지
- `frontend/super-admin-dashboard/src/app/energy/external-market/purchase/page.tsx` - 주문 로직
- `frontend/super-admin-dashboard/src/services/energytron-service.ts` - EnergyTron API 구현

### **백엔드 파일 (기존 구조)**
- `dantarowallet/app/services/external_energy_service.py` - 기존 외부 에너지 서비스
- `dantarowallet/app/api/` - API 엔드포인트 구현 위치

---

## ✅ **완료 체크리스트**

### **백엔드 구현**
- [ ] 데이터베이스 테이블 생성
- [ ] 공급자 관리 API 구현
- [ ] 시장 데이터 API 구현
- [ ] 주문 관리 API 구현
- [ ] TronNRG API 연동
- [ ] EnergyTron API 연동
- [ ] 캐싱 시스템 구현
- [ ] WebSocket 실시간 업데이트
- [ ] 백그라운드 작업 구현
- [ ] 보안 및 인증 구현
- [ ] 로깅 및 모니터링 구현

### **프론트엔드 수정**
- [ ] API 서비스 수정
- [ ] 에러 핸들링 개선
- [ ] WebSocket 연결 구현
- [ ] 테스트 및 검증

### **배포 및 운영**
- [ ] 환경변수 설정
- [ ] Redis 설정
- [ ] Celery 워커 설정
- [ ] 모니터링 대시보드 구성

---

**문의사항이나 추가 요구사항이 있으면 프론트엔드 팀과 협의 후 진행해주세요.**

**연락처**: 프론트엔드 개발팀  
**문서 최종 수정일**: 2025년 7월 21일
