# 🚀 파트너 관리자 템플릿 개발 계획서

**작성일**: 2025년 7월 20일  
**프로젝트**: DantaroWallet 파트너 관리자 대시보드  
**문서 기반**: COMPREHENSIVE_DEVELOPMENT_PLAN.md 분석 결과

## 📊 **현재 개발 상황 (2025-07-20 기준)**

### ✅ **완성된 영역 (95-100%)**
- **백엔드 API 시스템**: 98% 완성 (24개 엔드포인트)
- **기본 UI 구조**: 95% 완성 (Sidebar, 레이아웃, 컴포넌트)
- **메인 대시보드**: 90% 완성 (page.tsx)
- **TronLink 연동**: 95% 완성 (WalletConnection.tsx)
- **에너지 위젯**: 95% 완성 (EnergyRentalWidget.tsx)

### ⚠️ **부분 완성 영역 (30-70%)**
- **API 클라이언트**: 60% 완성 (구조만 완성, 실제 연동 필요)
- **에너지 관리 페이지**: 70% 완성 (UI 완성, API 연동 필요)
- **출금 관리 페이지**: 60% 완성 (기본 UI, 고급 기능 미연동)
- **사용자 관리 페이지**: 50% 완성 (UI 구조, 데이터 연동 필요)
- **분석 페이지**: 40% 완성 (차트 구조, 실제 데이터 필요)

### ❌ **미구현 영역 (0-30%)**
- **Doc-28~31 고급 기능 페이지**: 0% 구현 (백엔드 완성, 프론트엔드 미구현)
- **실시간 WebSocket 연동**: 0% 구현
- **지갑/알림/설정 페이지**: 10-20% 구현 (기본 구조만)

---

## 🎯 **Phase별 개발 계획**

### **🔥 Phase 1: API 연동 완성 (1-2일) - 최우선**

#### **목표**: 기존 UI를 실제 백엔드 데이터와 연결

#### **1.1 API 클라이언트 완성 (0.5일)**
- **파일**: `src/lib/api.ts`
- **작업**: 
  - 실제 백엔드 엔드포인트 연결
  - 에러 처리 및 재시도 로직
  - 인증 토큰 관리
  - React Query 설정

#### **1.2 기존 페이지 API 연동 (1일)**

##### **에너지 관리 페이지** (`src/app/energy/page.tsx`)
- **백엔드**: `energy.py`, `energy_management.py`
- **연동 작업**: 
  - 실시간 에너지 모니터링 데이터
  - 에너지 풀 상태 정보
  - 사용량 통계 및 예측

##### **출금 관리 페이지** (`src/app/withdrawals/page.tsx`)
- **백엔드**: `withdrawal.py`, `withdrawal_management.py`
- **연동 작업**: 
  - 출금 요청 목록 및 상태
  - 기본 출금 승인 기능
  - 출금 이력 및 통계

##### **사용자 관리 페이지** (`src/app/users/page.tsx`)
- **백엔드**: `users.py`, `partners.py`
- **연동 작업**: 
  - 사용자 목록 및 검색
  - 사용자 상태 관리
  - 계정 정보 수정

##### **분석 페이지** (`src/app/analytics/page.tsx`)
- **백엔드**: `stats.py`, `transaction_analytics.py`
- **연동 작업**: 
  - 거래량 분석 데이터
  - 수익성 리포트
  - 실시간 통계 차트

#### **1.3 WebSocket 실시간 연동 (0.5일)**
- **파일**: `src/lib/websocket.ts` (신규 생성)
- **작업**: 
  - 실시간 대시보드 업데이트
  - 알림 시스템 연동
  - 에너지 모니터링 실시간 데이터

**완료 기준**: 모든 기존 페이지에서 실제 백엔드 데이터 표시

---

### **⚡ Phase 2: Doc-28~31 고급 기능 페이지 구현 (2-3일) - 긴급**

#### **목표**: 백엔드 완성된 고급 기능을 프론트엔드에서 활용

> **중요**: 모든 백엔드 API가 완성되어 있으므로 프론트엔드 구현만 필요

#### **2.1 출금 관리 고도화 (Doc-28) - 1일**

##### **출금 정책 설정 페이지** 
- **경로**: `/withdrawal-policy`
- **파일**: `src/app/withdrawal-policy/page.tsx` (신규)
- **백엔드**: `withdrawal_management.py` (완성됨)
- **기능**: 
  - 실시간/일괄 출금 정책 설정
  - 자동 승인 규칙 엔진 UI
  - 화이트리스트 및 한도 관리
  - 배치 스케줄 관리

##### **출금 자동화 관리 페이지**
- **경로**: `/withdrawal-automation`
- **파일**: `src/app/withdrawal-automation/page.tsx` (신규)
- **기능**: 
  - 자동 승인 규칙 설정
  - 조건부 승인 시스템
  - 자동화 로그 모니터링

#### **2.2 온보딩 자동화 (Doc-29) - 0.5일**

##### **온보딩 대시보드 페이지**
- **경로**: `/partner-onboarding`
- **파일**: `src/app/partner-onboarding/page.tsx` (신규)
- **백엔드**: `partner_onboarding.py` (완성됨)
- **기능**: 
  - 6단계 온보딩 진행률 추적
  - 체크리스트 및 검증 시스템
  - 자동화 워크플로우 설정
  - 템플릿 배포 관리

#### **2.3 감사 및 컴플라이언스 (Doc-30) - 0.5일**

##### **감사 모니터링 페이지**
- **경로**: `/audit-compliance`
- **파일**: `src/app/audit-compliance/page.tsx` (신규)
- **백엔드**: `audit_compliance.py` (완성됨)
- **기능**: 
  - 실시간 감사 로그 모니터링
  - AML/KYC 상태 확인
  - 의심 거래 알림 센터
  - 규제 보고서 생성

#### **2.4 에너지 렌탈 관리 (Doc-31) - 0.5일**

##### **에너지 렌탈 관리 페이지**
- **경로**: `/energy-rental-management`
- **파일**: `src/app/energy-rental-management/page.tsx` (신규)
- **백엔드**: `energy.py` (완성됨)
- **기능**: 
  - 렌탈 플랜 설정 및 변경
  - 실시간 사용량 모니터링
  - 비용 분석 및 예측
  - 자동 결제 설정

**완료 기준**: 모든 고급 기능을 프론트엔드에서 활용 가능

---

### **📱 Phase 3: 기본 페이지 완성 (1일) - 중요**

#### **3.1 기본 페이지 API 연동 완성**

##### **지갑 관리 페이지** (`src/app/wallet/page.tsx`)
- **백엔드**: `wallet.py`, `tronlink.py`
- **기능**: TronLink 연동, 지갑 잔액, 거래 내역

##### **알림 페이지** (`src/app/notifications/page.tsx`)  
- **백엔드**: 실시간 알림 시스템
- **기능**: 알림 목록, 설정, 필터링

##### **설정 페이지** (`src/app/settings/page.tsx`)
- **백엔드**: `partners.py`
- **기능**: 파트너 프로필, API 키, 보안 설정

**완료 기준**: 모든 사이드바 메뉴 정상 동작

---

### **🧪 Phase 4: 테스트 및 최적화 (1일) - 일반**

#### **4.1 통합 테스트**
- API 연동 테스트
- UI/UX 테스트
- 성능 최적화

#### **4.2 에러 처리 개선**
- 에러 바운더리 강화
- 로딩 상태 개선
- 오프라인 지원

**완료 기준**: 안정적인 프로덕션 준비 상태

---

## 📋 **개발 참고 문서 매핑**

### **Phase 1: API 연동**
```
API 클라이언트 구현 참고:
├── /docs/in_progress/copilot-doc-24.md (TronLink 연동)
├── /docs/in_progress/copilot-doc-25.md (파트너 관리)
├── /docs/in_progress/copilot-doc-26.md (에너지 풀)
└── /docs/in_progress/copilot-doc-27.md (수수료 최적화)

백엔드 API:
├── /dantarowallet/app/api/v1/endpoints/energy.py
├── /dantarowallet/app/api/v1/endpoints/withdrawal.py
├── /dantarowallet/app/api/v1/endpoints/users.py
└── /dantarowallet/app/api/v1/endpoints/stats.py
```

### **Phase 2: 고급 기능**
```
Doc-28 출금 관리 고도화:
├── 📋 참고: /docs/in_progress/copilot-doc-28.md ⭐
├── 🔧 API: /dantarowallet/app/api/v1/endpoints/withdrawal_management.py
└── 📊 모델: /dantarowallet/app/models/withdrawal_policy.py

Doc-29 온보딩 자동화:
├── 📋 참고: /docs/in_progress/copilot-doc-29.md ⭐
├── 🔧 API: /dantarowallet/app/api/v1/endpoints/partner_onboarding.py
└── 📊 모델: /dantarowallet/app/models/partner_onboarding.py

Doc-30 감사 컴플라이언스:
├── 📋 참고: /docs/in_progress/copilot-doc-30.md ⭐
├── 🔧 API: /dantarowallet/app/api/v1/endpoints/audit_compliance.py
└── 📊 모델: /dantarowallet/app/models/audit.py

Doc-31 에너지 렌탈:
├── 📋 참고: /docs/in_progress/copilot-doc-31(36).md ⭐
├── 🔧 API: /dantarowallet/app/api/v1/endpoints/energy.py
└── 📊 모델: /dantarowallet/app/models/energy_rental.py
```

---

## 🎯 **개발 성공 기준**

### **Phase 1 완료 기준**
- [x] 모든 기존 페이지에서 실제 백엔드 데이터 표시
- [x] WebSocket 실시간 데이터 업데이트 동작
- [x] 에러 없이 빌드 및 실행

### **Phase 2 완료 기준**
- [x] Doc-28~31 모든 고급 기능 페이지 정상 동작
- [x] 백엔드 API 완전 활용
- [x] 사이드바 네비게이션 완전 구현

### **Phase 3 완료 기준**
- [x] 모든 기본 페이지 완성
- [x] 전체 시스템 통합 동작

### **Phase 4 완료 기준**
- [x] 프로덕션 준비 완료
- [x] 모든 테스트 통과

---

## ⚠️ **개발 주의사항**

### **1. 문서 우선 개발**
- 각 Phase 시작 전 해당 copilot-doc 문서 숙지 필수
- 백엔드 API 스펙 정확히 파악
- 요구사항과 구현 결과 지속적 검증

### **2. 일관성 유지**
- 기존 컴포넌트 스타일 패턴 준수
- API 호출 및 에러 처리 방식 통일
- 디자인 시스템 컴포넌트 재사용

### **3. 점진적 개발**
- 각 기능 완성 후 즉시 테스트
- 단계별 커밋으로 진행 상황 추적
- 문제 발생 시 이전 단계로 롤백 가능

---

## 📈 **진행 상황 추적**

### **2025-07-20 기준**
- [x] 개발 계획 수립 완료
- [x] 현재 상황 분석 완료
- [ ] Phase 1: API 연동 (예정)
- [ ] Phase 2: 고급 기능 페이지 (예정)
- [ ] Phase 3: 기본 페이지 완성 (예정)
- [ ] Phase 4: 테스트 및 최적화 (예정)

### **다음 작업**
**Phase 1.1: API 클라이언트 완성** 시작

---

**📝 참고**: 이 문서는 실제 개발 진행에 따라 지속적으로 업데이트됩니다.
