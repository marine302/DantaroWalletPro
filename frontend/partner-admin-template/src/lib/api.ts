/**
 * API 클라이언트 - 백엔드 연동
 * 참고 문서: Doc-24 (TronLink), Doc-25 (파트너 관리), Doc-26 (에너지), Doc-27 (수수료)
 *            Doc-28 (출금), Doc-29 (온보딩), Doc-30 (감사), Doc-31 (에너지 렌탈)
 */

// 기본 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || '/api/v1';
const IS_DEVELOPMENT = process.env.NEXT_PUBLIC_ENV === 'development';

// 로그 레벨 설정
const LOG_LEVEL = process.env.NEXT_PUBLIC_LOG_LEVEL || 'info';

// API 오류 타입
class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// HTTP 클라이언트 유틸리티
class HttpClient {
  private baseURL: string;
  private headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setAuthToken(token: string) {
    this.headers['Authorization'] = `Bearer ${token}`;
  }

  removeAuthToken() {
    delete this.headers['Authorization'];
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: Record<string, unknown>
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    // 개발 환경에서만 상세 로깅
    if (IS_DEVELOPMENT && LOG_LEVEL === 'debug') {
      console.log(`Making ${method} request to:`, url);
      if (data) console.log('Request data:', data);
    }
    
    try {
      const response = await fetch(url, {
        method,
        headers: this.headers,
        body: data ? JSON.stringify(data) : undefined,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message || `HTTP ${response.status}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError('Network error', 0, error);
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>('GET', endpoint);
  }

  async post<T>(endpoint: string, data?: Record<string, unknown>): Promise<T> {
    return this.request<T>('POST', endpoint, data);
  }

  async put<T>(endpoint: string, data?: Record<string, unknown>): Promise<T> {
    return this.request<T>('PUT', endpoint, data);
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>('DELETE', endpoint);
  }
}

// HTTP 클라이언트 인스턴스
const httpClient = new HttpClient(`${API_BASE_URL}${API_VERSION}`);

// =============================================================================
// 인증 API (Auth)
// =============================================================================
export const authApi = {
  async login(email: string, password: string) {
    return httpClient.post('/auth/login', { email, password });
  },

  async logout() {
    return httpClient.post('/auth/logout');
  },

  async refreshToken() {
    return httpClient.post('/auth/refresh');
  },

  async me() {
    return httpClient.get('/auth/me');
  }
};

// =============================================================================
// TronLink 연동 API (Doc-24)
// =============================================================================
export const tronlinkApi = {
  // 지갑 연결
  async connect(walletAddress: string, signature: string) {
    return httpClient.post('/tronlink/connect', {
      wallet_address: walletAddress,
      signature
    });
  },

  // 지갑 연결 해제
  async disconnect(walletAddress: string) {
    return httpClient.post('/tronlink/disconnect', {
      wallet_address: walletAddress
    });
  },

  // 연결된 지갑 목록
  async getWallets() {
    return httpClient.get('/tronlink/wallets');
  },

  // 지갑 잔액 조회
  async getBalance(walletAddress: string) {
    return httpClient.get(`/tronlink/balance/${walletAddress}`);
  },

  // 트랜잭션 생성
  async createTransaction(data: {
    to_address: string;
    amount: number;
    token_type?: string;
  }) {
    return httpClient.post('/tronlink/transaction/create', data);
  },

  // 트랜잭션 서명 완료
  async submitTransaction(transactionId: string, signedTx: string) {
    return httpClient.post('/tronlink/transaction/submit', {
      transaction_id: transactionId,
      signed_transaction: signedTx
    });
  },

  // 연결 상태 확인
  async getStatus() {
    return httpClient.get('/tronlink/status');
  }
};

// =============================================================================
// 파트너 관리 API (Doc-25)
// =============================================================================
export const partnerApi = {
  // 파트너 정보 조회
  async getProfile() {
    return httpClient.get('/partners/profile');
  },

  // 파트너 설정 업데이트
  async updateSettings(settings: Record<string, unknown>) {
    return httpClient.put('/partners/settings', settings);
  },

  // 파트너 통계
  async getStats() {
    return httpClient.get('/partners/stats');
  },

  // 사용자 목록
  async getUsers(page = 1, limit = 20) {
    return httpClient.get(`/partners/users?page=${page}&limit=${limit}`);
  },

  // 사용자 통계
  async getUserStats() {
    return httpClient.get('/partners/user-stats');
  },

  // 사용자 생성
  async createUser(userData: {
    email: string;
    name: string;
    role?: string;
  }) {
    return httpClient.post('/partners/users', userData);
  }
};

// =============================================================================
// 에너지 풀 관리 API (Doc-25, Doc-26) - 실제 백엔드 엔드포인트에 맞게 수정
// =============================================================================
export const energyApi = {
  // 파트너 에너지 실시간 모니터링 (실제 엔드포인트: /api/v1/energy/monitor/{partner_id})
  async getMonitoringData(partnerId: number) {
    return httpClient.get(`/energy/monitor/${partnerId}`);
  },

  // 에너지 분석 (실제 엔드포인트: /api/v1/energy/analytics/{partner_id})
  async getAnalytics(partnerId: number) {
    return httpClient.get(`/energy/analytics/${partnerId}`);
  },

  // 에너지 대시보드 (실제 엔드포인트: /api/v1/energy/dashboard/{partner_id})
  async getDashboard(partnerId: number) {
    return httpClient.get(`/energy/dashboard/${partnerId}`);
  },

  // 에너지 패턴 분석 (실제 엔드포인트: /api/v1/energy/patterns/{partner_id})
  async getPatterns(partnerId: number) {
    return httpClient.get(`/energy/patterns/${partnerId}`);
  },

  // 에너지 알림 목록 (실제 엔드포인트: /api/v1/energy/alerts/{partner_id})
  async getAlerts(partnerId: number) {
    return httpClient.get(`/energy/alerts/${partnerId}`);
  },

  // 글로벌 에너지 분석 (실제 엔드포인트: /api/v1/energy/global/analytics)
  async getGlobalAnalytics() {
    return httpClient.get('/energy/global/analytics');
  },

  // 에너지 풀 상태 조회 (실제 엔드포인트: /api/v1/energy/pool/{partner_id})
  async getPoolStatus(partnerId: number) {
    return httpClient.get(`/energy/pool/${partnerId}`);
  },

  // 에너지 거래 내역 조회 (실제 엔드포인트: /api/v1/energy/transactions/{partner_id})
  async getTransactions(partnerId: number, params: { page?: number; limit?: number } = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    
    const query = queryParams.toString();
    return httpClient.get(`/energy/transactions/${partnerId}${query ? '?' + query : ''}`);
  },

  // TRX 스테이킹으로 에너지 생성 (실제 엔드포인트: /api/v1/energy/stake)
  async stakeForEnergy(partnerId: number, amount: number) {
    return httpClient.post('/energy/stake', { partner_id: partnerId, amount });
  },

  // 에너지 언스테이킹 (실제 엔드포인트: /api/v1/energy/unstake) 
  async unstake(partnerId: number, amount: number) {
    return httpClient.post('/energy/unstake', { partner_id: partnerId, amount });
  },

  // 에너지 할당 (실제 엔드포인트: /api/v1/energy/allocate)
  async allocateEnergy(partnerId: number, targetAddress: string, amount: number) {
    return httpClient.post('/energy/allocate', { 
      partner_id: partnerId, 
      target_address: targetAddress, 
      amount 
    });
  },

  // 에너지 풀 최적화 (실제 엔드포인트: /api/v1/energy/optimize)
  async optimizePool(partnerId: number) {
    return httpClient.post(`/energy/optimize/${partnerId}`);
  }
};

// =============================================================================
// 수수료 최적화 API (Doc-27)
// =============================================================================
export const feeApi = {
  // 수수료 추천
  async getRecommendation(transactionType: string, amount?: number) {
    return httpClient.get(`/fees/recommendation?type=${transactionType}&amount=${amount || ''}`);
  },

  // 수수료 통계
  async getStats(period = '7d') {
    return httpClient.get(`/fees/stats?period=${period}`);
  },

  // 동적 수수료 정책
  async getFeePolicy() {
    return httpClient.get('/fees/policy');
  }
};

// =============================================================================
// 출금 관리 고도화 API (Doc-28)
// =============================================================================
export const withdrawalApi = {
  // 출금 정책 조회
  async getPolicy() {
    return httpClient.get('/withdrawal/policy');
  },

  // 출금 정책 업데이트
  async updatePolicy(policy: Record<string, unknown>) {
    return httpClient.put('/withdrawal/policy', policy);
  },

  // 출금 요청 목록
  async getRequests(page = 1, limit = 20, status?: string) {
    const params = new URLSearchParams({ 
      page: page.toString(), 
      limit: limit.toString(),
      ...(status && { status })
    });
    return httpClient.get(`/withdrawal/requests?${params}`);
  },

  // 출금 요청 생성
  async createRequest(data: {
    amount: number;
    to_address: string;
    description?: string;
  }) {
    return httpClient.post('/withdrawal/requests', data);
  },

  // 배치 출금 관리
  async getBatches() {
    return httpClient.get('/withdrawal/batches');
  },

  // 자동 승인 규칙
  async getApprovalRules() {
    return httpClient.get('/withdrawal/approval-rules');
  }
};

// =============================================================================
// 온보딩 자동화 API (Doc-29)
// =============================================================================
export const onboardingApi = {
  // 온보딩 진행률
  async getProgress() {
    return httpClient.get('/onboarding/progress');
  },

  // 온보딩 단계별 상태
  async getSteps() {
    return httpClient.get('/onboarding/steps');
  },

  // 체크리스트
  async getChecklist() {
    return httpClient.get('/onboarding/checklist');
  },

  // 단계 완료 처리
  async completeStep(stepId: string, data?: Record<string, unknown>) {
    return httpClient.post(`/onboarding/steps/${stepId}/complete`, data);
  }
};

// =============================================================================
// 감사 및 컴플라이언스 API (Doc-30)
// =============================================================================
export const auditApi = {
  // 감사 로그 조회
  async getLogs(page = 1, limit = 50, filters?: Record<string, unknown>) {
    const params = new URLSearchParams({ 
      page: page.toString(), 
      limit: limit.toString(),
      ...filters
    });
    return httpClient.get(`/audit/logs?${params}`);
  },

  // 의심 거래 목록
  async getSuspiciousTransactions() {
    return httpClient.get('/audit/suspicious-transactions');
  },

  // AML/KYC 상태
  async getComplianceStatus() {
    return httpClient.get('/audit/compliance-status');
  },

  // 규제 보고서
  async generateReport(type: string, period: string) {
    return httpClient.post('/audit/reports', { type, period });
  }
};

// =============================================================================
// 에너지 렌탈 서비스 API (Doc-31) - 실제 백엔드 엔드포인트에 맞게 수정
// =============================================================================
export const energyRentalApi = {
  // 활성 렌탈 플랜 조회 (실제 엔드포인트: /api/v1/energy-rental/rental-plans)
  async getPlans() {
    return httpClient.get('/energy-rental/rental-plans');
  },

  // 파트너 사용 통계 (실제 엔드포인트: /api/v1/energy-rental/partner/{partner_id}/usage-statistics)
  async getUsageStats(partnerId: number, period = '30d') {
    return httpClient.get(`/energy-rental/partner/${partnerId}/usage-statistics?period=${period}`);
  },

  // 파트너 청구 이력 (실제 엔드포인트: /api/v1/energy-rental/partner/{partner_id}/billing-history)
  async getBillingHistory(partnerId: number) {
    return httpClient.get(`/energy-rental/partner/${partnerId}/billing-history`);
  },

  // 파트너 에너지 할당 정보 (실제 엔드포인트: /api/v1/energy-rental/partner/{partner_id}/energy-allocation)
  async getCurrentPlan(partnerId: number) {
    return httpClient.get(`/energy-rental/partner/${partnerId}/energy-allocation`);
  },

  // 에너지 풀 상태 (실제 엔드포인트: /api/v1/energy-rental/energy-pools/status)
  async getPoolStatus() {
    return httpClient.get('/energy-rental/energy-pools/status');
  },

  // 시스템 상태 (실제 엔드포인트: /api/v1/energy-rental/system/status)
  async getSystemStatus() {
    return httpClient.get('/energy-rental/system/status');
  },

  // 비용 분석 (청구 이력에서 계산)
  async getCostAnalysis(partnerId: number) {
    return this.getBillingHistory(partnerId);
  }
};

// =============================================================================
// 분석 및 리포팅 API (Doc-33)
// =============================================================================
export const analyticsApi = {
  // 대시보드 데이터
  async getDashboardData() {
    return httpClient.get('/analytics/dashboard');
  },

  // 거래 분석
  async getTransactionAnalytics(period = '7d') {
    return httpClient.get(`/analytics/transactions?period=${period}`);
  },

  // 수익 분석
  async getRevenueAnalytics(period = '30d') {
    return httpClient.get(`/analytics/revenue?period=${period}`);
  },

  // 사용자 활동 분석
  async getUserActivityAnalytics() {
    return httpClient.get('/analytics/user-activity');
  },

  // 비용 분석
  async getCostAnalytics() {
    return httpClient.get('/analytics/costs');
  }
};

// =============================================================================
// WebSocket 연결 관리
// =============================================================================
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private listeners: Map<string, ((data: unknown) => void)[]> = new Map();

  connect() {
    try {
      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        } catch (error) {
          console.error('WebSocket message parsing error:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
    }
  }

  on(eventType: string, callback: (data: unknown) => void) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
  }

  off(eventType: string, callback: (data: unknown) => void) {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(eventType: string, data: unknown) {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// WebSocket 인스턴스
export const wsManager = new WebSocketManager();

// =============================================================================
// 사용자 관리 API (Users) 
// =============================================================================
export const usersApi = {
  // 사용자 목록 조회
  async getUsers(params: { 
    page?: number; 
    limit?: number; 
    search?: string; 
    status?: string; 
  } = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.status) queryParams.append('status', params.status);
    
    const query = queryParams.toString();
    return httpClient.get(`/users/${query ? '?' + query : ''}`);
  },

  // 사용자 상세 조회
  async getUser(userId: string) {
    return httpClient.get(`/users/${userId}`);
  },

  // 사용자 통계 조회
  async getUserStats() {
    return httpClient.get('/users/stats');
  },

  // 사용자 KYC 상태 업데이트
  async updateKYCStatus(userId: string, status: string) {
    return httpClient.put(`/users/${userId}/kyc`, { status });
  },

  // 사용자 상태 업데이트 (활성/비활성/정지)
  async updateUserStatus(userId: string, status: string) {
    return httpClient.put(`/users/${userId}/status`, { status });
  },

  // 사용자 계정 정지
  async suspendUser(userId: string, reason: string) {
    return httpClient.post(`/users/${userId}/suspend`, { reason });
  },

  // 사용자 계정 정지 해제
  async unsuspendUser(userId: string) {
    return httpClient.post(`/users/${userId}/unsuspend`);
  },

  // 사용자 잔액 조회
  async getUserBalance(userId: string) {
    return httpClient.get(`/users/${userId}/balance`);
  },

  // 사용자 거래 내역 조회
  async getUserTransactions(userId: string, params: { 
    page?: number; 
    limit?: number; 
    type?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.type) queryParams.append('type', params.type);
    
    const query = queryParams.toString();
    return httpClient.get(`/users/${userId}/transactions${query ? '?' + query : ''}`);
  },

  // 사용자 로그인 히스토리 조회
  async getUserLoginHistory(userId: string, params: { 
    page?: number; 
    limit?: number; 
  } = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    
    const query = queryParams.toString();
    return httpClient.get(`/users/${userId}/login-history${query ? '?' + query : ''}`);
  }
};

// =============================================================================
// 유틸리티 함수
// =============================================================================
export const apiUtils = {
  // 인증 토큰 설정
  setAuthToken(token: string) {
    httpClient.setAuthToken(token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  },

  // 인증 토큰 제거
  removeAuthToken() {
    httpClient.removeAuthToken();
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  },

  // 저장된 토큰 복원
  restoreAuthToken() {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        httpClient.setAuthToken(token);
      }
      return token;
    }
    return null;
  }
};

// 초기화 (브라우저 환경에서만)
if (typeof window !== 'undefined') {
  apiUtils.restoreAuthToken();
}

const api = {
  auth: authApi,
  users: usersApi,
  tronlink: tronlinkApi,
  partner: partnerApi,
  energy: energyApi,
  fee: feeApi,
  withdrawal: withdrawalApi,
  onboarding: onboardingApi,
  audit: auditApi,
  energyRental: energyRentalApi,
  analytics: analyticsApi,
  ws: wsManager,
  utils: apiUtils
};

export default api;
