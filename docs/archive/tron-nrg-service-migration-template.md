/**
 * 백엔드 API 연동용 TronNRG 서비스 - 변경 템플릿
 * 백엔드 API 준비 완료 시 기존 파일을 이 내용으로 교체
 */

// ===== 변경 필요한 부분들 =====

// 1. Constructor 부분 (Line 73-81)
// 현재:
/*
constructor() {
  this.baseURL = process.env.NEXT_PUBLIC_TRONNRG_API_URL || 'https://api.tronnrg.com/v1';
  this.apiKey = process.env.NEXT_PUBLIC_TRONNRG_API_KEY || 'demo_key';
  this.isProduction = process.env.NODE_ENV === 'production';
  
  console.log('🔋 TronNRG Service initialized:', {
    baseURL: this.baseURL,
    isProduction: this.isProduction,
    hasApiKey: !!this.apiKey
  });
}
*/

// 변경 후:
constructor() {
  // 백엔드 API 엔드포인트로 변경
  this.baseURL = (process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000/api/v1') + '/energy/external/tronnrg';
  this.isProduction = process.env.NODE_ENV === 'production';
  
  console.log('🔋 TronNRG Service initialized (Backend API):', {
    baseURL: this.baseURL,
    isProduction: this.isProduction,
    useBackendAPI: true
  });
}

// 2. makeRequest 메서드의 headers 부분 (Line 85-90)
// 현재:
/*
const defaultHeaders = {
  'Content-Type': 'application/json',
  'X-API-Key': this.apiKey,
  'User-Agent': 'DantaroWallet-SuperAdmin/1.0'
};
*/

// 변경 후:
const defaultHeaders = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${this.getAuthToken()}`,
  'User-Agent': 'DantaroWallet-SuperAdmin/1.0'
};

// 3. 인증 토큰 가져오기 메서드 추가
private getAuthToken(): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('accessToken') || '';
}

// 4. WebSocket 연결 부분 (Line 310-320)
// 현재:
/*
connectWebSocket(onMessage: (data: any) => void): void {
  if (typeof window === 'undefined') return;
  
  const wsUrl = this.isProduction 
    ? 'wss://api.tronnrg.com/ws'
    : 'ws://localhost:3002';
*/

// 변경 후:
connectWebSocket(onMessage: (data: any) => void): void {
  if (typeof window === 'undefined') return;
  
  // 백엔드 WebSocket URL 사용
  const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL || 'ws://localhost:8000/ws';
  
  // 인증 토큰 포함한 WebSocket 연결
  const token = this.getAuthToken();
  const wsUrlWithAuth = token ? `${wsUrl}?token=${token}` : wsUrl;
  
  this.ws = new WebSocket(wsUrlWithAuth);

// 5. API 엔드포인트 경로 변경
// 현재 경로들:
// '/market/price' → 그대로 유지 (백엔드에서 /market/price로 받을 예정)
// '/market/data' → 그대로 유지
// '/providers' → 그대로 유지  
// '/order' → 그대로 유지

// 백엔드에서 다음과 같이 라우팅할 예정:
// GET /api/v1/energy/external/tronnrg/market/price
// GET /api/v1/energy/external/tronnrg/market/data
// GET /api/v1/energy/external/tronnrg/providers
// POST /api/v1/energy/external/tronnrg/order

// ===== 변경 체크리스트 =====
/*
□ 1. Constructor에서 baseURL을 백엔드 API로 변경
□ 2. apiKey 제거하고 JWT 토큰 사용으로 변경
□ 3. getAuthToken() 메서드 추가
□ 4. API 요청 헤더를 Bearer 토큰으로 변경
□ 5. WebSocket URL을 백엔드로 변경
□ 6. WebSocket 연결에 인증 토큰 포함
□ 7. 에러 핸들링에서 백엔드 API 에러 형식 반영
□ 8. Mock 데이터 로직에서 백엔드 응답 형식 반영
*/
