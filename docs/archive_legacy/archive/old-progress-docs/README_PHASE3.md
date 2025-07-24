# DantaroWallet Partner Admin Template

파트너 관리자를 위한 Next.js 기반 관리 대시보드 템플릿입니다.

## 📋 프로젝트 개요

### 주요 기능
- 🏗️ **모듈화된 컴포넌트 구조**: shadcn/ui 기반 재사용 가능한 컴포넌트
- 📊 **실시간 대시보드**: WebSocket 및 SSE를 통한 실시간 데이터 업데이트
- 👥 **사용자 관리**: 사용자 등록, 권한 관리, 활동 모니터링
- 💰 **출금 관리**: 출금 요청 승인/거부, 일괄 처리, 통계 분석
- ⚡ **에너지 관리**: TRON 에너지 풀 관리, 렌탈 시스템
- 📈 **분석 및 리포팅**: 다양한 차트와 통계, 커스텀 리포트 생성
- 🔐 **보안**: JWT 인증, 권한 기반 접근 제어
- 🎨 **반응형 UI**: 모바일/태블릿/데스크톱 최적화

### 기술 스택
- **Frontend**: Next.js 15, React 19, TypeScript
- **UI Framework**: shadcn/ui, Tailwind CSS, Radix UI
- **State Management**: TanStack Query (React Query)
- **Real-time**: WebSocket, Server-Sent Events
- **Charts**: Recharts
- **Testing**: Jest, React Testing Library
- **Linting**: ESLint, TypeScript

## 🚀 시작하기

### 전제 조건
- Node.js 18+ 
- npm 또는 yarn
- 백엔드 API 서버 (포트 8000)

### 설치 및 실행

1. **의존성 설치**
```bash
npm install
```

2. **환경 변수 설정**
```bash
cp .env.example .env.local
# .env.local 파일을 편집하여 필요한 환경 변수 설정
```

3. **개발 서버 실행**
```bash
npm run dev
```

4. **브라우저에서 확인**
- 개발 서버: http://localhost:3030
- 고정 포트: 3030 (변경 불가)

## 📁 프로젝트 구조

```
src/
├── app/                          # Next.js App Router 페이지
│   ├── layout.tsx               # 루트 레이아웃
│   ├── page.tsx                 # 대시보드 홈
│   ├── analytics/               # 분석 페이지
│   ├── users/                   # 사용자 관리
│   ├── withdrawals/             # 출금 관리
│   ├── energy/                  # 에너지 관리
│   ├── energy-rental/           # 에너지 렌탈
│   ├── notifications/           # 알림 관리
│   ├── settings/                # 설정
│   ├── wallet/                  # 지갑 연동
│   ├── audit/                   # 감사 로그
│   ├── health-check/            # 시스템 상태
│   ├── onboarding/              # 온보딩
│   ├── withdrawal-policy/       # 출금 정책
│   └── api/                     # API 라우트
├── components/                   # 재사용 가능한 컴포넌트
│   ├── ui/                      # shadcn/ui 기본 컴포넌트
│   ├── layout/                  # 레이아웃 컴포넌트
│   ├── dashboard/               # 대시보드 컴포넌트
│   ├── analytics/               # 분석 컴포넌트
│   ├── users/                   # 사용자 관리 컴포넌트
│   ├── withdrawals/             # 출금 관리 컴포넌트
│   ├── energy/                  # 에너지 관리 컴포넌트
│   ├── charts/                  # 차트 컴포넌트
│   └── [feature]/               # 기능별 컴포넌트
├── lib/                         # 유틸리티 및 라이브러리
│   ├── api-client.ts            # API 클라이언트
│   ├── realtime.ts              # 실시간 데이터 처리
│   ├── hooks.ts                 # React 훅들
│   ├── utils.ts                 # 유틸리티 함수
│   └── services/                # API 서비스들
│       ├── user.service.ts
│       ├── withdrawal.service.ts
│       ├── energy.service.ts
│       └── analytics.service.ts
├── types/                       # TypeScript 타입 정의
│   └── index.ts
└── __tests__/                   # 테스트 파일
    ├── components/
    └── lib/
```

## 🔧 주요 컴포넌트

### 공통 컴포넌트
- **PageHeader**: 페이지 제목, 설명, 액션 버튼
- **StatsCards**: 통계 카드 그리드
- **DataTable**: 데이터 테이블 (정렬, 필터링, 페이지네이션)
- **LoadingSpinner**: 로딩 상태 표시
- **ErrorBoundary**: 에러 경계 처리

### 기능별 컴포넌트
- **UserManagementSection**: 사용자 목록, 생성, 수정
- **WithdrawalManagementSection**: 출금 요청 관리
- **EnergyManagementSection**: 에너지 풀 및 거래 관리
- **AnalyticsSection**: 차트 및 통계 표시
- **RealtimeEnergyMonitor**: 실시간 에너지 모니터링

## 🌐 API 연동

### API 클라이언트
```typescript
import { apiClient } from '@/lib/api-client'

// GET 요청
const users = await apiClient.get('/users')

// POST 요청
const newUser = await apiClient.post('/users', userData)

// 인증 토큰 설정
apiClient.setAuthToken('your-jwt-token')
```

### React Query 훅 사용
```typescript
import { useUsers, useCreateUser } from '@/lib/hooks'

function UserList() {
  const { data: users, loading, error } = useUsers()
  const createUser = useCreateUser()
  
  // 컴포넌트 로직
}
```

## ⚡ 실시간 데이터

### WebSocket 연결
```typescript
import { useRealtime } from '@/lib/hooks'

function RealTimeComponent() {
  const { data, connected, error } = useRealtime({
    channel: 'energy-updates',
    autoConnect: true
  })
  
  return (
    <div>
      Status: {connected ? 'Connected' : 'Disconnected'}
      Data: {JSON.stringify(data)}
    </div>
  )
}
```

### Server-Sent Events
```typescript
const { data } = useRealtime({
  channel: 'notifications',
  useSSE: true,
  sseEndpoint: '/api/events'
})
```

## 🧪 테스트

### 테스트 실행
```bash
# 전체 테스트 실행
npm test

# 감시 모드
npm run test:watch

# 커버리지 리포트
npm run test:coverage
```

### 테스트 구조
- **Unit Tests**: 개별 컴포넌트 및 유틸리티 함수
- **Integration Tests**: API 서비스 및 훅 테스트
- **Component Tests**: 사용자 상호작용 테스트

## 🔍 코드 품질

### 린팅 및 타입 체크
```bash
# ESLint 실행
npm run lint

# TypeScript 타입 체크
npm run type-check
```

### 코드 커버리지 목표
- 라인 커버리지: 70% 이상
- 함수 커버리지: 70% 이상
- 브랜치 커버리지: 70% 이상

## 📝 개발 가이드

### 새 페이지 추가
1. `src/app/` 에 디렉토리 생성
2. `page.tsx` 파일 생성
3. 해당 기능의 컴포넌트를 `src/components/` 에 생성
4. API 서비스가 필요한 경우 `src/lib/services/` 에 추가
5. 훅이 필요한 경우 `src/lib/hooks.ts` 에 추가

### 새 컴포넌트 추가
1. 적절한 디렉토리에 컴포넌트 파일 생성
2. TypeScript 인터페이스 정의
3. 테스트 파일 작성
4. 스토리북 스토리 작성 (선택사항)

### API 서비스 추가
1. `src/lib/services/` 에 서비스 파일 생성
2. API 엔드포인트 메서드 구현
3. 해당 훅을 `src/lib/hooks.ts` 에 추가
4. 타입 정의를 `src/types/index.ts` 에 추가

## 🚀 배포

### 빌드
```bash
npm run build
```

### 프로덕션 실행
```bash
npm start
```

### 환경별 설정
- **개발**: `.env.local`
- **스테이징**: `.env.staging`
- **프로덕션**: `.env.production`

## 🔒 보안 고려사항

1. **환경 변수**: 민감한 정보는 `.env` 파일에 저장하고 버전 관리에서 제외
2. **API 인증**: JWT 토큰 기반 인증 구현
3. **XSS 방지**: 사용자 입력 검증 및 이스케이프 처리
4. **CSRF 보호**: API 요청에 CSRF 토큰 포함

## 📚 참고 자료

- [Next.js 문서](https://nextjs.org/docs)
- [shadcn/ui 문서](https://ui.shadcn.com/)
- [TanStack Query 문서](https://tanstack.com/query)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)

## 🤝 기여하기

1. 이슈 생성 또는 기존 이슈 확인
2. 브랜치 생성 (`feature/feature-name`)
3. 변경사항 커밋
4. 테스트 작성 및 실행
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 📞 지원

문제가 발생하거나 질문이 있는 경우:
- GitHub Issues 생성
- 개발팀 연락

---

**주의**: 이 템플릿은 개발용이며, 프로덕션 환경에서 사용하기 전에 보안 검토가 필요합니다.
