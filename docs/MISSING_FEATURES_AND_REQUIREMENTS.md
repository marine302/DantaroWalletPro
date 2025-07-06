# DantaroWalletPro - 누락된 기능 및 추가 요구사항

## 🚨 핵심 비즈니스 로직 누락사항

### ⚡ 에너지 부족 대응 시나리오
**문제**: 본사가 TRX 스테이킹을 하지 않은 초기 단계 또는 에너지 부족 상황에서 서비스 중단 방지 필요

**해결책**:
1. **사용자에게 TRX 직접 전송** 옵션 제공
2. **대기열 시스템** 구현 (에너지 회복까지 대기)
3. **에너지 임계값 기반 알림** 시스템

### 🏢 화이트라벨링 멀티테넌시
**문제**: 파트너사별 사용자 풀, 수수료, 브랜딩 관리 시스템 완전 누락

**해결책**:
- 파트너사 모델 및 관리 시스템 구현
- 파트너별 사용자 매핑 및 권한 관리
- 파트너별 수수료 차별화
- API 키 기반 파트너 인증

### 💰 동적 수수료 관리
**문제**: 현재 하드코딩된 고정 수수료만 지원, 관리자가 실시간 조정 불가

**해결책**:
- 데이터베이스 기반 수수료 설정 테이블
- 파트너별/거래유형별 수수료 차별화
- 에너지 상태 기반 수수료 조정

---

## 📋 백엔드 API 누락 기능

### 🔋 TRON 에너지 풀 관리 API
**현재 상태**: 모델(`EnergyPool`, `EnergyUsageLog`, `EnergyPriceHistory`)은 존재하지만 API 엔드포인트 미구현

**필요한 엔드포인트**:
```
📁 /api/v1/admin/energy/ (❌ 현재 빈 파일)
├── GET /status - 에너지 풀 현황
├── POST /create-pool - 에너지 풀 생성  
├── GET /usage-stats - 에너지 사용 통계
├── GET /usage-logs - 에너지 사용 로그
├── POST /record-price - 에너지 가격 기록
├── GET /price-history - 가격 히스토리
├── POST /simulate-usage - 에너지 사용량 시뮬레이션
└── PUT /auto-manage - 자동 에너지 관리 설정
```

### ⚡ 에너지 부족 대응 API (신규 추가 필요)
```
📁 /api/v1/energy/ (❌ 완전 미구현)
├── GET /status - 현재 에너지 상태 확인
├── POST /emergency-withdrawal - TRX 직접 결제 출금
├── GET /queue-position - 대기열 위치 조회
├── POST /notify-shortage - 에너지 부족 알림
└── GET /trx-fee-estimate - TRX 수수료 견적
```
- 파트너사별 통계 및 정산

## 📋 추가 개발 필요 사항

### Phase A: 에너지 부족 시 대응 로직
```python
# 에너지 부족 시 처리 로직
class EnergyFallbackService:
    async def handle_insufficient_energy(self, withdrawal_request):
        if energy_pool.insufficient():
            # 옵션 1: 사용자에게 TRX 수수료 부과
            return await self.charge_trx_fee(withdrawal_request)
            # 옵션 2: 본사가 임시 TRX 수수료 지불
            return await self.company_pays_trx(withdrawal_request)
```

### Phase B: 수수료 관리 시스템
```python
# 수수료 설정 모델
class FeeConfig:
    partner_id: Optional[int]  # 파트너사별 수수료
    fee_type: str             # "withdrawal", "internal_transfer"
    asset: str                # "USDT", "TRX"
    fee_mode: str             # "percentage", "fixed"
    fee_value: Decimal        # 수수료 값
    is_active: bool
```

### Phase C: 파트너사 관리 시스템
```python
# 파트너사 모델
class Partner:
    partner_code: str         # 고유 파트너 코드
    company_name: str         # 회사명
    api_key: str             # API 인증키
    webhook_url: str         # 콜백 URL
    fee_tier: str           # 수수료 등급
    is_active: bool
    
# 사용자-파트너 연결
class User:
    # ...existing fields...
    partner_id: Optional[int]  # 소속 파트너사
```

## 🔧 백엔드 API 추가 구현

### 1. 수수료 관리 엔드포인트
```python
# app/api/v1/endpoints/admin/fees.py
@router.get("/current")
async def get_current_fees():
    """현재 수수료 설정 조회"""
    
@router.put("/internal")
async def update_internal_fees(fee_config: FeeConfigUpdate):
    """내부 수수료율 설정"""
    
@router.get("/energy-cost") 
async def get_energy_cost():
    """실시간 에너지 비용 조회"""
```

### 2. 에너지 풀 관리 엔드포인트
```python
# app/api/v1/endpoints/admin/energy.py
@router.get("/status")
async def get_energy_status():
    """에너지 풀 현황"""
    
@router.post("/create-pool")
async def create_energy_pool(pool_config: EnergyPoolConfig):
    """에너지 풀 생성"""
    
@router.get("/usage-stats")
async def get_energy_usage_stats():
    """에너지 사용 통계"""
```

### 3. 파트너사 관리 엔드포인트
```python
# app/api/v1/endpoints/admin/partners.py
@router.get("/")
async def get_partners():
    """파트너사 목록"""
    
@router.post("/")
async def create_partner(partner_data: PartnerCreate):
    """파트너사 등록"""
    
@router.get("/{partner_id}/users")
async def get_partner_users(partner_id: int):
    """파트너사 사용자 목록"""
    
@router.get("/{partner_id}/stats")
async def get_partner_stats(partner_id: int):
    """파트너사 통계"""
```

### 4. 사용자용 수수료 조회 엔드포인트
```python
# app/api/v1/endpoints/fees.py
@router.get("/estimate")
async def get_fee_estimate(amount: Decimal, currency: str):
    """출금 수수료 견적"""
    
@router.get("/current")
async def get_current_user_fees():
    """현재 사용자 수수료율"""
    
@router.get("/explanation")
async def get_fee_explanation():
    """수수료 체계 설명"""
```

### 💰 수수료 관리 API (신규 추가 필요)
```
📁 /api/v1/admin/fees/ (❌ 현재 빈 파일)  
├── GET /config - 현재 수수료 설정 조회
├── POST /config - 새 수수료 설정 생성
├── PATCH /config/{id} - 수수료 설정 수정
├── GET /history - 수수료 변경 이력
├── POST /calculate - 수수료 미리 계산
└── PUT /partner/{partner_id} - 파트너별 수수료 설정
```

### 🏢 파트너사 관리 API (신규 추가 필요)
```
📁 /api/v1/admin/partners/ (❌ 완전 미구현)
├── GET / - 파트너사 목록
├── POST / - 파트너사 등록
├── PATCH /{partner_id} - 파트너사 정보 수정
├── GET /{partner_id}/users - 파트너사 사용자 목록
├── GET /{partner_id}/stats - 파트너사별 통계
├── PUT /{partner_id}/fees - 파트너별 수수료 설정
└── PUT /{partner_id}/branding - 파트너별 UI 설정
```

### 🏢 파트너 API (외부 연동용, 신규 추가 필요)
```
📁 /api/v1/partner/ (❌ 완전 미구현)
├── POST /auth - 파트너 API 키 인증
├── GET /users - 파트너사 사용자 조회
├── POST /users - 파트너사 사용자 생성
├── GET /transactions - 파트너사 거래 내역
└── POST /webhook - 웹훅 수신
```

---

## 🗃️ 데이터베이스 모델 누락사항

### 새로 추가해야 할 테이블

#### 1. 수수료 설정 테이블
```sql
CREATE TABLE fee_configs (
    id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(50) NOT NULL, -- 'withdrawal', 'deposit', etc
    base_fee DECIMAL(18,8) NOT NULL,       -- 기본 수수료
    percentage_fee DECIMAL(5,4) NOT NULL,  -- 비율 수수료 (0.02 = 2%)
    min_fee DECIMAL(18,8) NOT NULL,        -- 최소 수수료
    max_fee DECIMAL(18,8) NOT NULL,        -- 최대 수수료
    partner_id INTEGER,                     -- NULL이면 글로벌 설정
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. 수수료 변경 이력 테이블  
```sql
CREATE TABLE fee_history (
    id SERIAL PRIMARY KEY,
    fee_config_id INTEGER NOT NULL,
    old_values JSONB,                      -- 이전 설정값
    new_values JSONB,                      -- 새 설정값
    changed_by INTEGER NOT NULL,           -- 변경한 관리자 ID
    change_reason VARCHAR(500),            -- 변경 사유
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. 파트너사 테이블
```sql
CREATE TABLE partners (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,            -- 파트너사명
    domain VARCHAR(255),                   -- 도메인
    api_key VARCHAR(255) UNIQUE NOT NULL,  -- API 키
    api_secret VARCHAR(255) NOT NULL,      -- API 시크릿
    webhook_url VARCHAR(500),              -- 웹훅 URL
    commission_rate DECIMAL(5,4) DEFAULT 0, -- 수수료율
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',           -- 커스텀 설정
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. 파트너-사용자 매핑 테이블
```sql
CREATE TABLE partner_users (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    partner_user_id VARCHAR(255),          -- 파트너사 내부 사용자 ID  
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(partner_id, user_id),
    UNIQUE(partner_id, partner_user_id)
);
```

#### 5. 시스템 알림 테이블
```sql
CREATE TABLE system_notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,             -- 'energy_low', 'fee_change', etc
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',   -- 'info', 'warning', 'error'
    is_read BOOLEAN DEFAULT false,
    target_user_id INTEGER,                -- NULL이면 모든 관리자
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 기존 테이블 수정사항

#### 1. users 테이블에 파트너 정보 추가
```sql
ALTER TABLE users ADD COLUMN partner_id INTEGER;
ALTER TABLE users ADD CONSTRAINT fk_users_partner 
    FOREIGN KEY (partner_id) REFERENCES partners(id);
```

#### 2. transactions 테이블에 파트너 및 수수료 정보 추가
```sql
ALTER TABLE transactions ADD COLUMN partner_id INTEGER;
ALTER TABLE transactions ADD COLUMN calculated_fee DECIMAL(18,8);
ALTER TABLE transactions ADD COLUMN fee_config_id INTEGER;
```

#### 3. energy_pools 테이블에 알림 관련 컬럼 추가
```sql
ALTER TABLE energy_pools ADD COLUMN last_alert_sent TIMESTAMP;
ALTER TABLE energy_pools ADD COLUMN alert_threshold_90 BOOLEAN DEFAULT false;
ALTER TABLE energy_pools ADD COLUMN alert_threshold_95 BOOLEAN DEFAULT false;
```

---

## 🔧 서비스 레이어 누락사항

### 1. 에너지 관리 서비스
```
📁 app/services/energy/
├── pool_manager.py - 에너지 풀 생성/관리
├── usage_tracker.py - 에너지 사용량 추적  
├── threshold_monitor.py - 임계값 모니터링
├── price_calculator.py - 에너지 가격 계산
└── emergency_handler.py - 에너지 부족 대응
```

### 2. 수수료 관리 서비스
```
📁 app/services/fee/
├── calculator.py - 동적 수수료 계산
├── config_manager.py - 수수료 설정 관리
├── history_tracker.py - 변경 이력 추적
└── partner_fee_manager.py - 파트너별 수수료
```

### 3. 파트너사 관리 서비스
```
📁 app/services/partner/
├── partner_manager.py - 파트너사 생성/관리
├── user_mapper.py - 사용자 매핑 관리
├── api_auth.py - 파트너 API 인증
├── webhook_handler.py - 웹훅 처리
└── analytics.py - 파트너별 분석
```

### 4. 알림 서비스
```
📁 app/services/notification/
├── alert_manager.py - 시스템 알림 관리
├── email_service.py - 이메일 알림
├── webhook_service.py - 웹훅 알림
└── dashboard_updates.py - 실시간 대시보드 업데이트
```

---

## 🎯 우선순위별 구현 계획

### Phase 1: 즉시 구현 필요 (운영에 필수)
1. **에너지 부족 대응 시스템**
   - TRX 직접 결제 출금 옵션
   - 에너지 상태 확인 API
   
2. **기본 수수료 관리**
   - 관리자 수수료 설정 API
   - 동적 수수료 계산

### Phase 2: 단기 구현 (1-2주)
3. **파트너사 기본 관리**
   - 파트너사 등록/관리 API
   - 기본 멀티테넌시 지원

4. **에너지 풀 관리 완성**
   - 전체 에너지 관리 API 구현
   - 모니터링 및 알림

### Phase 3: 중기 구현 (3-4주)  
5. **고급 파트너 기능**
   - 파트너별 수수료 차별화
   - 파트너 API 및 웹훅

6. **실시간 알림 시스템**
   - 시스템 상태 모니터링
   - 관리자 대시보드 실시간 업데이트

---

## 📈 예상 개발 리소스

### 백엔드 개발 (FastAPI/Python)
- **에너지 관리**: 3-5일
- **수수료 시스템**: 2-3일  
- **파트너사 관리**: 5-7일
- **알림 시스템**: 2-3일
- **테스트 및 통합**: 3-5일

### 프론트엔드 개발 (Next.js/React)
- **관리자 대시보드**: 5-7일
- **사용자 UI 업데이트**: 3-4일
- **실시간 기능**: 2-3일

### 데이터베이스
- **마이그레이션 작성**: 1일
- **데이터 이전**: 1-2일

**총 예상 개발 기간**: 3-4주 (1명 기준)

---

## ⚠️ 리스크 및 고려사항

### 기술적 리스크
1. **멀티테넌시 복잡성**: 파트너별 데이터 분리 및 보안
2. **실시간 처리**: 에너지 상태 모니터링 성능
3. **트랜잭션 무결성**: 수수료 계산 및 적용 과정

### 운영 리스크  
1. **에너지 부족 시나리오**: 사용자 경험 저하 가능성
2. **파트너사 온보딩**: 초기 설정 및 지원 복잡성
3. **수수료 변경**: 사용자 혼란 및 고객 문의 증가

### 보안 고려사항
1. **파트너 API 키 관리**: 안전한 키 생성 및 저장
2. **권한 분리**: 파트너별 데이터 접근 제어
3. **감사 로그**: 모든 수수료/설정 변경 추적

---

이제 **모든 누락된 기능과 구현 방향**이 명확히 정리되었습니다!
