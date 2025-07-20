# 🚀 Phase 2 시작 가이드

**시작 전 체크리스트**: Phase 1 완료 ✅  
**현재 상태**: 파트너 관리자 템플릿 프론트엔드 85% 완료  
**다음 목표**: 백엔드 실제 연동 및 운영 환경 구축

---

## 📋 **Phase 2 개발 계획**

### **🎯 목표**: 완전한 운영 시스템 구축

#### **2.1 백엔드 실제 연동 (우선순위 1)**

```bash
# 1. 환경 설정
cd /Users/danielkwon/DantaroWalletPro/frontend/partner-admin-template

# 2. 환경 변수 생성
cp .env.example .env.local

# 3. 백엔드 API 엔드포인트 설정
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

**필요한 작업**:
- ✅ `src/lib/api.ts`에서 `BASE_URL` 실제 백엔드로 변경
- ✅ API 인증 토큰 시스템 구현
- ✅ 실제 API 응답에 맞춰 타입 정의 조정
- ✅ 에러 처리 강화 (네트워크 오류, 인증 오류 등)

#### **2.2 실시간 WebSocket 연동 (우선순위 2)**

**새로 구현해야 할 파일**:
```
src/lib/websocket.ts          # WebSocket 클라이언트
src/hooks/useWebSocket.ts     # WebSocket React 훅
src/contexts/WebSocketContext.tsx  # WebSocket Provider
```

**연동 대상**:
- 실시간 에너지 모니터링 (`/energy`)
- 실시간 출금 상태 업데이트 (`/withdrawals`) 
- 실시간 알림 시스템 (`/notifications`)
- 실시간 사용자 활동 (`/users`)

#### **2.3 인증 및 보안 시스템 (우선순위 3)**

**구현해야 할 기능**:
- JWT 토큰 관리
- 자동 토큰 갱신
- 권한별 페이지 접근 제어
- API 요청 인증 헤더 자동 추가

#### **2.4 운영 환경 구축 (우선순위 4)**

```bash
# 프로덕션 빌드 최적화
npm run build
npm run start

# 환경별 설정 분리
.env.development
.env.staging  
.env.production
```

---

## 🛠️ **Phase 2 시작 명령어**

### **Step 1: 개발 환경 시작**

```bash
# 터미널 1: 백엔드 서버 실행
cd /Users/danielkwon/DantaroWalletPro/dantarowallet
python -m uvicorn app.main:app --reload --port 8000

# 터미널 2: 프론트엔드 개발 서버 실행
cd /Users/danielkwon/DantaroWalletPro/frontend/partner-admin-template
npm run dev
```

### **Step 2: 실제 API 연동 테스트**

```bash
# 백엔드 API 상태 확인
curl http://localhost:8000/api/v1/health

# 파트너 API 테스트
curl http://localhost:8000/api/v1/partner/dashboard

# WebSocket 연결 테스트  
wscat -c ws://localhost:8000/ws
```

### **Step 3: 단계별 구현**

1. **API 클라이언트 실제 연동** (1일)
   - `src/lib/api.ts` BASE_URL 변경
   - 실제 API 응답 구조에 맞춰 타입 수정
   - 토큰 인증 시스템 추가

2. **WebSocket 실시간 연동** (1-2일)
   - WebSocket 클라이언트 구현
   - 실시간 데이터 업데이트 적용
   - 재연결 로직 구현

3. **운영 환경 설정** (0.5일)
   - 환경 변수 분리
   - 프로덕션 빌드 최적화
   - 로깅 및 모니터링 설정

---

## 📁 **주요 수정 대상 파일**

### **즉시 수정 필요**
```
src/lib/api.ts                # BASE_URL 변경
src/lib/hooks.ts              # 실제 API 연동
.env.local                    # 환경 변수 설정
```

### **신규 구현 필요**
```
src/lib/websocket.ts          # WebSocket 클라이언트
src/hooks/useWebSocket.ts     # WebSocket 훅
src/contexts/WebSocketContext.tsx  # WebSocket Provider
src/lib/auth.ts               # 인증 시스템
src/middleware.ts             # Next.js 미들웨어 (인증)
```

---

## 🎯 **성공 지표**

### **Phase 2 완료 조건**
- ✅ 모든 API가 실제 백엔드와 연동
- ✅ 실시간 데이터 업데이트 정상 작동
- ✅ 인증 시스템 완전 구현
- ✅ 프로덕션 환경 배포 준비 완료
- ✅ 모든 기능이 실제 데이터로 정상 작동

### **최종 목표**
- **완전한 운영 시스템** 구축
- **실시간 파트너 관리 대시보드** 완성
- **상용 서비스 출시** 준비 완료

---

## 🚀 **시작하기**

```bash
# Phase 2 시작!
echo "🚀 Phase 2: 백엔드 실제 연동 시작!"
echo "📂 작업 디렉토리: /Users/danielkwon/DantaroWalletPro/frontend/partner-admin-template"
echo "📋 다음 작업: 실제 API 엔드포인트 연동"
echo "🎯 목표: 완전한 운영 시스템 구축"

# 개발 서버 시작
npm run dev
```

**Phase 2가 완료되면 DantaroWallet 파트너 관리자 대시보드가 완전히 운영 가능한 상태가 됩니다!** 🎉
