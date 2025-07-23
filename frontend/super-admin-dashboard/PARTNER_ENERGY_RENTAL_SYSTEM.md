# 🔋 파트너 에너지 렌탈 시스템 개발 계획

**작성일**: 2025년 1월 22일
**목표**: 수퍼어드민이 외부 에너지 공급업체로부터 구매한 에너지를 파트너사에게 마진을 붙여 렌탈하는 완전한 비즈니스 시스템 구현

## 🎯 **비즈니스 모델**

```
외부 에너지 공급업체 → 수퍼어드민(본사) → 파트너사 → 최종 사용자
     [구매가격]      [마진 추가]    [파트너 마진]
```

### **수익 구조**
- **구매가**: 외부 공급업체에서 에너지 구매하는 원가
- **렌탈가**: 파트너사에게 판매하는 가격 (구매가 + 마진)
- **마진**: 본사의 수익 = 렌탈가 - 구매가

## 📊 **시스템 요구사항**

### **1. 에너지 구매 관리**
- 외부 공급업체별 구매 단가 관리
- 대량 구매 할인율 적용
- 구매 내역 추적

### **2. 파트너 에너지 할당**
- 파트너사별 에너지 할당량 설정
- 마진율 설정 (파트너 등급별 차등 적용)
- 렌탈 요금 자동 계산

### **3. 사용량 추적 및 정산**
- 파트너사별 실시간 에너지 사용량 모니터링
- 자동 정산 시스템 (선불/후불)
- 미납 관리

### **4. 수익성 분석**
- 실시간 마진 분석
- 파트너별 수익성 리포트
- 에너지 구매 vs 렌탈 수익 대시보드

## 🔧 **구현 계획**

### **Phase 1: 백엔드 API 개발**

#### **1.1 데이터 모델**
```python
# 파트너 에너지 할당
class PartnerEnergyAllocation(Base):
    partner_id: str
    allocated_amount: int        # 할당된 에너지량
    purchase_price: float        # 구매 단가
    markup_percentage: float     # 마진율
    rental_price: float         # 렌탈 단가
    billing_cycle: str          # 정산 주기
    status: str                 # active, suspended, expired

# 파트너 에너지 사용량
class PartnerEnergyUsage(Base):
    partner_id: str
    allocation_id: str
    used_amount: int            # 사용량
    usage_date: datetime
    cost: float                 # 사용 비용
    billing_status: str         # pending, billed, paid
```

#### **1.2 API 엔드포인트**
```
POST   /api/v1/partners/{partner_id}/energy/allocate     # 에너지 할당
GET    /api/v1/partners/{partner_id}/energy/allocations  # 할당 목록
POST   /api/v1/partners/{partner_id}/energy/usage        # 사용량 기록
GET    /api/v1/partners/{partner_id}/energy/usage        # 사용량 조회
GET    /api/v1/partners/{partner_id}/energy/billing      # 정산 정보
GET    /api/v1/admin/energy/revenue-analytics            # 수익 분석
PUT    /api/v1/admin/energy/pricing                      # 마진 설정
```

### **Phase 2: 프론트엔드 UI 개발**

#### **2.1 파트너 에너지 관리 페이지**
- `/partners/{id}/energy` - 파트너별 에너지 관리
- 에너지 할당 인터페이스
- 실시간 사용량 모니터링
- 정산 현황 대시보드

#### **2.2 수익성 분석 대시보드**
- `/energy/revenue-analytics` - 전체 수익 분석
- 마진율 설정 인터페이스
- 파트너별 수익성 비교
- 에너지 구매 vs 렌탈 수익 차트

#### **2.3 에너지 마진 관리**
- `/energy/pricing` - 마진 설정 페이지
- 파트너 등급별 차등 마진
- 동적 가격 조정
- 시장 가격 연동

### **Phase 3: 통합 테스트 및 최적화**

#### **3.1 백엔드 API 테스트**
- 에너지 할당 API 테스트
- 사용량 추적 정확성 검증
- 정산 로직 검증
- 수익성 계산 정확성 확인

#### **3.2 프론트엔드 통합 테스트**
- 모든 페이지 백엔드 연동 확인
- 실시간 데이터 동기화 테스트
- 에러 핸들링 검증

## 📅 **개발 일정**

### **Day 1: 백엔드 API 개발**
- [x] 개발 계획 수립
- [ ] 데이터 모델 생성
- [ ] API 엔드포인트 구현
- [ ] 비즈니스 로직 구현
- [ ] API 테스트

### **Day 2: 프론트엔드 UI 개발**
- [ ] 파트너 에너지 관리 페이지
- [ ] 수익성 분석 대시보드
- [ ] 마진 설정 인터페이스
- [ ] API 클라이언트 연동

### **Day 3: 통합 테스트 및 검증**
- [ ] 전체 시스템 통합 테스트
- [ ] 비즈니스 로직 검증
- [ ] 성능 최적화
- [ ] 문서화 완료

## 🔍 **핵심 비즈니스 로직**

### **마진 계산 공식**
```python
# 렌탈가 = 구매가 × (1 + 마진율)
rental_price = purchase_price * (1 + markup_percentage / 100)

# 총 수익 = (렌탈가 - 구매가) × 사용량
total_profit = (rental_price - purchase_price) * used_amount
```

### **파트너 등급별 차등 마진**
```python
partner_tier_margins = {
    'enterprise': 0.15,  # 15% 마진 (대기업)
    'business': 0.25,    # 25% 마진 (중소기업)
    'startup': 0.35      # 35% 마진 (스타트업)
}
```

## 🎯 **성공 지표**

### **기능적 목표**
- [ ] 파트너사별 에너지 할당 시스템 완성
- [ ] 실시간 사용량 추적 시스템 구축
- [ ] 자동 정산 시스템 구현
- [ ] 수익성 분석 대시보드 완성

### **비즈니스 목표**
- [ ] 마진율 기반 수익 최적화
- [ ] 파트너사별 차등 요금제 구현
- [ ] 실시간 수익성 모니터링
- [ ] 자동화된 정산 프로세스

---

**다음 단계**: Phase 1 백엔드 API 개발 시작
