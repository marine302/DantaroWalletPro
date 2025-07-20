# Phase 2 개발 가이드

## 🎯 Phase 2 목표
파트너 관리자 템플릿의 백엔드 API 연동 및 실데이터 처리

## 📋 Phase 2 주요 작업 목록

### 1. 백엔드 API 연동 (우선순위: 높음)
- [ ] **API 엔드포인트 연결**
  - 사용자 관리 API (`/api/v1/admin/users/`)
  - 출금 관리 API (`/api/v1/admin/withdrawals/`)
  - 에너지 관리 API (`/api/v1/admin/energy/`)
  - 분석 데이터 API (`/api/v1/admin/analytics/`)

- [ ] **환경 변수 설정**
  ```bash
  # .env.local 파일 생성
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_TRON_NETWORK=shasta  # or mainnet
  ```

- [ ] **API 클라이언트 구현**
  - `src/lib/api.ts` 실제 API 호출 로직 구현
  - JWT 토큰 인증 처리
  - 에러 핸들링 및 재시도 로직

### 2. 실시간 데이터 처리 (우선순위: 중간)
- [ ] **WebSocket 연결**
  - 실시간 에너지 모니터링
  - 출금 요청 알림
  - 시스템 상태 업데이트

- [ ] **React Query 고도화**
  - 실시간 데이터 캐싱
  - 백그라운드 업데이트
  - Optimistic Updates

### 3. 차트 및 시각화 (우선순위: 중간)
- [ ] **차트 라이브러리 선택 및 구현**
  ```bash
  # 추천: Recharts 또는 Chart.js
  npm install recharts
  # 또는
  npm install chart.js react-chartjs-2
  ```

- [ ] **분석페이지 차트 구현**
  - 수익/비용 트렌드 차트
  - 사용자 증가 차트
  - 거래량 차트
  - 에너지 사용량 차트

### 4. TronLink 지갑 연동 고도화 (우선순위: 높음)
- [ ] **지갑 연결 개선**
  - 자동 재연결
  - 네트워크 변경 감지
  - 계정 변경 처리

- [ ] **트랜잭션 처리**
  - 에너지 대여 트랜잭션
  - 수수료 징수 트랜잭션
  - 트랜잭션 상태 모니터링

### 5. 보안 및 인증 (우선순위: 높음)
- [ ] **JWT 토큰 관리**
  - 토큰 자동 갱신
  - 만료 처리
  - 로그아웃 처리

- [ ] **권한 기반 접근 제어**
  - 페이지별 권한 체크
  - 기능별 권한 분리
  - 관리자 레벨 구분

## 🛠 즉시 시작할 수 있는 작업

### 1단계: API 연동 준비
```bash
# 환경 변수 설정
cp .env.example .env.local
# API_URL과 기본 설정 입력
```

### 2단계: API 클라이언트 개선
- `src/lib/api.ts`에서 실제 API 엔드포인트 연결
- 현재 폴백 데이터를 실제 API 응답으로 대체

### 3단계: 차트 라이브러리 설치
```bash
npm install recharts
npm install @types/recharts
```

### 4단계: 분석페이지 차트 구현
- 현재 placeholder를 실제 차트로 교체

## 📁 생성해야 할 파일들

```
src/
├── lib/
│   ├── api-client.ts      # 실제 API 클라이언트
│   ├── auth.ts           # 인증 관리
│   └── websocket.ts      # WebSocket 연결
├── components/
│   ├── charts/           # 차트 컴포넌트들
│   └── auth/            # 인증 관련 컴포넌트
└── hooks/
    ├── useAuth.ts        # 인증 훅
    └── useWebSocket.ts   # WebSocket 훅
```

## 🚀 권장 진행 순서

1. **환경 설정** (30분)
   - 환경 변수 파일 생성
   - API URL 설정

2. **API 연동** (2-3시간)
   - 실제 API 엔드포인트 연결
   - 기본 CRUD 작업 구현

3. **차트 구현** (2-3시간)
   - Recharts 설치 및 기본 차트 구현
   - 분석페이지 차트 교체

4. **실시간 기능** (4-5시간)
   - WebSocket 연결
   - 실시간 데이터 업데이트

5. **인증 고도화** (2-3시간)
   - JWT 관리 개선
   - 권한 체크 강화

## 💡 다음 명령어로 시작하세요

```bash
# Phase 2 시작
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm install recharts @types/recharts
```

---
*Phase 2 예상 소요시간: 12-15시간*
*완료 후 Phase 3: 고급 기능 및 배포 준비*
