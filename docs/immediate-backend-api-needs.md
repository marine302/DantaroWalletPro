# 🎯 즉시 백엔드 개발이 필요한 실제 사용 중인 API 목록

**작성일**: 2025년 7월 21일  
**분석 기준**: 현재 프론트엔드에서 실제로 호출하고 있는 API들

---

## 🚨 **현재 실제 사용 중인 백엔드 API 호출**

### **1. 메인 대시보드** (`src/app/page.tsx`) - ⚡ **즉시 필요**

```typescript
// 현재 useQuery로 실제 호출 중:
useQuery({
  queryKey: ['dashboard-stats'],
  queryFn: () => apiClient.getDashboardStats(),  // ❌ 백엔드 없으면 에러
  refetchInterval: 30000,
});

useQuery({
  queryKey: ['system-health'],
  queryFn: () => apiClient.getSystemHealth(),    // ❌ 백엔드 없으면 에러
  refetchInterval: 10000,
});

useQuery({
  queryKey: ['recent-partners'],
  queryFn: () => apiClient.getPartners(1, 5),    // ❌ 백엔드 없으면 에러
  refetchInterval: 60000,
});
```

**백엔드 API 엔드포인트 필요:**
- `GET /api/v1/admin/dashboard/stats`
- `GET /api/v1/admin/system/health`  
- `GET /api/v1/partners/?page=1&size=5`

### **2. 파트너 관리** (`src/app/partners/page.tsx`) - ⚡ **즉시 필요**

```typescript
// 현재 실제 호출 중:
const response = await apiClient.getPartners();  // ❌ 백엔드 없으면 에러
```

**백엔드 API 엔드포인트 필요:**
- `GET /api/v1/partners/`

### **3. 통합 대시보드** (`src/app/integrated-dashboard/page.tsx`) - 🟡 **Fallback 있음**

```typescript
// 현재 실제 시도 중 (Fallback 있음):
const response = await fetch(`${apiUrl}/api/v1/integrated-dashboard/dashboard/${partnerId}`)

// Fallback으로 Mock 서버 호출:
response = await fetch(`http://localhost:3001/api/integrated-dashboard/${partnerId}`)
```

**백엔드 API 엔드포인트 필요:**
- `GET /api/v1/integrated-dashboard/dashboard/{partnerId}`

### **4. Next.js API 라우트** (`src/app/api/dashboard/route.ts`) - 🟡 **프록시 역할**

```typescript
// 백엔드로 프록시 호출:
const response = await fetch('http://localhost:8000/api/v1/integrated-dashboard/summary')
```

**백엔드 API 엔드포인트 필요:**
- `GET /api/v1/integrated-dashboard/summary`

---

## 🔧 **API 클라이언트에서 정의된 모든 엔드포인트** (`src/lib/api.ts`)

### **인증 관련**
```typescript
POST /auth/login              // login(), superAdminLogin()
```

### **대시보드 관련**  
```typescript
GET /admin/dashboard/stats    // getDashboardStats()
GET /admin/system/health      // getSystemHealth()
```

### **파트너 관리**
```typescript
GET    /partners/                        // getPartners()
GET    /partners/{id}                    // getPartner()
POST   /admin/partners                   // createPartner()
PUT    /admin/partners/{id}              // updatePartner()
DELETE /admin/partners/{id}              // deletePartner()
GET    /admin/partners/{id}/config       // getPartnerConfig()
GET    /admin/partners/{id}/statistics   // getPartnerStatistics()
```

### **에너지 관리**
```typescript
GET  /admin/energy/pool          // getEnergyPool()
POST /admin/energy/recharge      // rechargeEnergy()
POST /admin/energy/allocate      // allocateEnergy()
GET  /admin/energy/transactions  // getEnergyTransactions()
```

### **수수료 관리**
```typescript
GET    /admin/fees/configs     // getFeeConfigs()
POST   /admin/fees/configs     // createFeeConfig()
PUT    /admin/fees/configs/{id} // updateFeeConfig()
DELETE /admin/fees/configs/{id} // deleteFeeConfig()
GET    /admin/fees/revenue     // getFeeRevenue()
```

### **시스템 관리자**
```typescript
GET    /admin/system/admins     // getSystemAdmins()
POST   /admin/system/admins     // createSystemAdmin()
PUT    /admin/system/admins/{id} // updateSystemAdmin()
DELETE /admin/system/admins/{id} // deleteSystemAdmin()
```

---

## 🔥 **SuperAdminService에서 정의된 추가 API** (`src/services/super-admin-service.ts`)

### **감사 및 컴플라이언스**
```typescript
GET /audit/logs                               // getAuditLogs()
GET /audit/compliance-stats                   // getComplianceStats()
GET /audit/suspicious-activities              // getSuspiciousActivities()
PUT /audit/suspicious-activities/{id}         // updateSuspiciousActivityStatus()
```

### **외부 에너지 시장**
```typescript
GET  /external-energy/providers               // getEnergyProviders()
GET  /external-energy/market-stats            // getMarketStats()
POST /external-energy/purchase                // createEnergyPurchase()
GET  /external-energy/purchase                // getEnergyPurchases()
PUT  /external-energy/providers/{id}          // updateProviderStatus()
```

### **파트너 온보딩**
```typescript
GET  /partner-onboarding/partners            // getPartners()
GET  /partner-onboarding/stats               // getOnboardingStats()
POST /partner-onboarding/partners/{id}/approve        // approvePartner()
POST /partner-onboarding/partners/{id}/reject         // rejectPartner()
POST /partner-onboarding/partners/{id}/advance-stage  // advancePartnerStage()
PUT  /partner-onboarding/partners/{id}/risk-score     // updatePartnerRiskScore()
```

---

## 🚀 **TronNRG 외부 API 중계** (백엔드 이전 필요)

### **현재 프론트엔드에서 직접 호출** (`src/services/tron-nrg-service.ts`)
```typescript
// 현재: 직접 외부 API 호출
this.baseURL = 'https://api.tronnrg.com/v1'

// 변경 필요: 백엔드 경유
this.baseURL = process.env.NEXT_PUBLIC_BACKEND_API_URL + '/energy/external/tronnrg'
```

**백엔드에서 구현해야 할 중계 API:**
```typescript
GET  /api/v1/energy/external/tronnrg/market/price     // getCurrentPrice()
GET  /api/v1/energy/external/tronnrg/market/data      // getMarketData()
GET  /api/v1/energy/external/tronnrg/providers        // getProviders()
POST /api/v1/energy/external/tronnrg/order           // createOrder()
GET  /api/v1/energy/external/tronnrg/orders          // getOrderHistory()
WS   /ws/energy/tronnrg                               // WebSocket 실시간 스트리밍
```

---

## ⚡ **개발 우선순위 (실사용 기준)**

### **🔴 최긴급 (현재 에러 발생 중)**
1. **메인 대시보드 API** - 매 10-60초마다 호출 중
   - `GET /api/v1/admin/dashboard/stats`
   - `GET /api/v1/admin/system/health`
   - `GET /api/v1/partners/?page=1&size=5`

2. **파트너 관리 API**
   - `GET /api/v1/partners/`

3. **기본 인증 API**
   - `POST /api/v1/auth/login`

### **🟡 2순위 (Fallback 있지만 필요)**
4. **통합 대시보드 API**
   - `GET /api/v1/integrated-dashboard/dashboard/{partnerId}`
   - `GET /api/v1/integrated-dashboard/summary`

### **🟢 3순위 (정의만 되어 있음)**
5. **에너지 관리 API**
6. **수수료 관리 API**  
7. **시스템 관리자 API**
8. **감사/컴플라이언스 API**
9. **외부 에너지 시장 API**
10. **파트너 온보딩 API**

### **🔄 4순위 (외부 API 중계)**
11. **TronNRG API 중계** - 현재 프론트엔드에서 직접 호출 중

---

## 💡 **권장사항**

1. **1단계**: 메인 대시보드 + 파트너 관리 + 인증 API 우선 개발
2. **2단계**: 통합 대시보드 API 개발  
3. **3단계**: 나머지 관리 API들 순차 개발
4. **4단계**: TronNRG 외부 API 중계 시스템 구축

백엔드 개발 완료 시 `./scripts/migrate-to-backend.sh http://backend-url:8000`으로 즉시 연동 가능합니다! 🚀
