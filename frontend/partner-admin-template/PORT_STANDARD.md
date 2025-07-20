# 🔧 DantaroWallet 프로젝트 포트 표준

**최종 업데이트**: 2025년 7월 20일  
**관리 스크립트**: `/dev-manager.sh`  
**표준 문서**: 이 파일

---

## 📋 **표준 포트 할당**

### **🔒 고정 포트 (절대 변경 금지)**

| 서비스 | 포트 | 설명 | 접속 URL |
|--------|------|------|----------|
| **백엔드 API** | `8000` | FastAPI + Uvicorn | http://localhost:8000 |
| **Super Admin** | `3020` | Next.js (슈퍼 관리자) | http://localhost:3020 |
| **Partner Admin** | `3030` | Next.js (파트너 관리자) | http://localhost:3030 |

### **🌐 API 엔드포인트**

| 용도 | URL | 설명 |
|------|-----|------|
| API 문서 | http://localhost:8000/docs | FastAPI Swagger UI |
| API 대체 문서 | http://localhost:8000/redoc | ReDoc |
| 헬스 체크 | http://localhost:8000/health | 서버 상태 확인 |

---

## 🔧 **포트 관리**

### **자동 포트 관리**
```bash
# 루트에서 모든 서버 시작 (표준 포트 사용)
./dev-manager.sh start

# 포트 상태 확인
./dev-manager.sh ports

# 포트 충돌 해결
./dev-manager.sh ports clean
```

### **개별 서버 시작**
```bash
# 백엔드만 (포트 8000)
./dev-manager.sh backend

# Super Admin만 (포트 3020)  
./dev-manager.sh super

# Partner Admin만 (포트 3030)
./dev-manager.sh partner
```

---

## ⚠️ **중요 사항**

### **절대 변경 금지**
- 이 포트 표준은 **모든 DantaroWallet 개발자**가 따라야 합니다
- 포트를 임의로 변경하면 **시스템 통합에 문제**가 발생합니다
- 모든 환경 설정 파일이 **이 포트를 기준**으로 구성되어 있습니다

### **포트 충돌 시 대처방법**
1. **다른 서비스 중지**: 해당 포트를 사용하는 다른 프로세스 종료
2. **dev-manager.sh 사용**: `./dev-manager.sh ports clean`
3. **수동 해결**: `lsof -ti:포트번호 | xargs kill -9`

### **환경 별 설정**

#### **개발 환경**
```env
# .env.local (프론트엔드)
PORT=3030
NEXT_PUBLIC_FRONTEND_PORT=3030
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

#### **프로덕션 환경**
```env
# .env.production
PORT=3030
NEXT_PUBLIC_API_BASE_URL=https://api.dantarowallet.com
NEXT_PUBLIC_WS_URL=wss://api.dantarowallet.com/ws
```

---

## 📚 **관련 파일**

### **포트 관리 스크립트**
- `/dev-manager.sh` - 메인 개발 환경 관리
- `/frontend/partner-admin-template/port-manager.js` - Partner Admin 포트 관리
- `/frontend/super-admin-dashboard/port-manager.js` - Super Admin 포트 관리

### **환경 설정 파일**
- `/.env` - 루트 환경 변수
- `/dantarowallet/.env` - 백엔드 환경 변수
- `/frontend/partner-admin-template/.env.local` - Partner Admin 환경 변수
- `/frontend/super-admin-dashboard/.env.local` - Super Admin 환경 변수

---

## 🔍 **포트 상태 확인**

```bash
# 현재 사용 중인 포트 확인
lsof -i :8000  # 백엔드
lsof -i :3020  # Super Admin
lsof -i :3030  # Partner Admin

# 모든 DantaroWallet 포트 확인
lsof -i :8000,:3020,:3030
```

---

## 🚀 **빠른 시작**

```bash
# 1. 루트 디렉토리로 이동
cd /Users/danielkwon/DantaroWalletPro

# 2. 모든 서비스 시작 (표준 포트 사용)
./dev-manager.sh start

# 3. 접속 확인
# - 백엔드: http://localhost:8000/docs
# - Super Admin: http://localhost:3020  
# - Partner Admin: http://localhost:3030
```

**이 표준을 따르면 DantaroWallet 프로젝트의 모든 서비스가 완벽하게 연동됩니다!** 🎯
