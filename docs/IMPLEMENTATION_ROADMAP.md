# DantaroWalletPro 구현 로드맵

## 🎯 현재 상황 분석

### ✅ 구현 완료된 기능
- **사용자 인증/관리**: 로그인, 회원가입, 관리자 기능
- **지갑 관리**: TRON/USDT 지갑 생성, 조회
- **입출금 처리**: 입금/출금 기본 로직 및 모니터링
- **잔액 관리**: 조회, 조정, 내부 이체
- **트랜잭션 분석**: 통계, 로그, 대시보드
- **백업 시스템**: 자동 백업, 복원 기능

### ❌ 누락된 핵심 기능
1. **에너지 풀 관리 API** (모델만 존재, 엔드포인트 미구현)
2. **동적 수수료 관리 시스템** (고정 수수료만 구현)
3. **파트너사(화이트라벨) 관리** (완전 미구현)
4. **멀티테넌시 지원** (파트너사별 사용자 관리)
5. **실시간 알림 시스템** (에너지 부족, 수수료 변경 등)

---

## 🚀 단계별 구현 계획

### Phase 1: 에너지 풀 관리 시스템 (우선순위: 높음)
**목표**: TRON 에너지 풀을 효율적으로 관리하고 모니터링

#### 1.1 에너지 풀 관리 API 구현
```
📁 app/api/v1/endpoints/admin/energy.py
├── GET /admin/energy/pools - 에너지 풀 목록 조회
├── POST /admin/energy/pools - 새 에너지 풀 생성
├── PATCH /admin/energy/pools/{pool_id} - 풀 설정 업데이트
├── GET /admin/energy/pools/{pool_id}/stats - 풀 통계
└── GET /admin/energy/usage-logs - 에너지 사용 로그
```

#### 1.2 에너지 서비스 레이어 구현
```
📁 app/services/energy/
├── pool_manager.py - 에너지 풀 관리
├── usage_tracker.py - 사용량 추적
├── threshold_monitor.py - 임계값 모니터링
└── price_calculator.py - 에너지 가격 계산
```

#### 1.3 에너지 스키마 정의
```
📁 app/schemas/energy.py
├── EnergyPoolResponse
├── EnergyUsageLogResponse
├── EnergyStatsResponse
└── EnergyPoolUpdateRequest
```

### Phase 2: 동적 수수료 관리 시스템
**목표**: 실시간으로 수수료를 조정하고 관리

#### 2.1 수수료 설정 모델 구현
```python
# app/models/fee_config.py
class FeeConfig(Base):
    """동적 수수료 설정"""
    transaction_type: str  # 거래 유형
    base_fee: Decimal      # 기본 수수료
    percentage_fee: Decimal # 비율 수수료
    min_fee: Decimal       # 최소 수수료
    max_fee: Decimal       # 최대 수수료
    is_active: bool        # 활성 여부
    partner_id: Optional[int]  # 파트너사별 설정
```

#### 2.2 수수료 관리 API 구현
```
📁 app/api/v1/endpoints/admin/fees.py
├── GET /admin/fees/config - 수수료 설정 조회
├── POST /admin/fees/config - 수수료 설정 생성
├── PATCH /admin/fees/config/{config_id} - 설정 업데이트
├── GET /admin/fees/history - 수수료 변경 이력
└── POST /admin/fees/calculate - 수수료 미리 계산
```

#### 2.3 수수료 계산 서비스
```
📁 app/services/fee/
├── calculator.py - 동적 수수료 계산
├── config_manager.py - 설정 관리
└── history_tracker.py - 변경 이력 추적
```

### Phase 3: 파트너사 관리 시스템 (화이트라벨링)
**목표**: 멀티테넌시 지원으로 여러 파트너사 관리

#### 3.1 파트너사 모델 구현
```python
# app/models/partner.py
class Partner(Base):
    """파트너사 정보"""
    name: str              # 파트너사명
    domain: str            # 도메인
    api_key: str           # API 키
    webhook_url: str       # 웹훅 URL
    commission_rate: Decimal # 수수료율
    is_active: bool        # 활성 여부
    settings: JSON         # 커스텀 설정

class PartnerUser(Base):
    """파트너사별 사용자 매핑"""
    partner_id: int
    user_id: int
    partner_user_id: str   # 파트너사 내부 사용자 ID
```

#### 3.2 파트너사 관리 API
```
📁 app/api/v1/endpoints/admin/partners.py
├── GET /admin/partners - 파트너사 목록
├── POST /admin/partners - 파트너사 등록
├── PATCH /admin/partners/{partner_id} - 정보 수정
├── GET /admin/partners/{partner_id}/users - 파트너사 사용자
├── GET /admin/partners/{partner_id}/stats - 통계
└── POST /admin/partners/{partner_id}/webhook-test - 웹훅 테스트
```

#### 3.3 파트너 API (외부 연동)
```
📁 app/api/v1/endpoints/partner/
├── auth.py - 파트너 인증
├── users.py - 사용자 관리
├── transactions.py - 거래 조회
└── webhooks.py - 웹훅 수신
```

### Phase 4: 실시간 알림 및 모니터링
**목표**: 시스템 상태를 실시간으로 모니터링하고 알림

#### 4.1 알림 시스템 구현
```
📁 app/services/notification/
├── alert_manager.py - 알림 관리
├── email_service.py - 이메일 알림
├── webhook_service.py - 웹훅 알림
└── dashboard_service.py - 대시보드 실시간 업데이트
```

#### 4.2 모니터링 대상
- 에너지 풀 임계값 도달
- 수수료 변경 알림
- 대용량 거래 감지
- 시스템 에러 발생
- 파트너사 API 장애

---

## 🏗️ 기술적 구현 세부사항

### 1. 에너지 풀 관리 구현 예시

```python
# app/services/energy/pool_manager.py
class EnergyPoolManager:
    async def check_energy_availability(self, required_energy: int) -> bool:
        """에너지 충분성 검사"""
        
    async def consume_energy(self, pool_id: int, amount: int) -> bool:
        """에너지 소비 처리"""
        
    async def recharge_energy(self, pool_id: int, amount: int) -> bool:
        """에너지 충전 처리"""
        
    async def get_optimal_pool(self, required_energy: int) -> Optional[EnergyPool]:
        """최적 에너지 풀 선택"""
```

### 2. 동적 수수료 계산 구현 예시

```python
# app/services/fee/calculator.py
class FeeCalculator:
    async def calculate_withdrawal_fee(
        self, 
        amount: Decimal, 
        partner_id: Optional[int] = None
    ) -> Decimal:
        """출금 수수료 계산"""
        
    async def calculate_energy_fee(
        self, 
        energy_amount: int,
        current_price: Decimal
    ) -> Decimal:
        """에너지 사용 수수료 계산"""
```

### 3. 파트너사 인증 미들웨어

```python
# app/middleware/partner_auth.py
class PartnerAuthMiddleware:
    async def verify_partner_api_key(self, api_key: str) -> Optional[Partner]:
        """파트너 API 키 검증"""
        
    async def check_partner_permissions(
        self, 
        partner: Partner, 
        endpoint: str
    ) -> bool:
        """파트너 권한 확인"""
```

---

## 📊 데이터베이스 마이그레이션 계획

### 새로 추가할 테이블
1. **fee_configs** - 동적 수수료 설정
2. **fee_history** - 수수료 변경 이력
3. **partners** - 파트너사 정보
4. **partner_users** - 파트너사-사용자 매핑
5. **notifications** - 알림 로그
6. **system_alerts** - 시스템 경고

### 기존 테이블 수정
- **users**: partner_id 컬럼 추가
- **transactions**: partner_id, calculated_fee 컬럼 추가
- **energy_pools**: notification_sent 컬럼 추가

---

## 🎯 우선순위 및 타임라인

### 🔥 즉시 구현 (1-2주)
1. **에너지 풀 관리 API** - 현재 비어있는 엔드포인트 구현
2. **기본 수수료 관리** - 현재 하드코딩된 수수료를 설정 가능하게

### 📈 단기 구현 (3-4주)
3. **파트너사 기본 모델** - 멀티테넌시 기반 구축
4. **알림 시스템 기초** - 에너지 부족 알림

### 🚀 중기 구현 (1-2개월)
5. **완전한 파트너 API** - 외부 연동 지원
6. **고급 모니터링** - 실시간 대시보드

---

## 🔧 프론트엔드 연동 준비사항

### API 문서화
- **OpenAPI 스키마 업데이트** 필요
- **에러 코드 표준화** 필요
- **웹훅 이벤트 정의** 필요

### 상태 관리
- **에너지 부족 상태** 처리
- **수수료 변경 알림** 처리
- **파트너사별 UI 커스터마이징**

### 실시간 업데이트
- **WebSocket 연결** for 실시간 알림
- **Server-Sent Events** for 상태 변경

---

## 🎉 완성 후 기대 효과

1. **운영 효율성**: 에너지/수수료 자동 관리로 수동 개입 최소화
2. **확장성**: 파트너사 온보딩으로 비즈니스 확장 가능
3. **안정성**: 실시간 모니터링으로 장애 사전 방지
4. **수익성**: 동적 수수료로 수익 최적화

---

**다음 단계**: Phase 1부터 순차적으로 구현 시작
