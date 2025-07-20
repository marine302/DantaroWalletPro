# Partner Admin Template

DantaroWalletPro의 파트너 관리자 대시보드 프론트엔드입니다.

## 🚀 기능

- **파트너 관리**: 파트너 등록, 수정, 삭제
- **지갑 연동**: TronLink를 통한 지갑 연결 및 관리
- **에너지 관리**: 에너지 렌탈 및 모니터링
- **출금 관리**: 출금 요청 처리 및 승인
- **실시간 분석**: 대시보드를 통한 실시간 데이터 모니터링
- **사용자 관리**: 사용자 계정 및 권한 관리

## 🛠 기술 스택

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI
- **Charts**: Recharts
- **Blockchain**: TronWeb, TronLink Adapter
- **State Management**: React Context

## 📦 설치 및 실행

### 환경 변수 설정

```bash
# 환경 변수 파일 복사
cp .env.example .env.local

# 필요한 환경 변수들을 설정하세요
# - NEXT_PUBLIC_API_URL: 백엔드 API URL
# - NEXT_PUBLIC_TRON_API_KEY: Tron API 키
```

### 의존성 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 프로덕션 실행
npm start

# 린트 검사
npm run lint
```

## 📁 프로젝트 구조

```
src/
├── app/                    # Next.js App Router 페이지
│   ├── analytics/         # 분석 페이지
│   ├── api/              # API 라우트
│   ├── energy/           # 에너지 관리 페이지
│   ├── notifications/    # 알림 페이지
│   ├── settings/         # 설정 페이지
│   ├── users/           # 사용자 관리 페이지
│   ├── wallet/          # 지갑 페이지
│   └── withdrawals/     # 출금 관리 페이지
├── components/           # 재사용 가능한 컴포넌트
│   ├── dashboard/       # 대시보드 전용 컴포넌트
│   ├── layout/          # 레이아웃 컴포넌트
│   ├── ui/              # 기본 UI 컴포넌트
│   └── wallet/          # 지갑 관련 컴포넌트
├── contexts/            # React Context
├── lib/                 # 유틸리티 및 API 클라이언트
└── types/               # TypeScript 타입 정의
```

## 🔗 백엔드 연동

이 프론트엔드는 별도의 백엔드 API 서버와 통신합니다:

- **기본 URL**: `http://localhost:8000`
- **API 버전**: `/api/v1`
- **인증**: Bearer Token 방식

### API 문서 참고

- Doc-24: TronLink 연동
- Doc-25: 파트너 관리
- Doc-26: 에너지 관리
- Doc-27: 수수료 관리
- Doc-28: 출금 관리
- Doc-29: 온보딩
- Doc-30: 감사
- Doc-31: 에너지 렌탈

## 🌐 배포

### Vercel 배포

가장 간단한 배포 방법입니다:

1. [Vercel](https://vercel.com)에 GitHub 저장소 연결
2. 환경 변수 설정
3. 자동 배포 완료

### Docker 배포

```bash
# Docker 이미지 빌드
docker build -t partner-admin .

# 컨테이너 실행
docker run -p 3000:3000 partner-admin
```

## 🔧 개발 환경 설정

### VSCode 확장 프로그램 권장

- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- TypeScript Importer
- Prettier - Code formatter
- ESLint

### 코드 스타일

- **Prettier**: 코드 포맷팅
- **ESLint**: 코드 품질 검사
- **TypeScript**: 타입 안전성

## 📝 라이센스

MIT License
