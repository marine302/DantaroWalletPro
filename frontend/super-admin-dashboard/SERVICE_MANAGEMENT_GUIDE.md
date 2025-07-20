# 🚀 통합 서비스 관리자 가이드

Super Admin Dashboard의 모든 서비스(프론트엔드, Mock HTTP 서버, Mock WebSocket 서버)를 하나의 명령으로 관리할 수 있습니다.

## 🎯 빠른 시작

```bash
# 모든 서비스 시작
npm run dev

# 또는 스크립트 직접 실행
./manage-services.sh start
```

## 📋 사용 가능한 명령어

### npm scripts (권장)
```bash
npm run dev      # 모든 서비스 시작
npm run stop     # 모든 서비스 중지
npm run restart  # 모든 서비스 재시작
npm run status   # 서비스 상태 확인
npm run logs     # 서비스 로그 확인
```

### 직접 스크립트 실행
```bash
./manage-services.sh start    # 모든 서비스 시작
./manage-services.sh stop     # 모든 서비스 중지
./manage-services.sh restart  # 모든 서비스 재시작
./manage-services.sh status   # 서비스 상태 확인
./manage-services.sh logs     # 서비스 로그 확인
./manage-services.sh help     # 도움말
```

### 개별 서비스 관리
```bash
npm run frontend-only  # 프론트엔드만 시작
npm run mock-only      # 목업 서버들만 시작

# 또는
node port-manager.js dev                # 프론트엔드만
node unified-service-manager.js start   # 목업 서버들만
```

## 🌐 서비스 접속 정보

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Frontend** | http://localhost:3020 | Next.js 개발 서버 |
| **Mock HTTP API** | http://localhost:3001 | REST API 목업 서버 |
| **Mock WebSocket** | ws://localhost:3002 | 실시간 데이터 목업 서버 |

### Health Check 엔드포인트
- Mock HTTP: `http://localhost:3001/health`
- Mock WebSocket: 포트 연결 확인으로 상태 체크

## 🔧 설정 파일

### 자동 생성되는 설정 파일들
- `.service-config.json` - 통합 서비스 설정
- `.port-config.json` - 포트 설정 (기존)
- `.services.lock` - 서비스 락 파일
- `services.log` - 통합 로그 파일

### 환경 변수 (.env.local)
통합 관리자가 자동으로 업데이트합니다:
```bash
NEXT_PUBLIC_FRONTEND_PORT=3020
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3002
```

## 🛠️ 고급 기능

### 포트 자동 관리
- 포트 충돌 시 자동으로 다른 포트 할당
- 기존 프로세스 자동 종료 옵션
- 환경 변수 자동 업데이트

### 프로세스 관리
- 정상적인 shutdown 처리
- 백그라운드 프로세스 추적
- 크래시 감지 및 로깅

### 로그 관리
- 모든 서비스의 통합 로그
- 타임스탬프 포함
- 실시간 로그 확인 (`npm run logs`)

## 🚨 트러블슈팅

### 서비스가 시작되지 않을 때
```bash
# 현재 상태 확인
npm run status

# 모든 서비스 강제 종료 후 재시작
npm run stop
sleep 2
npm run start
```

### 포트 충돌 문제
```bash
# 포트 사용 현황 확인
npm run check-ports

# 특정 포트의 프로세스 확인
lsof -ti:3020  # 프론트엔드 포트
lsof -ti:3001  # Mock HTTP 포트
lsof -ti:3002  # Mock WebSocket 포트
```

### 로그 확인
```bash
# 실시간 로그 확인
npm run logs

# 또는 파일 직접 확인
tail -f services.log
```

## 📁 파일 구조

```
├── manage-services.sh           # 통합 관리 스크립트
├── unified-service-manager.js   # 목업 서버 통합 관리자
├── port-manager.js             # 프론트엔드 포트 관리자
├── mock-server.js              # HTTP API 목업 서버
├── mock-realtime-server.js     # WebSocket 목업 서버
├── .service-config.json        # 서비스 설정 (자동 생성)
├── .services.lock              # 서비스 락 파일 (자동 생성)
└── services.log                # 통합 로그 파일 (자동 생성)
```

## 🔄 마이그레이션 가이드

### 기존 방식에서 새 방식으로
**기존:**
```bash
npm run dev:with-mock  # concurrently 사용
```

**새 방식:**
```bash
npm run dev           # 통합 관리자 사용
```

### 이점
- ✅ 단일 명령으로 모든 서비스 관리
- ✅ 자동 포트 관리 및 충돌 해결
- ✅ 통합 로깅 및 상태 모니터링
- ✅ 정상적인 프로세스 종료 처리
- ✅ 환경 변수 자동 동기화

## 🎛️ 개발 워크플로우

### 일반적인 개발 시작
```bash
cd frontend/super-admin-dashboard
npm run dev
# 모든 서비스가 시작되고 브라우저에서 http://localhost:3020 접속
```

### 디버깅을 위한 개별 서비스 실행
```bash
# 터미널 1: 목업 서버들만
npm run mock-only

# 터미널 2: 프론트엔드만
npm run frontend-only
```

### 종료
```bash
# Ctrl+C (프론트엔드 터미널에서)
# 또는
npm run stop
```
