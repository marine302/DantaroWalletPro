# 프론트엔드 마이그레이션 계획서

**작성일**: 2025년 7월 21일  
**목적**: 백엔드 API 완성 후 프론트엔드 수정 가이드  
**담당**: 프론트엔드 개발팀

---

## 📋 **수정 필요한 파일 목록**

### **1. 핵심 서비스 파일**
- ✅ `src/services/tron-nrg-service.ts` - **주요 수정 필요**
- ✅ `src/app/energy/external-market/page.tsx` - 일부 수정
- ✅ `src/app/energy/external-market/purchase/page.tsx` - 일부 수정

### **2. 설정 파일**
- ✅ `.env.local` - API 엔드포인트 변경
- ✅ `src/lib/api.ts` - 백엔드 API 클라이언트 설정

---

## 🔧 **상세 수정 계획**

### **1. API 엔드포인트 변경**

#### **Before (현재):**
```typescript
// src/services/tron-nrg-service.ts
private baseURL: string = 'https://api.tronnrg.com/v1';  // 직접 외부 API
```

#### **After (변경 후):**
```typescript
// src/services/tron-nrg-service.ts  
private baseURL: string = process.env.NEXT_PUBLIC_API_URL + '/api/v1/external-energy';  // 백엔드 API
```

### **2. 환경변수 설정**

#### **.env.local 추가:**
```bash
# 백엔드 API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
# 또는 프로덕션: https://api.dantarowallet.com

# 기존 TronNRG 설정은 제거 (백엔드에서 관리)
# NEXT_PUBLIC_TRONNRG_API_URL=  # 삭제
# NEXT_PUBLIC_TRONNRG_API_KEY=  # 삭제
```

### **3. TronNRG 서비스 수정**

#### **주요 메서드 변경:**
```typescript
// Before: 직접 외부 API 호출
async getCurrentPrice(): Promise<TronNRGPrice> {
  return this.makeRequest<TronNRGPrice>('/market/price');  // TronNRG 직접 호출
}

// After: 백엔드 API 호출
async getCurrentPrice(): Promise<TronNRGPrice> {
  return this.makeRequest<TronNRGPrice>('/market/prices/realtime');  // 백엔드 호출
}
```

#### **WebSocket 연결 변경:**
```typescript
// Before: TronNRG WebSocket 직접 연결
connectPriceStream(): WebSocket {
  const ws = new WebSocket('wss://api.tronnrg.com/v1/stream/price');
}

// After: 백엔드 WebSocket 연결
connectPriceStream(): WebSocket {
  const ws = new WebSocket('ws://localhost:8000/ws/external-energy/prices');
}
```

### **4. API 응답 형식 변경**

#### **백엔드 표준 응답 형식:**
```typescript
interface BackendResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

// 기존 직접 응답 처리
const data = await response.json();  // 직접 데이터

// 변경 후 백엔드 응답 처리
const response = await response.json() as BackendResponse<T>;
const data = response.data;  // response.data에서 추출
```

---

## 📁 **파일별 상세 수정 가이드**

### **1. src/services/tron-nrg-service.ts**

#### **수정 포인트:**
```typescript
class TronNRGService {
  private baseURL: string;
  
  constructor() {
    // 변경: 백엔드 API URL 사용
    this.baseURL = process.env.NEXT_PUBLIC_API_URL + '/api/v1/external-energy';
    // API 키는 제거 (백엔드에서 관리)
  }

  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,  // 사용자 인증 토큰
      // 'X-API-Key': 제거 (백엔드에서 관리)
    };

    const response = await fetch(url, {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
    });

    const result = await response.json() as BackendResponse<T>;
    
    if (!result.success) {
      throw new Error(result.error || 'API call failed');
    }
    
    return result.data;  // 백엔드 표준 응답에서 data 추출
  }

  // 엔드포인트 변경
  async getCurrentPrice(): Promise<TronNRGPrice> {
    return this.makeRequest<TronNRGPrice>('/market/prices/realtime');
  }

  async getMarketData(): Promise<TronNRGMarketData> {
    return this.makeRequest<TronNRGMarketData>('/market/summary');
  }

  async getProviders(): Promise<TronNRGProvider[]> {
    return this.makeRequest<TronNRGProvider[]>('/providers');
  }

  async createOrder(orderRequest: TronNRGOrderRequest): Promise<TronNRGOrderResponse> {
    return this.makeRequest<TronNRGOrderResponse>('/orders', {
      method: 'POST',
      body: JSON.stringify(orderRequest),
    });
  }

  // WebSocket 연결 변경
  connectPriceStream(onUpdate: (price: TronNRGPrice) => void): WebSocket | null {
    try {
      const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') + '/ws/external-energy/prices';
      const ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'price_update') {
          onUpdate(data.data);
        }
      };
      
      return ws;
    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
      return null;
    }
  }
}
```

### **2. src/lib/api.ts (새로 생성)**

```typescript
// 백엔드 API 클라이언트 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface BackendResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getAuthToken()}`,
  };

  const response = await fetch(url, {
    ...options,
    headers: { ...defaultHeaders, ...options.headers },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const result = await response.json() as BackendResponse<T>;
  
  if (!result.success) {
    throw new Error(result.error || 'API call failed');
  }
  
  return result.data;
}

function getAuthToken(): string {
  // 사용자 인증 토큰 가져오기 로직
  return localStorage.getItem('auth_token') || '';
}
```

### **3. 페이지 컴포넌트 수정**

#### **수정 사항이 적은 이유:**
- 기존 인터페이스 (`TronNRGProvider`, `TronNRGPrice` 등)는 그대로 유지
- 서비스 레이어에서만 API 호출 방식 변경
- 컴포넌트 로직은 거의 변경 없음

#### **필요한 수정:**
```typescript
// src/app/energy/external-market/page.tsx
useEffect(() => {
  // 인증 체크 추가
  if (!isAuthenticated()) {
    router.push('/login');
    return;
  }
  
  // 기존 로직 그대로
  loadInitialData();
  connectPriceStream();
}, []);
```

---

## 🔐 **인증 처리 추가**

### **백엔드 API 호출 시 인증 필요:**
```typescript
// 모든 API 요청에 인증 토큰 포함
headers: {
  'Authorization': `Bearer ${userToken}`,
  'Content-Type': 'application/json'
}
```

### **인증 실패 처리:**
```typescript
// API 응답에서 401 처리
if (response.status === 401) {
  // 토큰 만료 처리
  logout();
  router.push('/login');
  return;
}
```

---

## ⚡ **성능 개선 사항**

### **1. 캐싱 활용**
```typescript
// 백엔드에서 캐싱된 데이터 사용으로 응답 속도 향상
// 프론트엔드에서 별도 캐싱 불필요
```

### **2. 에러 처리 개선**
```typescript
// 백엔드에서 표준화된 에러 응답
try {
  const data = await tronNRGService.getProviders();
} catch (error) {
  if (error.message.includes('rate limit')) {
    showToast('요청이 너무 많습니다. 잠시 후 다시 시도해주세요.');
  } else {
    showToast('데이터를 불러오는데 실패했습니다.');
  }
}
```

---

## 🧪 **테스트 계획**

### **1. 개발 환경 테스트**
```bash
# 백엔드 서버 실행 확인
curl http://localhost:8000/api/v1/external-energy/providers

# 프론트엔드 연동 테스트
npm run dev
```

### **2. API 연동 테스트**
- [ ] 공급자 목록 조회
- [ ] 실시간 가격 업데이트
- [ ] 주문 생성 및 추적
- [ ] WebSocket 연결
- [ ] 에러 처리

### **3. 인증 테스트**
- [ ] 로그인 후 API 호출
- [ ] 토큰 만료 처리
- [ ] 권한 없는 접근 처리

---

## 📅 **마이그레이션 일정**

### **Day 1: 준비 작업**
- [ ] 백엔드 API 완성 확인
- [ ] 환경변수 설정
- [ ] API 클라이언트 생성

### **Day 2: 서비스 레이어 수정**
- [ ] `tron-nrg-service.ts` 수정
- [ ] 인증 처리 추가
- [ ] 에러 처리 개선

### **Day 3: 테스트 및 검증**
- [ ] 기능 테스트
- [ ] 성능 테스트
- [ ] 에러 시나리오 테스트

### **Day 4: 배포 및 모니터링**
- [ ] 스테이징 배포
- [ ] 프로덕션 배포
- [ ] 모니터링 설정

---

## ⚠️ **주의사항**

### **1. 하위 호환성**
- 기존 Mock 데이터 기능 유지 (백엔드 장애 시 Fallback)
- 점진적 마이그레이션 (기능별로 단계적 적용)

### **2. 에러 처리**
- 백엔드 서버 다운 시 대체 방안
- 네트워크 오류 시 재시도 로직
- 사용자 친화적 에러 메시지

### **3. 성능 모니터링**
- API 응답 시간 측정
- 에러율 모니터링
- 사용자 경험 개선

---

**백엔드 API 완성 후 이 문서를 참고하여 프론트엔드 마이그레이션을 진행하세요.**

**예상 소요 시간**: 3-4일  
**난이도**: 중간  
**영향도**: 높음 (전체 외부 에너지 기능)
