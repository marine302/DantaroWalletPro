# 🚀 DantaroWallet Pro 개발환경 시작 가이드

## ⚡ 빠른 시작 (권장)

### 1. 전체 시스템 시작
```bash
# 프로젝트 루트에서
./dev-manager.sh start-all

# 상태 확인
./dev-manager.sh status
```

### 2. 브라우저에서 확인
- **슈퍼어드민 대시보드**: http://localhost:3020
- **백엔드 API 문서**: http://localhost:8000/docs
- **백엔드 헬스체크**: http://localhost:8000/health

## 🔧 개별 서버 관리

### 백엔드만 시작
```bash
./dev-manager.sh start-backend
# 또는
cd dantarowallet && ./start_backend.sh
```

### 프론트엔드만 시작
```bash
./dev-manager.sh start-frontend
# 또는
cd frontend/super-admin-dashboard && ./start_frontend.sh
```

### 모든 서버 중지
```bash
./dev-manager.sh stop-all
```

## 🧪 API 테스트

### 자동 테스트
```bash
./dev-manager.sh test-api
```

### 수동 테스트
```bash
# 헬스체크
curl http://localhost:8000/health

# 시스템 상태
curl http://localhost:8000/api/v1/superadmin/system-health

# 대시보드 통계
curl http://localhost:8000/api/v1/superadmin/dashboard/stats
```

## ⚠️ 문제 해결

### 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
lsof -i:8000  # 백엔드 포트
lsof -i:3020  # 프론트엔드 포트

# 강제 종료
./dev-manager.sh stop-all
```

### 백엔드 의존성 문제
```bash
cd dantarowallet
source .venv/bin/activate
python3 -c "from app.main import app; print('✅ 백엔드 import 성공')"
```

### 프론트엔드 의존성 문제
```bash
cd frontend/super-admin-dashboard
npm install
npx next --version
```

## 📊 개발 상태

### ✅ 완료된 기능
- 백엔드 API 서버 (98% 완성)
- 포트 관리 중앙화
- 자동화된 서버 관리
- API 연결성 검증

### 🚧 진행 중
- 프론트엔드 API 연동 (80% 완성)
- 실제 데이터 처리 개선

### 📝 다음 단계
1. 프론트엔드 API 연동 완성
2. 로그인/인증 시스템 연결
3. 실제 데이터베이스 연동 테스트

---

**개발 관련 문의**: 이슈 생성 또는 개발팀 연락
