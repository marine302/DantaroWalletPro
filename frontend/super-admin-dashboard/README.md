# Super Admin Dashboard

Dantaro Wallet Pro의 슈퍼 관리자용 대시보드입니다.

## 🚀 주요 기능

- **파트너 관리**: 파트너사 등록, 상태 모니터링, 정산 관리
- **트랜잭션 모니터링**: 실시간 거래 추적 및 분석
- **에너지 시장 관리**: 에너지 거래소 모니터링 및 자동 구매 설정
- **수수료 정책**: 동적 수수료 정책 관리 및 최적화
- **감사 및 컴플라이언스**: 규정 준수 모니터링
- **통합 대시보드**: 다중 파트너 통합 뷰

## 🛠️ 기술 스택

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack React Query
- **UI Components**: Headless UI + Custom Components
- **API Client**: Axios
- **Development**: Turbopack

## 📦 설치 및 실행

### 개발 환경 실행
```bash
npm install
npm run dev
```

### 빌드 및 배포
```bash
npm run build
npm run start
```

### Linting
```bash
npm run lint
```

## 🔧 환경 설정

`.env.local` 파일을 생성하고 다음 설정을 추가하세요:

```env
# 포트 설정
NEXT_PUBLIC_FRONTEND_PORT=3020

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
│   ├── page.tsx           # 홈페이지
│   ├── partners/          # 파트너 관리
│   ├── analytics/         # 분석 대시보드
│   ├── energy/           # 에너지 관리
│   └── ...
├── components/            # 재사용 컴포넌트
│   ├── layout/           # 레이아웃 컴포넌트
│   ├── ui/               # UI 컴포넌트
│   └── charts/           # 차트 컴포넌트
├── hooks/                # Custom Hooks
├── lib/                  # 유틸리티 및 설정
├── services/             # API 서비스
├── types/                # TypeScript 타입 정의
└── styles/               # 스타일 관련
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

1. **컴포넌트 개발**: `src/components/ui/`에 재사용 가능한 컴포넌트 작성
2. **API 연동**: `src/services/`에 API 서비스 로직 구현
3. **타입 정의**: `src/types/`에 TypeScript 인터페이스 정의
4. **스타일링**: Tailwind CSS 클래스 사용, 필요시 CSS 모듈 활용

## 📚 문서

상세한 개발 문서는 `docs/` 폴더를 참조하세요.
