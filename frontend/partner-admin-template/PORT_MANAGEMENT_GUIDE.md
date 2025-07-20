# 🔌 DantaroWallet 포트 설정 가이드

**중요**: 포트 설정은 시스템 전체에서 통일되어야 하므로 임의로 변경하지 마세요.

---

## 📋 **고정 포트 할당**

### **프론트엔드 서비스**
```bash
# 파트너 관리자 템플릿 (고정)
PORT: 3030
URL: http://localhost:3030
서비스: Partner Admin Template
```

### **백엔드 서비스**
```bash
# 메인 API 서버 (고정)
PORT: 8000
URL: http://localhost:8000
서비스: DantaroWallet API

# WebSocket 서버 (고정)  
PORT: 8001
URL: ws://localhost:8001
서비스: Real-time WebSocket
```

### **데이터베이스 서비스**
```bash
# PostgreSQL (고정)
PORT: 5432
URL: postgresql://localhost:5432
서비스: Main Database

# Redis (고정)
PORT: 6379  
URL: redis://localhost:6379
서비스: Cache & Sessions
```

---

## ⚙️ **포트 관리 시스템**

### **자동 포트 관리**
파트너 관리자 템플릿은 `port-manager.js`를 통해 포트를 자동 관리합니다:

```bash
# 개발 서버 시작 (자동으로 포트 3030 사용)
npm run dev

# 빌드 (포트 무관)
npm run build

# 프로덕션 서버 시작 (자동으로 포트 3030 사용)  
npm run start
```

### **포트 충돌 방지**
- 시작 시 포트 3030 사용 가능 여부 자동 확인
- 포트가 사용 중이면 명확한 오류 메시지 표시
- 다른 포트로 임의 변경 방지

### **환경 변수 강제 설정**
```bash
# .env.local에서 포트가 다르게 설정되어 있어도 자동으로 3030으로 수정
NEXT_PUBLIC_FRONTEND_PORT=3030  # 고정
PORT=3030                       # 고정
```

---

## 🚫 **포트 변경 금지 사항**

### **절대 변경하면 안 되는 이유**
1. **시스템 통합**: 다른 서비스들이 고정 포트를 참조
2. **문서 일관성**: 모든 문서가 고정 포트 기준으로 작성
3. **배포 안정성**: 운영 환경에서 포트 충돌 방지
4. **개발 효율성**: 팀원 간 동일한 환경 보장

### **포트 변경 시 발생하는 문제**
- 백엔드 API 연동 실패
- WebSocket 연결 실패  
- 문서와 실제 환경 불일치
- 팀 개발 환경 혼란

---

## 🔧 **포트 설정 파일**

### **주요 설정 파일**
```
📁 프로젝트 루트/
├── .env.local              # 로컬 환경 변수 (포트 포함)
├── .env.example            # 환경 변수 예시
├── port-manager.js         # 포트 관리 스크립트
└── package.json            # NPM 스크립트 설정
```

### **.env.local 필수 설정**
```bash
# 포트 설정 (고정 - 변경 금지)
NEXT_PUBLIC_FRONTEND_PORT=3030
PORT=3030

# API 백엔드 설정  
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=/api/v1
```

---

## 🆘 **포트 관련 문제 해결**

### **포트 3030이 사용 중인 경우**
```bash
# 1. 포트 사용 프로세스 확인
lsof -i :3030

# 2. 프로세스 종료 (PID 확인 후)
kill -9 <PID>

# 3. 다시 시작
npm run dev
```

### **환경 변수 문제**
```bash
# 1. .env.local 파일 확인
cat .env.local

# 2. 잘못 설정된 경우 올바른 값으로 수정
# (port-manager.js가 자동으로 수정하지만 수동으로도 가능)

# 3. 캐시 정리 후 재시작
rm -rf .next
npm run dev
```

### **포트 매니저 실행 오류**
```bash
# 1. Node.js 버전 확인
node --version  # v18+ 권장

# 2. 권한 확인  
chmod +x port-manager.js

# 3. 직접 실행 테스트
node port-manager.js dev
```

---

## 📞 **지원 및 문의**

포트 설정 관련 문제가 지속되면:
1. **PHASE_2_START_GUIDE.md** 참조
2. **개발팀 문의** (포트 변경 요청 금지)
3. **시스템 관리자 문의** (인프라 문제)

**중요**: 포트 설정은 시스템 안정성을 위해 절대 임의로 변경하지 마세요! 🚨
