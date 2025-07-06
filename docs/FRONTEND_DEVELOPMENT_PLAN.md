# DantaroWallet Pro - 프론트엔드 개발 계획

## 📊 백엔드 구조 분석 결과

### 🔌 API 엔드포인트 정리

#### 🔑 인증 관련 (사용자 공통)
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/refresh` - 토큰 갱신
- `GET /api/v1/auth/me` - 사용자 정보 조회
- `PUT /api/v1/auth/password` - 비밀번호 변경

#### 👤 사용자 페이지 API
**잔액 관리**
- `GET /api/v1/balance/` - 잔액 조회
- `POST /api/v1/balance/transfer` - 내부 이체
- `GET /api/v1/balance/transactions` - 거래 내역

**지갑 관리**
- `POST /api/v1/wallet/create` - 지갑 생성
- `GET /api/v1/wallet/` - 지갑 정보 조회
- `GET /api/v1/wallet/transactions` - 지갑 거래 내역

**입금**
- `POST /api/v1/deposit/request` - 입금 요청
- `GET /api/v1/deposit/` - 입금 내역
- `GET /api/v1/deposit/{deposit_id}` - 입금 상세 조회

**출금**
- `POST /api/v1/withdrawals/` - 출금 요청
- `GET /api/v1/withdrawals/` - 출금 내역
- `GET /api/v1/withdrawals/{withdrawal_id}` - 출금 상세 조회
- `DELETE /api/v1/withdrawals/{withdrawal_id}` - 출금 취소

**💰 수수료 정보** ⭐️ **핵심 기능**
- `GET /api/v1/fees/estimate` - 출금 수수료 견적 (USDT 기준) ❌ **구현필요**
- `GET /api/v1/fees/current` - 현재 내부 수수료율 조회 ❌ **구현필요**
- `GET /api/v1/fees/explanation` - 수수료 체계 설명 ❌ **구현필요**

**대시보드**
- `GET /api/v1/dashboard/overview` - 대시보드 개요
- `GET /api/v1/dashboard/recent-transactions` - 최근 거래
- `GET /api/v1/dashboard/balance-history` - 잔액 히스토리
- `GET /api/v1/dashboard/wallet-stats` - 지갑 통계

#### 🛠️ 관리자 페이지 API
**시스템 관리**
- `GET /api/v1/admin/stats` - 시스템 통계
- `GET /api/v1/admin/users` - 사용자 목록
- `GET /api/v1/admin/users/{user_id}` - 사용자 상세 정보
- `PUT /api/v1/admin/users/{user_id}` - 사용자 정보 수정

**거래 관리**
- `GET /api/v1/admin/transactions` - 전체 거래 내역
- `GET /api/v1/admin/suspicious-activities` - 의심스러운 활동

**출금 관리**
- `GET /api/v1/withdrawals/admin/pending` - 대기 중인 출금
- `POST /api/v1/withdrawals/{withdrawal_id}/review` - 출금 검토
- `POST /api/v1/withdrawals/{withdrawal_id}/approve` - 출금 승인
- `POST /api/v1/withdrawals/{withdrawal_id}/reject` - 출금 거부
- `GET /api/v1/withdrawals/admin/stats` - 출금 통계

**🔋 TRON 에너지 풀 관리** ⭐️ **핵심 기능**
- `GET /api/v1/admin/energy/status` - 에너지 풀 현황 ❌ **구현필요**
- `POST /api/v1/admin/energy/create-pool` - 에너지 풀 생성 ❌ **구현필요**
- `GET /api/v1/admin/energy/usage-stats` - 에너지 사용 통계 ❌ **구현필요**
- `GET /api/v1/admin/energy/usage-logs` - 에너지 사용 로그 ❌ **구현필요**
- `POST /api/v1/admin/energy/record-price` - 에너지 가격 기록 ❌ **구현필요**
- `GET /api/v1/admin/energy/price-history` - 가격 히스토리 ❌ **구현필요**
- `POST /api/v1/admin/energy/simulate-usage` - 에너지 사용량 시뮬레이션 ❌ **구현필요**
- `PUT /api/v1/admin/energy/auto-manage` - 자동 에너지 관리 설정 ❌ **구현필요**

**수수료 관리**
- `GET /api/v1/admin/fees/current` - 현재 수수료 설정 ❌ **구현필요**
- `PUT /api/v1/admin/fees/internal` - 내부 수수료율 설정 ❌ **구현필요**
- `GET /api/v1/admin/fees/energy-cost` - 실시간 에너지 비용 조회 ❌ **구현필요**

**🏢 파트너사 관리** ⭐️ **화이트라벨링 핵심**
- `GET /api/v1/admin/partners/` - 파트너사 목록 ❌ **구현필요**
- `POST /api/v1/admin/partners/` - 파트너사 등록 ❌ **구현필요**
- `GET /api/v1/admin/partners/{partner_id}` - 파트너사 상세 ❌ **구현필요**
- `PUT /api/v1/admin/partners/{partner_id}` - 파트너사 수정 ❌ **구현필요**
- `GET /api/v1/admin/partners/{partner_id}/users` - 파트너사 사용자 목록 ❌ **구현필요**
- `GET /api/v1/admin/partners/{partner_id}/stats` - 파트너사 통계 ❌ **구현필요**
- `PUT /api/v1/admin/partners/{partner_id}/fees` - 파트너별 수수료 설정 ❌ **구현필요**

**분석 및 모니터링**
- `GET /api/v1/transaction-analytics/analytics` - 거래 분석
- `GET /api/v1/transaction-analytics/trends` - 트렌드 분석
- `GET /api/v1/transaction-analytics/suspicious-patterns` - 의심스러운 패턴
- `GET /api/v1/transaction-analytics/real-time-metrics` - 실시간 메트릭
- `GET /api/v1/transaction-analytics/alerts` - 알림 목록

**백업 관리**
- `GET /api/v1/admin/backups` - 백업 목록
- `POST /api/v1/admin/backups` - 백업 생성

## 🎨 프론트엔드 구조 설계

### 📁 프로젝트 구조
```
frontend/dantaro-wallet-ui/
├── public/
├── src/
│   ├── components/           # 공통 컴포넌트
│   │   ├── common/          # 버튼, 입력폼, 모달 등
│   │   ├── layout/          # 헤더, 사이드바, 푸터
│   │   └── charts/          # 차트 컴포넌트
│   ├── pages/               # 페이지 컴포넌트
│   │   ├── user/            # 사용자 페이지
│   │   │   ├── Dashboard/
│   │   │   ├── Wallet/
│   │   │   ├── Transactions/
│   │   │   ├── Deposit/
│   │   │   ├── Withdrawal/
│   │   │   ├── FeeInfo/     # 💰 수수료 안내
│   │   │   └── Settings/
│   │   ├── admin/           # 관리자 페이지
│   │   │   ├── Dashboard/
│   │   │   ├── EnergyPool/  # 🔋 에너지 풀 관리
│   │   │   ├── FeeManagement/ # 💰 수수료 관리  
│   │   │   ├── Partners/    # 🏢 파트너사 관리 (화이트라벨링)
│   │   │   ├── Users/
│   │   │   ├── Transactions/
│   │   │   ├── Analytics/
│   │   │   ├── Withdrawals/
│   │   │   └── System/
│   │   └── auth/            # 인증 페이지
│   │       ├── Login/
│   │       └── Register/
│   ├── services/            # API 서비스
│   ├── store/               # 상태 관리 (Redux/Zustand)
│   ├── utils/               # 유틸리티 함수
│   ├── hooks/               # 커스텀 훅
│   └── types/               # TypeScript 타입 정의
├── package.json
├── tsconfig.json
└── tailwind.config.js
```

### 🎯 화이트라벨링 고려사항

#### 사용자 페이지 (User Interface)
- **인증**: 로그인/회원가입
- **대시보드**: 잔액, 최근 거래, 차트
- **지갑**: 지갑 생성, 주소 확인, QR 코드
- **입금**: 입금 주소, 내역 조회
- **출금**: 출금 요청, 내역 조회, 취소, **🔥 수수료 견적 (USDT 기준)**
- **거래내역**: 전체 거래 내역, 필터링
- **💰 수수료 안내**: 수수료 체계 설명, 현재 요율 표시
- **설정**: 프로필 수정, 비밀번호 변경

#### 관리자 페이지 (Admin Interface)  
- **대시보드**: 시스템 개요, 실시간 통계
- **🔋 TRON 에너지 풀**: **핵심 기능!**
  - 에너지 풀 현황 모니터링
  - TRX Freeze 상태 관리
  - 에너지 사용량 통계 및 로그
  - 에너지 가격 정보 관리
  - 자동 에너지 관리 설정
- **💰 수수료 관리**: 
  - 내부 수수료율 설정
  - 실시간 에너지 비용 모니터링
  - 수수료 수익 분석
  - 파트너별 차등 수수료 설정
- **🏢 파트너사 관리**: **화이트라벨링 핵심!**
  - 파트너사 등록 및 관리
  - 파트너별 사용자 풀 분리
  - 파트너별 수수료 설정
  - 파트너별 통계 및 정산
  - API 키 관리
- **사용자 관리**: 사용자 목록, 상세 정보, 수정
- **거래 관리**: 전체 거래 내역, 모니터링
- **출금 관리**: 출금 승인/거부, 검토 시스템
- **분석**: 거래 분석, 트렌드, 의심스러운 패턴
- **알림**: 시스템 알림, 보안 알림
- **시스템**: 백업 관리, 설정

### 🛠️ 기술 스택 제안

#### 프레임워크
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**

#### 상태 관리
- **Zustand** (가벼운 상태 관리)
- **TanStack Query** (서버 상태 관리)

#### UI 라이브러리
- **Headless UI** 또는 **Radix UI**
- **Lucide React** (아이콘)
- **Chart.js** 또는 **Recharts** (차트)

#### 유틸리티
- **Axios** (HTTP 클라이언트)
- **React Hook Form** (폼 관리)
- **Zod** (스키마 검증)
- **Date-fns** (날짜 처리)

## 🚀 개발 우선순위

### Phase 1: 기본 설정 및 인증
1. Next.js 프로젝트 셋업
2. 타입 정의 및 API 서비스 계층
3. 인증 시스템 (로그인/회원가입)
4. 라우팅 및 권한 관리

### Phase 2: 사용자 페이지
1. 사용자 대시보드
2. 지갑 관리
3. 입출금 기능
4. 거래 내역

### Phase 3: 관리자 페이지
1. 관리자 대시보드
2. 사용자 관리
3. 출금 승인 시스템
4. 거래 분석 및 모니터링

### Phase 4: 고급 기능
1. 실시간 업데이트 (WebSocket)
2. 차트 및 분석 도구
3. 알림 시스템
4. 화이트라벨링 설정

## 🎨 디자인 컨셉

### 사용자 페이지
- **모던하고 깔끔한 디자인**
- **직관적인 네비게이션**
- **모바일 반응형**
- **다크/라이트 테마**

### 관리자 페이지
- **데이터 중심의 대시보드**
- **테이블과 차트 위주**
- **다양한 필터링 옵션**
- **실시간 상태 표시**

## 🔋 **TRON 에너지 풀 시스템 상세**

### 비즈니스 로직
1. **본사가 TRX를 Freeze하여 Energy Pool 운영**
   - 사용자의 모든 USDT 출금 트랜잭션을 본사 에너지로 스폰서십
   - 사용자는 실제 TRON 네트워크 수수료(Energy/Bandwidth)를 직접 지불하지 않음

2. **내부 수수료 시스템**
   - 사용자는 USDT 기준으로 내부 수수료 지불
   - 예: USDT 출금 시 2% 또는 고정 금액 차감
   - 본사는 TRX Energy로 실제 네트워크 수수료 지불

3. **수익 구조**
   - 내부 수수료 수익 > 실제 TRON 네트워크 비용
   - 에너지 풀 관리를 통한 비용 최적화

### 프론트엔드에서 구현해야 할 기능

#### 👤 사용자 페이지
**출금 시 수수료 표시**
```javascript
// 출금 요청 시 수수료 견적
const feeEstimate = await api.getFeeEstimate({
  amount: withdrawalAmount,
  currency: 'USDT'
});

// 표시 내용:
// - 출금 금액: 100 USDT
// - 플랫폼 수수료: 2 USDT (2%)
// - 실제 출금액: 98 USDT
// - 네트워크 수수료: 무료 (본사 지원)
```

**수수료 안내 페이지**
- 수수료 체계 설명
- "왜 네트워크 수수료가 무료인가?" 설명
- 내부 수수료율 표시

#### 🛠️ 관리자 페이지
**에너지 풀 대시보드**
```javascript
// 실시간 에너지 상태
const energyStatus = {
  totalFrozenTRX: 50000,      // 총 Freeze된 TRX
  availableEnergy: 1500000,   // 사용 가능한 에너지
  dailyConsumption: 85000,    // 일일 소비량
  energyThreshold: 100000,    // 부족 임계값
  costPerTransaction: 13000   // 트랜잭션당 에너지 비용
}
```

**에너지 사용 모니터링**
- 실시간 에너지 소비 차트
- 사용자별/시간대별 사용 패턴
- 에너지 부족 시 알림
- 자동 TRX Freeze 관리

**수수료 수익 분석**
- 내부 수수료 수익 vs 실제 에너지 비용
- 수익률 분석
- 수수료율 최적화 제안

### UI/UX 고려사항

#### 사용자 친화적 설명
```
✅ 출금 수수료 안내
┌─────────────────────────────────┐
│ 출금 금액: 100 USDT             │
│ 플랫폼 수수료: 2 USDT (2%)      │
│ ─────────────────────────────   │
│ 실제 출금액: 98 USDT            │
│                                 │
│ 🎉 TRON 네트워크 수수료: 무료   │
│    (본사가 대신 지불합니다)     │
└─────────────────────────────────┘
```

#### 관리자 에너지 모니터링
```
🔋 에너지 풀 현황
┌─────────────────────────────────┐
│ 🟢 에너지 충분 (1,500,000)      │
│ 📊 일일 소비율: 85%             │
│ 💰 동결 TRX: 50,000            │
│ ⚡ 예상 지속시간: 17일          │
└─────────────────────────────────┘
```

## 🚨 **중요한 추가 고려사항**

### 에너지 부족 시나리오 대응
**문제**: 서비스 초기 또는 에너지 고갈 시 출금 불가
**프론트엔드 구현 필요**:

#### 사용자 페이지
```javascript
// 에너지 부족 시 사용자 안내
const EnergyInsufficientModal = () => {
  return (
    <Modal>
      <h3>⚠️ 일시적 서비스 제한</h3>
      <p>현재 TRON 네트워크 에너지가 부족합니다.</p>
      
      <div className="options">
        <div className="option">
          <h4>옵션 1: TRX 수수료 추가 지불</h4>
          <p>추가 TRX 수수료: 0.5 TRX (~$0.06)</p>
          <button>TRX로 수수료 지불</button>
        </div>
        
        <div className="option">
          <h4>옵션 2: 에너지 충전 대기</h4>
          <p>예상 대기시간: 2-4시간</p>
          <button>대기열에 추가</button>
        </div>
      </div>
    </Modal>
  );
};
```

#### 관리자 페이지
```javascript
// 에너지 풀 긴급 관리
const EnergyEmergencyPanel = () => {
  return (
    <div className="emergency-panel">
      <div className="alert-critical">
        🚨 에너지 풀 임계 수준 (5% 남음)
      </div>
      
      <div className="emergency-actions">
        <button className="btn-urgent">
          긴급 TRX Freeze (10,000 TRX)
        </button>
        <button className="btn-urgent">
          에너지 구매 (외부 서비스)
        </button>
        <button className="btn-urgent">
          서비스 일시 중단
        </button>
      </div>
    </div>
  );
};
```

### 화이트라벨링 파트너 관리

#### 파트너사 대시보드
```javascript
const PartnerDashboard = () => {
  return (
    <div className="partner-dashboard">
      <div className="partner-header">
        <h2>파트너사: {partner.companyName}</h2>
        <span className="tier-badge tier-{partner.tier}">
          {partner.tier.toUpperCase()} 등급
        </span>
      </div>
      
      <div className="stats-grid">
        <StatCard title="총 사용자" value={partner.userCount} />
        <StatCard title="월 거래량" value={partner.monthlyVolume} />
        <StatCard title="수수료 수익" value={partner.feeRevenue} />
        <StatCard title="에너지 사용량" value={partner.energyUsage} />
      </div>
      
      <div className="partner-settings">
        <h3>파트너별 설정</h3>
        <FeeConfigPanel partnerId={partner.id} />
        <BrandingConfigPanel partnerId={partner.id} />
        <APIKeyManager partnerId={partner.id} />
      </div>
    </div>
  );
};
```

### 동적 수수료 관리

#### 관리자 수수료 설정
```javascript
const FeeManagementPanel = () => {
  return (
    <div className="fee-management">
      <div className="global-fees">
        <h3>글로벌 수수료 설정</h3>
        <FeeSlider 
          label="기본 출금 수수료" 
          value={fees.withdrawal} 
          range={[0.5, 5.0]}
          unit="USDT"
        />
      </div>
      
      <div className="partner-fees">
        <h3>파트너별 차등 수수료</h3>
        {partners.map(partner => (
          <PartnerFeeRow 
            key={partner.id}
            partner={partner}
            onUpdate={updatePartnerFee}
          />
        ))}
      </div>
      
      <div className="energy-based-adjustment">
        <h3>에너지 비용 연동 자동 조정</h3>
        <Toggle 
          enabled={autoAdjustment.enabled}
          label="에너지 비용에 따른 수수료 자동 조정"
        />
      </div>
    </div>
  );
};
```

이제 **트론 에너지 관리**가 핵심 기능으로 포함된 프론트엔드 계획이 완성되었습니다!

---

## 🚨 추가 구현 필요 사항

### ⚡ 에너지 부족 대응 시나리오
**상황**: 본사가 TRX 스테이킹을 하지 않은 초기 단계나 에너지 부족 상황

#### 사용자 페이지 추가 기능
```
🔋 에너지 부족 안내
┌─────────────────────────────────┐
│ ⚠️ 현재 네트워크가 혼잡합니다   │
│                                 │
│ 옵션 1: 대기 (예상: 2-4시간)   │
│ 옵션 2: TRX 수수료 직접 지불   │
│                                 │
│ TRX 수수료: ~13 TRX             │
│ [TRX로 즉시 출금]               │
└─────────────────────────────────┘
```

**필요한 엔드포인트**:
- `GET /api/v1/energy/status` - 현재 에너지 상태 확인 ❌ **구현필요**
- `POST /api/v1/energy/emergency-withdrawal` - TRX 직접 결제 출금 ❌ **구현필요**
- `GET /api/v1/energy/queue-position` - 대기열 위치 조회 ❌ **구현필요**

### 🏢 파트너사 관리 시스템 (화이트라벨링)
**목표**: 여러 파트너사가 각자의 사용자 풀을 관리

#### 관리자 페이지 추가 폴더 구조
```
src/pages/admin/
├── Partners/              # 🏢 파트너사 관리
│   ├── PartnerList/      # 파트너사 목록
│   ├── PartnerDetail/    # 파트너사 상세
│   ├── PartnerSettings/  # 파트너별 설정
│   └── PartnerAnalytics/ # 파트너별 분석
└── MultiTenant/          # 멀티테넌트 관리
    ├── UserPool/         # 파트너별 사용자 풀
    ├── FeeSettings/      # 파트너별 수수료
    └── BrandingConfig/   # 브랜딩 설정
```

#### 파트너사 관리 API ❌ **구현필요**
```
📁 /api/v1/admin/partners/
├── GET /partners - 파트너사 목록
├── POST /partners - 파트너사 등록
├── PATCH /partners/{id} - 파트너사 정보 수정
├── GET /partners/{id}/users - 파트너사 사용자 목록
├── GET /partners/{id}/stats - 파트너사별 통계
├── PUT /partners/{id}/fees - 파트너별 수수료 설정
└── PUT /partners/{id}/branding - 파트너별 UI 설정
```

#### 파트너사 대시보드 예시
```
🏢 파트너사: ABC Exchange
┌─────────────────────────────────┐
│ 📊 이번 달 통계                │
│ - 활성 사용자: 1,234명         │
│ - 총 거래량: 50,000 USDT       │
│ - 수수료 수익: 1,000 USDT      │
│ - 에너지 사용량: 45,000        │
│                                 │
│ 💰 수수료 설정                 │
│ - 출금 수수료: 1.5% (기본 2%)  │
│ - 최소 수수료: 0.5 USDT        │
│ - 최대 수수료: 10 USDT         │
└─────────────────────────────────┘
```

### 💰 동적 수수료 관리 시스템
**목표**: 관리자가 실시간으로 수수료율을 조정

#### 수수료 관리 페이지
```
src/pages/admin/FeeManagement/
├── FeeConfig/           # 수수료 설정
├── FeeHistory/          # 수수료 변경 이력
├── FeeAnalytics/        # 수수료 분석
└── PartnerFees/         # 파트너별 수수료
```

#### 수수료 관리 API ❌ **구현필요**
```
📁 /api/v1/admin/fees/
├── GET /config - 현재 수수료 설정 조회
├── POST /config - 새 수수료 설정 생성
├── PATCH /config/{id} - 수수료 설정 수정
├── GET /history - 수수료 변경 이력
├── POST /calculate - 수수료 미리 계산
└── PUT /partner/{partner_id} - 파트너별 수수료 설정
```

#### 동적 수수료 설정 UI
```
💰 수수료 설정 관리
┌─────────────────────────────────┐
│ 📋 전역 설정                   │
│ - 기본 출금 수수료: 2.0%       │
│ - 최소 수수료: 1.0 USDT        │
│ - 최대 수수료: 50.0 USDT       │
│                                 │
│ 🏢 파트너별 설정               │
│ ABC Exchange: 1.5%             │
│ XYZ Wallet: 2.5%               │
│                                 │
│ ⚡ 에너지 기반 할인             │
│ 에너지 충분 시: -0.2%          │
│ 에너지 부족 시: +0.3%          │
└─────────────────────────────────┘
```

### 🔔 실시간 알림 시스템
#### 알림 종류
1. **에너지 부족 경고** (임계값 90%)
2. **에너지 소진 알림** (임계값 95%)
3. **수수료 변경 알림**
4. **파트너사 API 장애**
5. **대용량 거래 감지**

#### 알림 UI 컴포넌트
```
src/components/notifications/
├── AlertBanner/         # 상단 경고 배너
├── NotificationCenter/  # 알림 센터
├── RealTimeStatus/      # 실시간 상태 표시
└── SystemHealth/        # 시스템 건강 상태
```

### 🚀 우선순위 구현 순서

#### Phase 1: 에너지 부족 대응 (즉시 필요)
1. **에너지 상태 확인 API** 구현
2. **TRX 직접 결제 출금** 옵션 추가
3. **사용자 대기열 시스템** 구현

#### Phase 2: 파트너사 기본 관리
1. **파트너사 모델 및 API** 구현
2. **파트너별 사용자 관리** 구현
3. **기본 멀티테넌시** 지원

#### Phase 3: 동적 수수료 시스템
1. **수수료 설정 API** 구현
2. **파트너별 수수료** 차별화
3. **에너지 상태 기반 수수료** 조정

#### Phase 4: 고급 기능
1. **실시간 알림** 시스템
2. **파트너 브랜딩** 커스터마이징
3. **고급 분석** 대시보드

### 📝 구현 가이드 문서

위의 모든 내용을 상세히 구현하기 위한 로드맵이 `/docs/IMPLEMENTATION_ROADMAP.md`에 작성되었습니다. 

**핵심 포인트**:
- ⚡ **에너지 부족 시 TRX 직접 결제** 옵션으로 서비스 중단 방지
- 🏢 **파트너사별 사용자/수수료 관리**로 화이트라벨링 완전 지원  
- 💰 **관리자가 실시간 수수료 조정** 가능
- 🔔 **실시간 모니터링**으로 운영 안정성 확보
