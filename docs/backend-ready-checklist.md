# 백엔드 API 준비 시 프론트엔드 변경 체크리스트

**작성일**: 2025년 7월 21일  
**목적**: 백엔드 API 완성 후 즉시 수행할 프론트엔드 변경사항  

---

## 🚨 **즉시 변경 필요한 파일들**

### **1. 환경변수 설정 (.env.local)**

```bash
# 현재 설정 (TronNRG API 직접 호출)
# NEXT_PUBLIC_TRONNRG_API_URL=https://api.tronnrg.com/v1
# NEXT_PUBLIC_TRONNRG_API_KEY=your-api-key

# 변경 후 설정 (백엔드 API 호출)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_WS_URL=ws://localhost:8000/ws
```

### **2. TronNRG 서비스 파일 (src/services/tron-nrg-service.ts)**

#### **API 엔드포인트 변경:**
```typescript
// 현재 (라인 66-67)
private baseURL: string = 'https://api.tronnrg.com/v1';

// 변경 후
private baseURL: string = process.env.NEXT_PUBLIC_API_URL + '/api/v1/energy/external';
```

#### **인증 헤더 변경:**
```typescript
// 현재 (라인 85-90)
const defaultHeaders = {
  'Content-Type': 'application/json',
  'X-API-Key': process.env.NEXT_PUBLIC_TRONNRG_API_KEY || '',
};

// 변경 후
const defaultHeaders = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
};
```

#### **엔드포인트 경로 변경:**
```typescript
// 현재 엔드포인트들
'/market/price' → '/tronnrg/market/price'
'/market/data' → '/tronnrg/market/data'  
'/providers' → '/tronnrg/providers'
'/order' → '/tronnrg/order'
```

### **3. WebSocket 연결 변경**

#### **현재 (라인 310-320):**
```typescript
connectWebSocket(onMessage: (data: any) => void): void {
  if (typeof window === 'undefined') return;
  
  const wsUrl = this.isProduction 
    ? 'wss://api.tronnrg.com/ws'
    : 'ws://localhost:3002';
```

#### **변경 후:**
```typescript
connectWebSocket(onMessage: (data: any) => void): void {
  if (typeof window === 'undefined') return;
  
  const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL || 'ws://localhost:8000/ws';
```

---

## 🔧 **단계별 변경 절차**

### **Phase 1: 환경변수 업데이트**
1. `.env.local` 파일에서 백엔드 API URL 설정
2. TronNRG 직접 API 관련 환경변수 제거

### **Phase 2: 서비스 파일 수정**
1. `tron-nrg-service.ts`에서 baseURL 변경
2. 인증 방식을 백엔드 토큰 방식으로 변경
3. 엔드포인트 경로를 백엔드 API 스펙에 맞게 수정

### **Phase 3: WebSocket 연결 변경**
1. WebSocket URL을 백엔드 서버로 변경
2. 연결 로직에서 인증 토큰 포함

### **Phase 4: 테스트 및 검증**
1. 개발 환경에서 백엔드 연동 테스트
2. 에러 핸들링 확인
3. 실시간 데이터 수신 확인

---

## 📝 **변경 후 확인사항**

- [ ] 에너지 시장 데이터 정상 로드
- [ ] 가격 정보 실시간 업데이트
- [ ] 공급업체 목록 정상 표시
- [ ] 주문 기능 정상 동작
- [ ] WebSocket 실시간 연결 정상
- [ ] 인증 토큰 정상 전달
- [ ] 에러 메시지 적절히 표시

---

## ⚠️ **주의사항**

1. **백엔드 API 스펙 확인**: 정확한 엔드포인트와 데이터 구조 확인 필요
2. **인증 방식 통일**: 백엔드와 동일한 JWT 토큰 방식 사용
3. **WebSocket 인증**: WebSocket 연결 시에도 인증 토큰 전달 필요
4. **에러 핸들링**: 백엔드 API 에러 코드에 맞는 처리 로직 추가

---

## 🔗 **관련 문서**

- [백엔드 API 요구사항](./backend-energy-api-requirements.md)
- [프론트엔드 마이그레이션 계획](./frontend-migration-plan.md)
- [개발 체크리스트](./DEVELOPMENT_CHECKLIST.md)
