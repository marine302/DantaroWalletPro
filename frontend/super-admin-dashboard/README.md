# Su# Super Admin Dashboard

Dantaro Wallet Pro의 슈퍼 관리자용 대시보드입니다.

## 🎯 최신 업데이트 (2025.07.21)

### ✨ 완료된 주요 개선사항 - Phase 2 완료 🎉
- **🔋 TronNRG API 완전 통합**: 실시간 에너지 가격, 공급자 모니터링, 주문 생성/관리
- **⚡ 외부 에너지 마켓 시스템**: 실시간 가격 업데이트, 시장가/지정가 주문, 다중 공급자 지원
- **� Audit & Compliance 시스템 완전 구현**: 실시간 모니터링, 감사 로그, 보고서 생성
- **🛡️ RBAC 권한 시스템**: 모든 보호된 페이지에 withRBAC 적용 및 세분화된 권한 관리
- **🌍 완전한 다국어 지원**: 메뉴 시스템과 언어팩 완전 통합 (한국어/영어)
- **🔧 타입 안전성**: TypeScript 에러 완전 제거, 빌드 성공 (24/24 페이지)
- **⚡ 성능 최적화**: Next.js 빌드 최적화 완료, WebSocket 실시간 연결 구현
- **🎛️ 통합 서비스 관리**: Mock HTTP Server, WebSocket Server, Frontend 자동화
- **🎨 UI/UX 일관성**: DarkThemeComponents 기반 통일된 디자인 시스템
- **⚡ 성능 최적화**: Next.js 빌드 최적화 완료, WebSocket 연결 안정화
- **🎛️ 통합 서비스 관리**: Mock HTTP Server, WebSocket Server, Frontend 자동화
- **🎨 UI/UX 일관성**: DarkThemeComponents 기반 통일된 디자인 시스템
- **📋 메뉴 시스템 완전 리팩터링**: i18n 기반 동적 메뉴, 권한별 필터링
- **🔄 워크플로우 명확화**: 파트너 관리/온보딩, 시스템/분석 대시보드 역할 분리
- **📊 감사 시스템**: 실시간 트랜잭션 모니터링, 긴급 차단, 보고서 생성 완료
- **⚡ 성능 최적화**: Next.js 빌드 최적화 완료 (24/24 페이지 생성)
- **🎛️ 통합 서비스 관리**: Mock HTTP Server, WebSocket Server, Frontend 자동화
- **� UI/UX 일관성**: DarkThemeComponents 기반 통일된 디자인 시스템

### 🔄 리팩터링된 페이지 및 워크플로우
- **파트너 관리** (`/partners`): 승인된 파트너 운영 관리 (관리/모니터링 중심)
- **신규 파트너 온보딩** (`/partner-onboarding`): 신규 가입 프로세스 관리 (등록/승인 중심)
- **시스템 대시보드** (`/`): 전체 시스템 현황 및 실시간 모니터링
- **파트너 분석 대시보드** (`/integrated-dashboard`): 파트너별 상세 데이터 분석
- **감사 및 컴플라이언스** (`/audit-compliance`): 668줄 → 간소화된 표준 구조
- **알림 테스트** (`/notification-test`): 완전 재구성 및 기능 강화
- **WebSocket 테스트** (`/websocket-test`): 실시간 연결 테스트 및 모니터링
- **디버그 페이지** (`/debug`): 개발자 도구 및 시스템 진단

### 🎨 메뉴 시스템 개선
- **동적 메뉴 생성**: menu-config.ts 기반 중앙집중식 메뉴 관리
- **권한별 메뉴 필터링**: RBAC 권한에 따른 메뉴 자동 표시/숨김
- **다국어 메뉴**: i18n 언어팩과 완전 통합된 메뉴 라벨
- **중첩 메뉴 지원**: 에너지 관리 등 하위 메뉴 구조
- **아이콘 통일**: Heroicons 기반 일관된 아이콘 시스템
- **개발 도구 메뉴**: 개발 환경에서만 표시 (notification-test, websocket-test, debug)

## �🚀 주요 기능

- **실시간 모니터링**: WebSocket 기반 실시간 시스템 상태 모니터링
- **파트너 관리**: 파트너사 등록, 상태 모니터링, 정산 관리
- **파트너 온보딩**: 신규 파트너 가입 프로세스 관리 (KYC, 계약, 배포)
## 🚀 주요 기능

### 🎛️ 시스템 관리
- **실시간 모니터링**: WebSocket 기반 실시간 시스템 상태 모니터링
- **통합 대시보드**: 시스템 성능, 사용자 활동, 거래 현황 실시간 추적
- **실시간 알림**: 시스템 이벤트 및 거래 알림 (우선순위별 분류)
- **RBAC 권한 관리**: 역할 기반 접근 제어 및 세분화된 권한 시스템

### 👥 파트너 관리
- **파트너 운영 관리**: 승인된 파트너사 모니터링, 상태 관리, 정산 처리
- **신규 파트너 온보딩**: KYC, 계약 체결, 시스템 배포 프로세스 관리
- **파트너 분석 대시보드**: 파트너별 상세 분석, 실시간 데이터 연동
- **트랜잭션 모니터링**: 파트너별 거래 추적 및 분석

### ⚡ 에너지 시장 (TronNRG API 연동)
- **실시간 에너지 거래**: TronNRG API 기반 실시간 가격 모니터링 및 주문 관리
- **외부 공급자 통합**: TronNRG 및 기타 에너지 공급자 API 연동
- **자동/수동 구매**: 시장가/지정가 주문, 임계값 기반 자동 구매
- **구매 이력 관리**: 완전한 에너지 구매 내역 추적 및 분석
- **실시간 WebSocket**: 가격 변동 및 주문 상태 실시간 업데이트

### 💼 비즈니스 관리
- **수수료 정책**: 동적 수수료 정책 관리 및 최적화
- **분석 리포트**: 비즈니스 분석 및 트렌드 추적
- **감사 및 컴플라이언스**: 실시간 규정 준수 모니터링, AML/KYC 관리, 보고서 생성
- **관리자 계정**: 슈퍼 관리자 및 하위 관리자 계정 관리

### 🔧 개발 도구
- **WebSocket 테스트**: 실시간 연결 상태 테스트 및 모니터링
- **알림 테스트**: 알림 시스템 테스트 및 히스토리 관리
- **디버그 도구**: 시스템 진단 및 개발자 도구

## 🛠️ 기술 스택

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack React Query
- **Real-time**: WebSocket (ws)
- **UI Components**: Headless UI + Custom Components
- **API Client**: Axios
- **Development**: Turbopack

## 📦 설치 및 실행

### 통합 서비스 실행 (권장)
```bash
npm install
./manage-services.sh start  # 모든 서비스 자동 시작
```

### 개발 환경 실행
```bash
npm install
npm run dev                 # 프론트엔드만 실행
```

### Mock 서버와 함께 개발
```bash
# 실시간 모니터링 Mock 서버와 함께 실행
npm run dev:with-mock

# 또는 개별 실행
npm run mock-server         # 터미널 1: Mock HTTP Server (포트 3001)
npm run mock-realtime       # 터미널 2: Mock WebSocket Server (포트 3002)
npm run dev                 # 터미널 3: Frontend (포트 3020)
```

### 빌드 및 배포
```bash
npm run build
npm run start
```

### 개발 도구
```bash
npm run lint               # ESLint 실행
npm run type-check         # TypeScript 타입 체크
./check-all-errors.sh      # 전체 에러 체크
```

## 🔧 환경 설정

`.env.local` 파일을 생성하고 다음 설정을 추가하세요:

```env
# API 설정
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MOCK_API_URL=http://localhost:3001

# WebSocket 설정
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_MOCK_WS_URL=ws://localhost:3002

# 포트 설정
NEXT_PUBLIC_FRONTEND_PORT=3020
NEXT_PUBLIC_MOCK_SERVER_PORT=3001
NEXT_PUBLIC_MOCK_WS_PORT=3002

# 개발 설정
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_USE_MOCK_DATA=true

# 권한 설정
NEXT_PUBLIC_ENABLE_RBAC=true
```

## 🎛️ 서비스 관리

### 통합 서비스 관리자
```bash
./manage-services.sh start    # 모든 서비스 시작
./manage-services.sh stop     # 모든 서비스 종료
./manage-services.sh status   # 서비스 상태 확인
./manage-services.sh restart  # 서비스 재시작
```

### 포트 관리
- **Frontend**: 3020
- **Mock HTTP Server**: 3001  
- **Mock WebSocket Server**: 3002
- **Backend API**: 8000 (실제 서버)

## 🔐 권한 시스템 (RBAC)

### 사용자 역할
- **super_admin**: 모든 권한
- **admin**: 일반 관리 권한
- **viewer**: 조회 권한만
- **auditor**: 감사 관련 권한

### 주요 권한
- `partners.view`, `partners.create`, `partners.edit`: 파트너 관리
- `admin.manage`: 관리자 계정 관리
- `audit.view`, `compliance.view`: 감사 및 컴플라이언스
- `analytics.view`: 분석 대시보드
- `energy.view`, `energy.manage`: 에너지 관리
- `notifications.view`: 알림 시스템
- `realtime.monitor`: 실시간 모니터링

# Auth 설정
NEXTAUTH_SECRET=dantaro-super-admin-secret-key-2025
NEXTAUTH_URL=http://localhost:3020
```

## 🎯 구현 상태

### ✅ **완료된 기능**
- **🎛️ 통합 서비스 관리**: 자동화된 프로세스 및 포트 관리 시스템
- **📊 실시간 모니터링**: WebSocket 기반 실시간 시스템 상태 모니터링
- **📈 시스템 성능 추적**: CPU, Memory, Disk, 연결 수 실시간 모니터링
- **💼 비즈니스 메트릭**: 사용자, 거래, 수익 실시간 추적
- **🔔 실시간 알림**: 시스템 이벤트 및 거래 알림 (우선순위, 히스토리)
- **💰 거래 모니터링**: 실시간 거래 내역 스트리밍
- **🎨 표준화된 UI/UX**: DarkThemeComponents 기반 일관된 디자인
- **🌍 완전한 i18n**: 다국어 지원 및 동적 메뉴 시스템
- **🛡️ RBAC 권한 시스템**: 역할 기반 접근 제어 및 페이지 보호
- **👥 파트너 관리 시스템**: 파트너 운영 관리 및 신규 온보딩 프로세스
- **📋 감사 및 컴플라이언스**: 규정 준수 모니터링 시스템
- **⚡ 에너지 시장 관리**: 거래소 모니터링 및 자동 구매 시스템
- **🔧 개발자 도구**: Mock 서버, 테스트 페이지, 디버그 도구

### 🔄 **지속적인 개선**
- **성능 최적화**: 코드 분할, 메모이제이션, 렌더링 최적화
- **보안 강화**: 2FA, 세션 관리, API 보안
- **사용자 경험**: 로딩 상태, 에러 처리, 접근성 개선

### ⏳ **향후 계획**
- **모바일 최적화**: 반응형 디자인 개선 및 모바일 전용 기능
- **백엔드 API 연동**: 실제 서버 API와의 완전한 통합
- **고급 분석**: 머신러닝 기반 예측 분석 및 인사이트

## 🔄 실시간 모니터링 시스템

### 실행 중인 서비스
현재 다음 서비스들이 실행 중입니다:

- **Dashboard**: http://localhost:3021
- **Mock WebSocket**: ws://localhost:3002  
- **Mock HTTP API**: http://localhost:3001

### Mock 서버
개발 중에는 실제 백엔드 없이 Mock 서버를 사용할 수 있습니다:

- **HTTP API**: `http://localhost:3001`
- **WebSocket**: `ws://localhost:3002`

Mock 서버는 다음 데이터를 실시간으로 제공합니다:
- 시스템 성능 지표 (CPU, Memory, Disk)
- 비즈니스 메트릭 (사용자, 거래, 수익)
- 실시간 알림
- 거래 내역

### 실시간 데이터 타입
```typescript
interface RealtimeData {
  systemStats: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    activeConnections: number;
  };
  dashboardStats: {
    activeUsers: number;
    totalTransactions: number;
    energyTrading: number;
    revenue: number;
  };
  alerts: Alert[];
  transactions: Transaction[];
  energyMarket: EnergyMarketData;
}
```

# API 엔드포인트
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# 외부 서비스
NEXT_PUBLIC_PARTNER_ADMIN_URL=http://localhost:3021
```

## 📁 프로젝트 구조

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 전역 레이아웃
│   ├── page.tsx           # 시스템 대시보드 (홈)
│   ├── partners/          # 파트너 운영 관리
│   ├── partner-onboarding/ # 신규 파트너 온보딩
│   ├── integrated-dashboard/ # 파트너 분석 대시보드
│   ├── analytics/         # 비즈니스 분석
│   ├── energy/           # 에너지 시장 관리
│   │   ├── auto-purchase/    # 자동 구매 설정
│   │   ├── external-market/  # 외부 시장 연동
│   │   └── purchase-history/ # 구매 이력
│   ├── audit-compliance/  # 감사 및 컴플라이언스
│   ├── fees/             # 수수료 정책
│   ├── admins/           # 관리자 계정 관리
│   ├── settings/         # 시스템 설정
│   ├── notification-test/ # 알림 테스트 (개발)
│   ├── websocket-test/   # WebSocket 테스트 (개발)
│   ├── debug/            # 디버그 도구 (개발)
│   └── api/              # API 라우트
├── components/            # 재사용 컴포넌트
│   ├── layout/           # 레이아웃 컴포넌트
│   │   ├── DashboardLayout.tsx
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx   # 동적 메뉴 시스템
│   ├── ui/               # UI 컴포넌트
│   │   ├── BasePage.tsx  # 페이지 기본 구조
│   │   ├── PageTemplates.tsx # 표준 페이지 템플릿
│   │   ├── DarkThemeComponents.tsx # 통일된 UI
│   │   └── ...
│   └── charts/           # 차트 컴포넌트
├── hooks/                # Custom Hooks
│   ├── use-super-admin.ts
│   └── use-partner-admin.ts
├── lib/                  # 유틸리티 및 설정
│   ├── api.ts           # API 클라이언트
│   ├── menu-config.ts   # 메뉴 설정 (중앙집중)
│   └── i18n/            # 다국어 지원
│       ├── ko.ts        # 한국어
│       └── en.ts        # 영어
├── services/             # API 서비스
│   ├── api-client.ts
│   ├── super-admin-service.ts
│   └── partner-admin-service.ts
├── types/                # TypeScript 타입 정의
│   ├── index.ts         # 공통 타입
│   ├── auth.ts          # 인증/권한 타입
│   ├── i18n.ts          # 다국어 타입
│   └── notification.ts  # 알림 타입
└── styles/               # 스타일 관련
    └── dark-theme.ts
```

## 🔌 API 연동

- **Mock Server**: 개발용 목 서버 (`mock-server.js`)
- **API Client**: Axios 기반 클라이언트 (`src/lib/api.ts`)
- **타입 안전성**: 완전한 TypeScript 지원

## 🌐 다국어 지원

- 한국어 (ko)
- 영어 (en)

## 📱 반응형 디자인

- Desktop First 접근
- Tablet 및 Mobile 지원
- Dark/Light 테마 (개발 중)

## 🔗 관련 프로젝트

- [Partner Admin Template](../partner-admin-template) - 파트너사용 관리 템플릿
- [Backend API](../../dantarowallet) - Python FastAPI 백엔드

## 📋 포트 관리

이 프로젝트는 중앙집중식 포트 관리를 사용합니다:
- Frontend: 3020
- Mock Server: 3001
- Partner Admin: 3021

자세한 내용은 `PORT_MANAGEMENT.md`를 참조하세요.

## 🤝 개발 가이드

### 📋 코딩 표준
1. **컴포넌트 개발**: 
   - `src/components/ui/`에 재사용 가능한 컴포넌트 작성
   - `BasePage`, `Section`, `StatCard` 표준 구조 사용
   - `DarkThemeComponents`를 통한 일관된 스타일링

2. **페이지 개발**:
   - `PageTemplates.tsx`의 표준 템플릿 활용
   - RBAC 권한이 필요한 페이지는 `withRBAC` HOC 적용
   - 언어팩 기반 텍스트 사용 (`useI18n` 훅)

3. **API 연동**: 
   - `src/services/`에 API 서비스 로직 구현
   - TypeScript 인터페이스를 통한 타입 안전성 보장
   - TanStack React Query를 통한 데이터 관리

4. **타입 정의**: 
   - `src/types/`에 TypeScript 인터페이스 정의
   - 공통 타입은 `index.ts`, 도메인별 타입은 별도 파일

5. **스타일링**: 
   - Tailwind CSS 클래스 우선 사용
   - 복잡한 스타일은 CSS 모듈 활용
   - 다크/라이트 테마 고려한 색상 사용

### 🔧 개발 워크플로우
1. **새 기능 개발**:
   ```bash
   # 1. 개발 환경 시작
   ./manage-services.sh start
   
   # 2. 타입 체크
   npm run type-check
   
   # 3. 린트 체크
   npm run lint
   
   # 4. 빌드 테스트
   npm run build
   ```

2. **메뉴 추가**:
   - `src/lib/menu-config.ts`에 메뉴 설정 추가
   - `src/lib/i18n/`에 다국어 라벨 추가
   - 필요시 권한 설정 및 아이콘 지정

3. **권한 관리**:
   - `src/types/auth.ts`에 새 권한 정의
   - 컴포넌트에서 `useAuth` 훅으로 권한 체크
   - 페이지 레벨에서는 `withRBAC` HOC 사용

### 🧪 테스트 가이드
- **알림 테스트**: `/notification-test` 페이지
- **WebSocket 테스트**: `/websocket-test` 페이지  
- **시스템 디버그**: `/debug` 페이지
- **에러 체크**: `./check-all-errors.sh` 스크립트

## 📚 문서

상세한 개발 문서는 `docs/` 폴더를 참조하세요.

## 🔄 백엔드 API 마이그레이션 준비

### 현재 상태 (Phase 2 완료)
- ✅ TronNRG API 직접 연동 구현 완료 
- ✅ 실시간 에너지 거래 시스템 구현
- ✅ Mock/Real API 전환 가능한 서비스 구조
- ✅ 백엔드 API 요구사항 문서 작성 완료

### 백엔드 API 완성 시 즉시 적용할 준비 완료
- 📋 **백엔드 연동 체크리스트**: `docs/backend-ready-checklist.md`
- 🔧 **자동 마이그레이션 스크립트**: `scripts/migrate-to-backend.sh`
- 📖 **상세 마이그레이션 가이드**: `docs/frontend-migration-plan.md`
- 🎯 **백엔드 API 스펙 문서**: `docs/backend-energy-api-requirements.md`

### 백엔드 팀을 위한 API 요구사항
1. **에너지 공급자 API 엔드포인트** (`/api/v1/energy/external`)
   - TronNRG 시장 데이터 중계 (`/tronnrg/market/*`)
   - 주문 생성 및 관리 (`/tronnrg/order`)
   - WebSocket 실시간 스트리밍 (`/ws/energy/tronnrg`)

2. **인증 및 권한**
   - JWT 토큰 기반 인증
   - RBAC 권한 시스템 연동

3. **실시간 통신**
   - WebSocket을 통한 실시간 가격 스트리밍
   - 주문 상태 실시간 업데이트

### 마이그레이션 실행 방법
```bash
# 백엔드 API 준비 완료 시
./scripts/migrate-to-backend.sh http://your-backend-url:8000

# 수동 설정 확인이 필요한 경우
./scripts/prepare-backend-migration.sh
```

## 🔧 개발 환경 설정

### 통합 서비스 실행 (권장)
```bash
npm install
./manage-services.sh start  # 모든 서비스 자동 시작
```
