# 🔗 실제 백엔드 API 호출이 필요한 작업 목록

**작성일**: 2025년 7월 21일  
**목적**: 현재 프론트엔드에서 실제 백엔드 API를 호출해야 하는 모든 작업 분석

---

## 📋 **백엔드 API 호출이 필요한 주요 영역**

### **1. 📊 대시보드 및 시스템 관리**

#### **메인 대시보드** (`src/app/page.tsx`)
```typescript
// 현재 호출 중인 API들:
apiClient.getDashboardStats()       // ✅ 구현됨
apiClient.getSystemHealth()         // ✅ 구현됨  
apiClient.getPartners(1, 5)         // ✅ 구현됨
```

#### **통합 대시보드** (`src/app/integrated-dashboard/page.tsx`)
```typescript
// 현재 Fallback 방식으로 구현:
fetch(`${apiUrl}/api/v1/integrated-dashboard/dashboard/${partnerId}`)  // 🟡 백엔드 미완성

// Fallback 호출:
fetch(`http://localhost:3001/api/integrated-dashboard/${partnerId}`)  // Mock 서버
```

#### **API 라우트** (`src/app/api/dashboard/route.ts`)
```typescript
// 백엔드 프록시 역할:
fetch('http://localhost:8000/api/v1/integrated-dashboard/summary')  // 🟡 백엔드 미완성
```

### **2. 👥 파트너 관리**

#### **파트너 목록** (`src/app/partners/page.tsx`)
```typescript
// 실제 호출 중:
const response = await apiClient.getPartners();  // ✅ 구현됨
```

#### **파트너 온보딩** (`src/services/super-admin-service.ts`)
```typescript
// 백엔드 API 호출 필요:
apiClient.get(`/partner-onboarding/partners?page=${page}&limit=${limit}`)
apiClient.get('/partner-onboarding/stats')
apiClient.post(`/partner-onboarding/partners/${partnerId}/approve`)
apiClient.post(`/partner-onboarding/partners/${partnerId}/reject`, { reason })
apiClient.post(`/partner-onboarding/partners/${partnerId}/advance-stage`)
apiClient.put(`/partner-onboarding/partners/${partnerId}/risk-score`, { riskScore })
```

### **3. 🔋 에너지 관리 시스템**

#### **TronNRG 서비스** (`src/services/tron-nrg-service.ts`)
```typescript
// 현재 외부 API 직접 호출 (백엔드로 이전 필요):
this.baseURL = 'https://api.tronnrg.com/v1'  // 🔴 백엔드로 이전 필요

// 변경 예정:
this.baseURL = process.env.NEXT_PUBLIC_BACKEND_API_URL + '/energy/external/tronnrg'
```

#### **외부 에너지 공급자** (`src/services/super-admin-service.ts`)
```typescript
// 백엔드 API 호출 필요:
apiClient.get('/external-energy/providers')
apiClient.get('/external-energy/market-stats')
apiClient.post('/external-energy/purchase', purchase)
apiClient.get('/external-energy/purchase')
apiClient.put(`/external-energy/providers/${providerId}`, { isActive })
```

### **4. 🔒 감사 및 컴플라이언스**

#### **감사 시스템** (`src/services/super-admin-service.ts`)
```typescript
// 백엔드 API 호출 필요:
apiClient.get(`/audit/logs?page=${page}&limit=${limit}`)
apiClient.get('/audit/compliance-stats')
apiClient.get('/audit/suspicious-activities')
apiClient.put(`/audit/suspicious-activities/${id}`, { status })
```

### **5. 🔐 인증 및 권한 관리**

#### **API 클라이언트** (`src/lib/api.ts`)
```typescript
// 모든 API 호출에 JWT 토큰 필요:
Authorization: `Bearer ${token}`

// 인증 관련 엔드포인트:
this.client.post('/auth/login', credentials)
this.client.get('/admin/dashboard/stats')
this.client.get('/admin/system/health')
this.client.get('/partners/')
this.client.post('/admin/partners', data)
this.client.get('/admin/energy/pool')
this.client.post('/admin/energy/recharge', { amount })
this.client.get('/admin/fees/configs')
this.client.get('/admin/system/admins')
```

---

## 🚨 **백엔드 개발이 시급한 API 엔드포인트**

### **Phase 1: 핵심 시스템 API (최우선)**

#### **1. 인증 및 세션 관리**
```
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

#### **2. 대시보드 데이터**
```
GET /api/v1/admin/dashboard/stats
GET /api/v1/admin/system/health
GET /api/v1/integrated-dashboard/dashboard/{partnerId}
GET /api/v1/integrated-dashboard/summary
```

#### **3. 파트너 관리**
```
GET  /api/v1/partners/
POST /api/v1/admin/partners
GET  /api/v1/partners/{id}
PUT  /api/v1/admin/partners/{id}
DELETE /api/v1/admin/partners/{id}
```

### **Phase 2: 에너지 시스템 API**

#### **4. 에너지 관리**
```
GET  /api/v1/admin/energy/pool
POST /api/v1/admin/energy/recharge
POST /api/v1/admin/energy/allocate
GET  /api/v1/admin/energy/transactions
```

#### **5. 외부 에너지 공급자** (TronNRG 등)
```
GET  /api/v1/energy/external/tronnrg/market/price
GET  /api/v1/energy/external/tronnrg/market/data
GET  /api/v1/energy/external/tronnrg/providers
POST /api/v1/energy/external/tronnrg/order
WS   /ws/energy/tronnrg  (WebSocket)
```

### **Phase 3: 고급 기능 API**

#### **6. 감사 및 컴플라이언스**
```
GET /api/v1/audit/logs
GET /api/v1/audit/compliance-stats
GET /api/v1/audit/suspicious-activities
PUT /api/v1/audit/suspicious-activities/{id}
```

#### **7. 파트너 온보딩**
```
GET  /api/v1/partner-onboarding/partners
GET  /api/v1/partner-onboarding/stats
POST /api/v1/partner-onboarding/partners/{id}/approve
POST /api/v1/partner-onboarding/partners/{id}/reject
POST /api/v1/partner-onboarding/partners/{id}/advance-stage
PUT  /api/v1/partner-onboarding/partners/{id}/risk-score
```

#### **8. 수수료 관리**
```
GET  /api/v1/admin/fees/configs
POST /api/v1/admin/fees/configs
PUT  /api/v1/admin/fees/configs/{id}
DELETE /api/v1/admin/fees/configs/{id}
GET  /api/v1/admin/fees/revenue
```

#### **9. 시스템 관리자**
```
GET  /api/v1/admin/system/admins
POST /api/v1/admin/system/admins
PUT  /api/v1/admin/system/admins/{id}
DELETE /api/v1/admin/system/admins/{id}
```

---

## 🔄 **현재 상태별 분류**

### **✅ 프론트엔드 구현 완료 (백엔드 대기 중)**
- 모든 API 클라이언트 코드 완성 (`src/lib/api.ts`)
- TronNRG 외부 API 연동 완료 (백엔드 이전 준비됨)
- 감사 시스템 UI/UX 완료
- 파트너 관리 페이지 완료
- 대시보드 페이지 완료

### **🟡 임시 구현 (Mock/Fallback 사용 중)**
- 통합 대시보드: Mock 서버 fallback 사용
- API 라우트: 백엔드 프록시 역할만
- 일부 서비스: `super-admin-service.ts`에서 API 호출 대기

### **🔴 백엔드 의존적 (즉시 개발 필요)**
- 모든 인증 및 세션 관리
- 실제 데이터베이스 연동
- 외부 API 중계 서비스 (TronNRG 등)
- WebSocket 실시간 통신

---

## ⚡ **개발 우선순위 권장사항**

1. **최우선**: 인증 시스템 + 기본 대시보드 API
2. **2순위**: 파트너 관리 + 에너지 풀 관리 API  
3. **3순위**: 외부 에너지 공급자 API (TronNRG 중계)
4. **4순위**: 감사/컴플라이언스 + 고급 기능 API

백엔드 개발 완료 시 `./scripts/migrate-to-backend.sh`로 즉시 연동 가능합니다! 🚀
