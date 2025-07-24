# 🚀 **프론트엔드 개발자 빠른 시작 가이드**

DantaroWallet 프론트엔드 개발을 위한 빠른 시작 가이드입니다.

---

## ⚡ **30초 빠른 시작**

```bash
# 1️⃣ 백엔드 서버 실행
make dev-server

# 2️⃣ API 연결 테스트
make frontend-test

# 3️⃣ 프론트엔드 개발 환경 완전 준비
make frontend-ready
```

**완료!** 이제 역할별 API 문서에 접속하세요:

- 🔐 **Super Admin**: http://localhost:8000/api/v1/admin/docs
- 🔗 **Partner Admin**: http://localhost:8000/api/v1/partner/docs
- 🌟 **개발/테스트**: http://localhost:8000/api/v1/dev/docs

---

## 🎯 **역할별 개발 가이드**

### **🔐 Super Admin Dashboard 개발팀**

```bash
# TypeScript API 클라이언트 확인
ls frontend/super-admin-dashboard/src/lib/api-client.ts

# 예제 코드 확인
ls frontend/super-admin-dashboard/src/examples/

# Super Admin API만 테스트
make frontend-test-super-admin
```

**사용할 API 엔드포인트**:
- ⚡ 에너지 관리: `/api/v1/admin/energy/*`
- 👥 파트너 관리: `/api/v1/admin/partners/*`
- 📊 대시보드: `/api/v1/admin/dashboard/*`
- 💰 수수료 관리: `/api/v1/admin/fees/*`
- 💾 백업 관리: `/api/v1/admin/backup*`

### **🔗 Partner Admin Template 개발팀**

```bash
# TypeScript API 클라이언트 확인
ls frontend/partner-admin-template/src/lib/api-client.ts

# 예제 코드 확인
ls frontend/partner-admin-template/src/examples/

# Partner Admin API만 테스트
make frontend-test-partner-admin
```

**사용할 API 엔드포인트**:
- 🔗 TronLink 연동: `/api/v1/tronlink/*`
- ⚡ 에너지 렌탈: `/api/v1/partner/energy-rental/*`
- 💰 수수료 정책: `/api/v1/fee-policy/*`
- 🎯 에너지 관리: `/api/v1/energy-management/*`

---

## 📚 **TypeScript API 클라이언트 사용법**

### **Super Admin Dashboard 예제**

```typescript
import { SuperAdminApiClient } from './lib/api-client';

const client = new SuperAdminApiClient({
  baseURL: 'http://localhost:8000'
});

// 인증 토큰 설정
client.setAuthToken('your-jwt-token');

// 에너지 풀 상태 조회
const energyStatus = await client.energy.getStatus();

// 파트너에게 에너지 할당
await client.energyRental.allocateToPartner({
  partner_id: 'partner-123',
  amount: 1000000,
  duration_hours: 24
});
```

### **Partner Admin Template 예제**

```typescript
import { PartnerAdminApiClient } from './lib/api-client';

const client = new PartnerAdminApiClient({
  baseURL: 'http://localhost:8000'
});

// TronLink 상태 확인
const tronlinkStatus = await client.tronlink.getStatus();

// 에너지 렌탈 요금 조회
const rates = await client.energyRental.getCurrentRates();

// 에너지 구매
await client.energyRental.purchaseEnergy({
  amount: 100000,
  duration_hours: 24,
  user_address: 'TYour-Address-Here'
});
```

---

## 🔧 **개발 도구**

### **API 문서 업데이트**
```bash
# API 변경 시 자동으로 TypeScript 타입 업데이트
make update-api-docs

# TypeScript 타입만 재생성
make generate-api-types
```

### **실시간 모니터링**
```bash
# API 요청 실시간 모니터링
make monitor-api

# 백엔드 상태 확인
make check-backend-status
```

### **테스트**
```bash
# 전체 API 테스트
make frontend-test

# 특정 역할 API만 테스트
make frontend-test-super-admin
make frontend-test-partner-admin
```

---

## 🌐 **API 문서 접근**

### **Swagger UI 문서**
- **Super Admin**: http://localhost:8000/api/v1/admin/docs
- **Partner Admin**: http://localhost:8000/api/v1/partner/docs
- **개발/테스트**: http://localhost:8000/api/v1/dev/docs
- **전체 API**: http://localhost:8000/api/v1/docs

### **OpenAPI JSON**
- **Super Admin**: http://localhost:8000/api/v1/admin/openapi.json
- **Partner Admin**: http://localhost:8000/api/v1/partner/openapi.json
- **개발/테스트**: http://localhost:8000/api/v1/dev/openapi.json

---

## 🔄 **실시간 데이터 연동**

### **WebSocket 연결**

```typescript
// Super Admin - 실시간 시스템 모니터링
const wsAdmin = new WebSocket('ws://localhost:8000/ws/admin/system');
wsAdmin.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('실시간 시스템 데이터:', data);
};

// Partner Admin - 실시간 에너지 상태
const wsPartner = new WebSocket('ws://localhost:8000/ws/partner/energy');
wsPartner.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('실시간 에너지 데이터:', data);
};
```

---

## 🚨 **문제 해결**

### **백엔드 서버가 안 되는 경우**
```bash
# 백엔드 상태 확인
make check-backend-status

# 백엔드 재시작
make dev-server
```

### **API 연결 에러**
```bash
# CORS 설정 확인
curl -H "Origin: http://localhost:3020" http://localhost:8000/health

# 전체 API 테스트
make frontend-test
```

### **TypeScript 타입 에러**
```bash
# 최신 API 타입 재생성
make update-api-docs
```

---

## 📁 **파일 구조**

```
frontend/
├── super-admin-dashboard/          # 🔐 Super Admin (포트 3020)
│   ├── src/lib/api-client.ts      # TypeScript API 클라이언트
│   ├── src/lib/api-classification.ts # API 분류
│   └── src/examples/              # 사용 예제
└── partner-admin-template/        # 🔗 Partner Admin (포트 3030)
    ├── src/lib/api-client.ts      # TypeScript API 클라이언트
    ├── src/lib/api-classification.ts # API 분류
    └── src/examples/              # 사용 예제

docs/
├── FRONTEND_DEVELOPMENT_GUIDE.md  # 상세 개발 가이드
├── API_REFERENCE_BY_ROLE.md      # 역할별 API 참조
└── SIMPLE_ENERGY_SERVICE.md      # Simple Energy Service 가이드
```

---

## 🎉 **다음 단계**

1. **백엔드 실행**: `make dev-server`
2. **API 테스트**: `make frontend-test`
3. **문서 확인**: 위의 Swagger UI 링크 접속
4. **TypeScript 클라이언트**: `frontend/*/src/lib/api-client.ts` 확인
5. **예제 코드**: `frontend/*/src/examples/` 확인
6. **프론트엔드 시작**: 각 프론트엔드 프로젝트에서 `npm run dev`

---

## 📞 **지원 및 문의**

- **실시간 모니터링**: `make monitor-api`
- **백엔드 로그**: `tail -f server.log`
- **상세 가이드**: `docs/FRONTEND_DEVELOPMENT_GUIDE.md`
- **API 참조**: `docs/API_REFERENCE_BY_ROLE.md`

**✅ 프론트엔드 개발팀이 역할별로 구분된 API를 쉽게 사용할 수 있는 완전한 환경이 준비되었습니다!**
