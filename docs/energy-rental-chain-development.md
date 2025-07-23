# 🔋 에너지 렌탈 체인 API 개발 문서

**개발 일자**: 2025년 7월 24일  
**개발자**: GitHub Copilot  
**목적**: 수퍼어드민 → 파트너 → 사용자 에너지 렌탈 체인 구현

## 📋 개발 개요

### 비즈니스 플로우
1. **수퍼어드민**: 외부 에너지 공급업체에서 에너지 구매 → 마진 추가 → 파트너에게 렌탈
2. **파트너어드민**: 수퍼어드민에서 에너지 렌탈 → 사용자 출금 시 자동 제공
3. **사용자**: 출금 신청 → 자동 에너지 할당 받음 → 수수료는 USDT로 지불

### 문제점 식별
- 역할별 API 구분 없음 (수퍼어드민 vs 파트너어드민)
- 출금 시 에너지 자동 전송 로직 누락
- 에너지 공급업체 관리 API 부재
- 권한 검증 로직 부재

---

## 🛠️ 개발 내용

### 1. 새로운 API 라우터 생성

#### 1.1 수퍼어드민 전용 라우터
**파일**: `app/api/v1/endpoints/admin/energy_rental.py`

```python
# 수퍼어드민 전용 에너지 렌탈 관리 API
router = APIRouter(prefix="/admin/energy-rental", tags=["admin-energy-rental"])

# 구현된 엔드포인트:
POST /admin/energy-rental/providers          # 에너지 공급업체 등록
GET  /admin/energy-rental/providers          # 공급업체 목록 조회
POST /admin/energy-rental/purchase           # 외부에서 에너지 구매
POST /admin/energy-rental/partners/allocate  # 파트너별 에너지 할당
GET  /admin/energy-rental/partners/{partner_id}/usage  # 파트너 사용량 조회
POST /admin/energy-rental/margin             # 마진율 설정
GET  /admin/energy-rental/analytics          # 전체 분석 데이터
```

#### 1.2 파트너어드민 전용 라우터
**파일**: `app/api/v1/endpoints/partner/energy_rental.py`

```python
# 파트너어드민 전용 에너지 렌탈 API
router = APIRouter(prefix="/partner/energy-rental", tags=["partner-energy-rental"])

# 구현된 엔드포인트:
POST /partner/energy-rental/rent             # 수퍼어드민에서 에너지 렌탈
GET  /partner/energy-rental/balance          # 현재 에너지 잔액 조회
GET  /partner/energy-rental/usage-history    # 사용 이력 조회
GET  /partner/energy-rental/billing          # 청구서 조회
POST /partner/energy-rental/auto-allocation  # 자동 할당 설정
```

### 2. 출금 서비스 개선

#### 2.1 에너지 자동 할당 로직 추가
**파일**: `app/services/withdrawal/request_service.py`

**기존 코드**:
```python
async def create_withdrawal_request(...):
    # 잔고 확인, 수수료 계산만 있음
```

**개선된 코드**:
```python
async def create_withdrawal_request(...):
    # 1. 잔고 확인 (USDT)
    # 2. 수수료 계산 (USDT) - 기존 유지
    # 3. 파트너 에너지 잔여량 확인 - 신규 추가
    # 4. 에너지 자동 할당/전송 - 신규 추가
    # 5. 출금 처리
    
    # 새로 추가된 로직:
    await self._ensure_energy_for_withdrawal(partner_id, withdrawal_amount)
```

#### 2.2 새로운 메서드 추가
```python
async def _ensure_energy_for_withdrawal(self, partner_id: int, amount: Decimal):
    """출금을 위한 에너지 확보 및 자동 할당"""
    
async def _calculate_required_energy(self, amount: Decimal) -> int:
    """출금 금액에 따른 필요 에너지 계산"""
    
async def _allocate_energy_to_user(self, user_id: int, energy_amount: int):
    """사용자에게 에너지 자동 할당"""
```

### 3. 에너지 렌탈 서비스 확장

#### 3.1 EnergyRentalService 새로운 메서드
**파일**: `app/services/energy_rental_service.py`

```python
# 수퍼어드민 관련
def register_energy_provider(self, name: str, api_endpoint: str, ...)
def purchase_energy_from_provider(self, provider_id: int, amount: int, ...)
def set_partner_energy_allocation(self, partner_id: int, amount: int, ...)
def get_partner_energy_usage(self, partner_id: int, ...)
def set_energy_margin_rate(self, rate: Decimal)

# 파트너어드민 관련
def rent_energy_from_admin(self, partner_id: int, amount: int, ...)
def get_partner_energy_balance(self, partner_id: int)
def get_partner_usage_history(self, partner_id: int, ...)
def get_partner_billing_info(self, partner_id: int, ...)

# 자동 할당 관련
def auto_allocate_energy_for_withdrawal(self, partner_id: int, user_id: int, amount: int)
def calculate_energy_needed_for_amount(self, withdrawal_amount: Decimal) -> int
```

### 4. 권한 검증 시스템

#### 4.1 인증 함수 생성
**파일**: `app/api/deps.py`

```python
async def get_current_super_admin(token: str = Depends(oauth2_scheme)) -> Admin:
    """수퍼어드민 권한 검증"""
    
async def get_current_partner_admin(token: str = Depends(oauth2_scheme)) -> PartnerAdmin:
    """파트너어드민 권한 검증"""
    
async def get_partner_id_from_token(token: str = Depends(oauth2_scheme)) -> int:
    """토큰에서 파트너 ID 추출"""
```

### 5. 라우터 등록

#### 5.1 메인 API 라우터 수정
**파일**: `app/api/v1/api.py`

```python
# 기존
from app.api import energy_rental

# 신규 추가
from app.api.v1.endpoints.admin import energy_rental as admin_energy_rental
from app.api.v1.endpoints.partner import energy_rental as partner_energy_rental

# 라우터 등록
api_router.include_router(admin_energy_rental.router, prefix="/api/v1")
api_router.include_router(partner_energy_rental.router, prefix="/api/v1")
api_router.include_router(energy_rental.router, prefix="/api/v1")  # 기존 유지
```

---

## 📊 데이터베이스 모델 영향

### 기존 모델 활용
- `EnergyRentalPlan` - 렌탈 플랜 정보
- `EnergyAllocation` - 에너지 할당 정보  
- `EnergyUsageRecord` - 사용 기록
- `EnergyBilling` - 청구 정보

### 새로 필요한 필드/모델
```python
# 에너지 공급업체 모델 (신규 필요)
class EnergyProvider(Base):
    id: int
    name: str
    api_endpoint: str
    api_key: str
    status: str
    
# 마진율 설정 모델 (신규 필요)  
class EnergyMarginConfig(Base):
    id: int
    partner_id: int
    margin_rate: Decimal
    effective_from: datetime
```

---

## 🧪 테스트 계획

### 1. 단위 테스트
- [ ] 수퍼어드민 API 엔드포인트 테스트
- [ ] 파트너어드민 API 엔드포인트 테스트  
- [ ] 에너지 자동 할당 로직 테스트
- [ ] 권한 검증 테스트

### 2. 통합 테스트
- [ ] 전체 에너지 렌탈 체인 플로우 테스트
- [ ] 출금 시 에너지 자동 전송 테스트
- [ ] 마진 계산 및 청구 테스트

### 3. API 테스트
```bash
# 수퍼어드민 테스트
curl -X POST /api/v1/admin/energy-rental/providers
curl -X POST /api/v1/admin/energy-rental/purchase
curl -X POST /api/v1/admin/energy-rental/partners/allocate

# 파트너어드민 테스트  
curl -X POST /api/v1/partner/energy-rental/rent
curl -X GET /api/v1/partner/energy-rental/balance
curl -X GET /api/v1/partner/energy-rental/billing

# 출금 시 자동 할당 테스트
curl -X POST /api/v1/withdrawals/request
```

---

## 🔄 다음 단계

### 즉시 필요한 작업
1. [ ] 새로운 데이터베이스 모델 생성 및 마이그레이션
2. [ ] 실제 에너지 공급업체 API 연동 (TronNRG, EnergyTron 등)
3. [ ] 프론트엔드 API 경로 업데이트
4. [ ] 통합 테스트 작성 및 실행

### 장기 개선 사항
1. [ ] 에너지 사용량 예측 및 자동 리밸런싱
2. [ ] 실시간 에너지 가격 모니터링
3. [ ] 에너지 사용 패턴 분석 및 최적화
4. [ ] 다중 에너지 공급업체 지원

---

## ⚠️ 주의사항

### 보안
- 에너지 공급업체 API 키 안전한 저장 필요
- 파트너별 에너지 할당량 검증 강화
- 출금 시 에너지 할당 한도 체크

### 성능
- 에너지 자동 할당 시 지연 최소화
- 대량 출금 요청 시 에너지 풀 관리
- 실시간 에너지 잔액 조회 최적화

### 모니터링
- 에너지 공급업체별 응답 시간 모니터링  
- 파트너별 에너지 사용량 이상 패턴 감지
- 에너지 할당 실패율 추적

---

**개발 완료 일자**: 2025년 7월 24일  
**리뷰 필요**: 프론트엔드 팀과 API 스펙 조율  
**배포 예정**: 테스트 완료 후 staging 환경 배포
