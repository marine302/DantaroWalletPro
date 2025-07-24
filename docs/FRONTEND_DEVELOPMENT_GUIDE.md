# 🚀 **프론트엔드 개발자 가이드**

DantaroWallet 프론트엔드 개발을 위한 완전한 가이드

---

## 📋 **프로젝트 구조**

```
frontend/
├── super-admin-dashboard/     # 🔐 Super Admin Dashboard (포트 3020)
│   ├── src/lib/api-classification.ts  # Super Admin API 타입
│   └── src/lib/api-client.ts          # Super Admin API 클라이언트
└── partner-admin-template/    # 🔗 Partner Admin Template (포트 3030)
    ├── src/lib/api-classification.ts  # Partner Admin API 타입
    └── src/lib/api-client.ts          # Partner Admin API 클라이언트
```

---

## 🎯 **역할별 API 문서 접근**

### **🔐 Super Admin Dashboard 개발팀**
- **Swagger UI**: http://localhost:8000/api/v1/admin/docs
- **OpenAPI JSON**: http://localhost:8000/api/v1/admin/openapi.json
- **프론트엔드 주소**: http://localhost:3020
- **주요 기능**: 시스템 관리, 파트너 관리, 에너지 풀 관리

### **🔗 Partner Admin Template 개발팀**
- **Swagger UI**: http://localhost:8000/api/v1/partner/docs
- **OpenAPI JSON**: http://localhost:8000/api/v1/partner/openapi.json
- **프론트엔드 주소**: http://localhost:3030
- **주요 기능**: TronLink 연동, 파트너 에너지 관리, 수수료 정책

### **🌟 개발/테스트 전용**
- **Swagger UI**: http://localhost:8000/api/v1/dev/docs
- **OpenAPI JSON**: http://localhost:8000/api/v1/dev/openapi.json
- **주요 기능**: Simple Energy Service, 테스트, 최적화

### **📋 전체 API (통합 개발용)**
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

---

## ⚡ **빠른 시작**

### **1️⃣ 백엔드 서버 실행**
```bash
cd /Users/danielkwon/DantaroWalletPro/dantarowallet
make dev-server
```

### **2️⃣ 프론트엔드 개발 환경 설정**

#### **Super Admin Dashboard**
```bash
cd frontend/super-admin-dashboard
npm install
npm run dev  # http://localhost:3020
```

#### **Partner Admin Template**
```bash
cd frontend/partner-admin-template
npm install
npm run dev  # http://localhost:3030
```

### **3️⃣ API 연결 테스트**
```bash
# 백엔드 상태 확인
curl http://localhost:8000/health

# Super Admin API 테스트
curl http://localhost:8000/api/v1/admin/dashboard/overview

# Partner Admin API 테스트
curl http://localhost:8000/api/v1/partner/energy-rental/current-rates
```

---

## 🔧 **TypeScript API 클라이언트 사용법**

### **Super Admin Dashboard 예시**
```typescript
import { SuperAdminApiClient } from './lib/api-client';
import { SUPER_ADMIN_APIS } from './lib/api-classification';

const client = new SuperAdminApiClient({
  baseURL: 'http://localhost:8000',
  timeout: 5000
});

// 에너지 풀 상태 조회
const energyStatus = await client.admin.energy.getStatus();

// 파트너 에너지 할당
await client.admin.energyRental.allocateToPartner({
  partnerId: 'partner-123',
  amount: 1000,
  durationHours: 24
});
```

### **Partner Admin Template 예시**
```typescript
import { PartnerAdminApiClient } from './lib/api-client';
import { PARTNER_ADMIN_APIS } from './lib/api-classification';

const client = new PartnerAdminApiClient({
  baseURL: 'http://localhost:8000',
  timeout: 5000
});

// TronLink 연결 상태 확인
const tronlinkStatus = await client.tronlink.getStatus();

// 에너지 렌탈 현재 요금 조회
const currentRates = await client.energyRental.getCurrentRates();
```

---

## 🔐 **인증 및 권한**

### **API 키 설정**
```typescript
// Super Admin
client.setAuthToken('super-admin-jwt-token');

// Partner Admin
client.setAuthToken('partner-admin-jwt-token');
```

### **역할별 권한 확인**
```typescript
// API 분류 확인
import { SUPER_ADMIN_APIS, PARTNER_ADMIN_APIS, COMMON_APIS } from './lib/api-classification';

// Super Admin만 접근 가능한 API인지 확인
const isSuperAdminOnly = SUPER_ADMIN_APIS.includes(apiTag);

// Partner Admin만 접근 가능한 API인지 확인
const isPartnerAdminOnly = PARTNER_ADMIN_APIS.includes(apiTag);

// 공통 API인지 확인
const isCommonApi = COMMON_APIS.includes(apiTag);
```

---

## 📊 **실시간 데이터 연동**

### **WebSocket 연결**
```typescript
// Super Admin Dashboard - 실시간 시스템 모니터링
const wsClient = new WebSocket('ws://localhost:8000/ws/admin/system');

wsClient.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('실시간 시스템 상태:', data);
};

// Partner Admin Template - 실시간 에너지 상태
const wsPartner = new WebSocket('ws://localhost:8000/ws/partner/energy');

wsPartner.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('실시간 에너지 상태:', data);
};
```

---

## 🧪 **개발 및 테스트**

### **API 연결 테스트 스크립트**
```bash
# 전체 API 연결 테스트
./test_frontend_requests.sh

# Super Admin API만 테스트
./test_frontend_requests.sh super-admin

# Partner Admin API만 테스트
./test_frontend_requests.sh partner-admin
```

### **Mock 데이터 사용**
```bash
# Simple Energy Service (개발용)
curl http://localhost:8000/api/v1/simple-energy/providers
curl http://localhost:8000/api/v1/simple-energy/simulate-purchase
```

---

## 🛠️ **개발 도구**

### **코드 생성 도구**
```bash
# API 타입 자동 생성
make generate-api-types

# 역할별 API 문서 업데이트
make update-api-docs
```

### **VS Code 설정**
```json
{
  "typescript.preferences.includePackageJsonAutoImports": "on",
  "typescript.suggest.autoImports": true,
  "api-client.baseURL": "http://localhost:8000",
  "api-client.timeout": 5000
}
```

---

## 📝 **API 엔드포인트 요약**

### **🔐 Super Admin 전용 API**
- **에너지 관리**: `/api/v1/admin/energy/*`
- **파트너 관리**: `/api/v1/admin/partners/*`
- **시스템 관리**: `/api/v1/admin/backup`, `/api/v1/admin/fees/*`
- **대시보드**: `/api/v1/admin/dashboard/*`

### **🔗 Partner Admin 전용 API**
- **TronLink**: `/api/v1/tronlink/*`
- **에너지 렌탈**: `/api/v1/partner/energy-rental/*`
- **수수료 정책**: `/api/v1/fee-policy/*`

### **🌟 공통 API**
- **인증**: `/api/v1/auth/*`
- **지갑**: `/api/v1/wallet/*`
- **거래**: `/api/v1/transactions/*`
- **잔액**: `/api/v1/balance/*`

---

## 🔄 **API 업데이트 워크플로우**

1. **백엔드 API 변경 시**:
   ```bash
   make update-api-docs  # 자동으로 TypeScript 타입 및 문서 업데이트
   ```

2. **프론트엔드에서 새 타입 적용**:
   ```bash
   cd frontend/super-admin-dashboard
   npm run type-check
   
   cd frontend/partner-admin-template
   npm run type-check
   ```

3. **API 변경사항 확인**:
   - Swagger UI에서 새 엔드포인트 확인
   - TypeScript 타입 정의 확인
   - 테스트 스크립트 실행

---

## 🚨 **문제 해결**

### **자주 발생하는 문제**

1. **CORS 에러**:
   ```bash
   # 백엔드 CORS 설정 확인
   curl -H "Origin: http://localhost:3020" http://localhost:8000/health
   ```

2. **API 경로 변경**:
   ```bash
   # 최신 API 문서 다시 생성
   make update-api-docs
   ```

3. **TypeScript 타입 에러**:
   ```bash
   # API 분류 파일 업데이트
   make generate-api-types
   ```

---

## 📞 **지원 및 문의**

- **API 문서**: http://localhost:8000/
- **백엔드 로그**: `tail -f server.log`
- **실시간 모니터링**: `./monitor_api_requests.sh`
- **개발 가이드라인**: `DEVELOPMENT_GUIDELINES.md`

---

**✅ 이제 프론트엔드 개발팀이 역할별로 구분된 API를 쉽게 사용할 수 있습니다!**
