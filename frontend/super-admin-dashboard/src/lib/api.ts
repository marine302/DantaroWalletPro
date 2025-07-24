import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  PaginatedResponse,
  Partner,
  PartnerConfig,
  PartnerDailyStatistics,
  EnergyPool,
  EnergyTransaction,
  FeeConfig,
  FeeRevenue,
  SystemAdmin,
  DashboardStats,
  SystemHealth,
  LoginRequest,
  AuthResponse,
  CreatePartnerRequest,
  UpdatePartnerRequest,
  CreateFeeConfigRequest,
} from '@/types';

class ApiClient {
  private client: AxiosInstance;
  private mockClient: AxiosInstance;
  private backendClient: AxiosInstance;
  private useBackendAPI: boolean = false;

  constructor() {
    // Mock 서버 클라이언트 (항상 준비)
    this.mockClient = axios.create({
      baseURL: "http://localhost:3001",
      timeout: 5000,
    });

    // 백엔드 API 클라이언트 (프로덕션 또는 백엔드 테스트용)
    this.backendClient = axios.create({
      baseURL: process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1",
      timeout: 10000,
    });

    // 기본 클라이언트 설정 (환경에 따라 결정)
    const _baseURL = process.env.NODE_ENV === 'development'
      ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001")
      : (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1");

    // 백엔드 API 사용 여부 결정
    this.useBackendAPI = process.env.NEXT_PUBLIC_USE_BACKEND_API === 'true';

    console.log('🔧 API Client Configuration:', {
      baseURL: _baseURL,
      useBackendAPI: this.useBackendAPI,
      environment: process.env.NODE_ENV,
      mockURL: "http://localhost:3001",
      backendURL: process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1"
    });

    this.client = axios.create({
      baseURL: _baseURL,
      timeout: 10000,
    });

    // Request interceptor to add auth token (모든 클라이언트에 적용)
    [this.client, this.mockClient, this.backendClient].forEach(client => {
      client.interceptors.request.use(
        (config) => {
          const _token = this.getAuthToken();
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
          return config;
        },
        (error) => Promise.reject(error)
      );

      // Response interceptor to handle errors
      client.interceptors.response.use(
        (response) => response,
        (error) => {
          // 개발 환경에서는 401 에러 무시
          if (error.response?.status === 401 && process.env.NODE_ENV !== 'development') {
            this.removeAuthToken();
            // Redirect to login page
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
          }
          return Promise.reject(error);
        }
      );
    });
  }

  /**
   * 백엔드 API 실패 시 자동으로 Mock API로 fallback하는 요청 메서드
   */
  public async makeResilientRequest<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    data?: any,
    options?: any
  ): Promise<T> {
    const _requestConfig = {
      method: method.toLowerCase(),
      ...options,
      ...(data && ['post', 'put'].includes(method.toLowerCase()) && { data })
    };

    // 1. 백엔드 API 사용이 활성화된 경우 먼저 시도
    if (this.useBackendAPI) {
      try {
        console.log(`🚀 Trying Backend API: ${method} ${endpoint}`);
        const response: AxiosResponse<any> = await this.backendClient.request({
          url: endpoint,
          ...requestConfig
        });
        console.log(`✅ Backend API Success: ${method} ${endpoint}`);

        // 백엔드 응답이 { success: true, data: {...} } 형태인 경우 data 추출
        if (response.data && typeof response.data === 'object' && response.data.success && response.data.data) {
          return response.data.data as T;
        }
        // PaginatedResponse의 경우 페이지네이션 정보도 처리
        if (response.data && typeof response.data === 'object' && response.data.success && response.data.data && response.data.data.items) {
          const _data = response.data.data;
          return {
            items: data.items,
            total: data.total,
            page: data.page,
            size: data.size,
            pages: Math.ceil(data.total / data.size)
          } as T;
        }
        return response.data as T;
      } catch (error) {
        console.warn(`❌ Backend API Failed: ${method} ${endpoint}`, error);
        console.log(`🔄 Falling back to Mock API...`);
      }
    }

    // 2. Mock API로 fallback
    try {
      console.log(`🎭 Using Mock API: ${method} ${endpoint}`);
      const response: AxiosResponse<T> = await this.mockClient.request({
        url: endpoint,
        ...requestConfig
      });
      console.log(`✅ Mock API Success: ${method} ${endpoint}`);
      return response.data;
    } catch (mockError) {
      console.error(`❌ Mock API Also Failed: ${method} ${endpoint}`, mockError);

      // 3. 최종 fallback: 기본 클라이언트 사용
      try {
        console.log(`🔄 Using Default Client: ${method} ${endpoint}`);
        const response: AxiosResponse<T> = await this.client.request({
          url: endpoint,
          ...requestConfig
        });
        return response.data;
      } catch (finalError) {
        console.error(`💥 All API clients failed: ${method} ${endpoint}`, finalError);
        throw finalError;
      }
    }
  }

  /**
   * 백엔드 API 상태 확인 및 자동 전환
   */
  async checkBackendHealth(): Promise<boolean> {
    if (!this.useBackendAPI) return false;

    try {
      await this.backendClient.get('/health', { timeout: 3000 });
      console.log('✅ Backend API is healthy');
      return true;
    } catch (error) {
      console.warn('❌ Backend API health check failed:', error);
      return false;
    }
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('authToken');
    }
    return null;
  }

  private setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('authToken', token);
    }
  }

  private removeAuthToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const _response = await this.makeResilientRequest<AuthResponse>('/auth/login', 'POST', credentials);
    this.setAuthToken(response.access_token);
    return response;
  }

  async superAdminLogin(credentials: LoginRequest): Promise<AuthResponse> {
    console.log('Attempting super admin login with:', { email: credentials.email });
    // 슈퍼 어드민 로그인은 별도 엔드포인트 사용
    const _response = await this.makeResilientRequest<AuthResponse>('/auth/super-admin/login', 'POST', credentials);
    console.log('Super admin login response:', response);
    this.setAuthToken(response.access_token);
    return response;
  }

  async logout(): Promise<void> {
    this.removeAuthToken();
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    // 백엔드 API는 /admin/dashboard/overview 엔드포인트를 사용
    return this.makeResilientRequest<DashboardStats>('/admin/dashboard/overview');
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return this.makeResilientRequest<SystemHealth>('/admin/system/health');
  }

  // Partners
  async getPartners(page = 1, size = 20): Promise<PaginatedResponse<Partner>> {
    // 백엔드는 /partners/ 엔드포인트를 사용하고 인증이 필요함
    // 일시적으로 Mock API 사용하도록 임시 처리
    return this.makeResilientRequest<PaginatedResponse<Partner>>('/partners/', 'GET', undefined, {
      params: { page, size },
    });
  }

  async getPartner(id: number): Promise<Partner> {
    return this.makeResilientRequest<Partner>(`/partners/${id}`);
  }

  async createPartner(data: CreatePartnerRequest): Promise<Partner> {
    return this.makeResilientRequest<Partner>('/admin/partners', 'POST', data);
  }

  async updatePartner(id: number, data: UpdatePartnerRequest): Promise<Partner> {
    return this.makeResilientRequest<Partner>(`/admin/partners/${id}`, 'PUT', data);
  }

  async deletePartner(id: number): Promise<void> {
    return this.makeResilientRequest<void>(`/admin/partners/${id}`, 'DELETE');
  }

  async getPartnerConfig(partnerId: number): Promise<PartnerConfig> {
    return this.makeResilientRequest<PartnerConfig>(`/admin/partners/${partnerId}/config`);
  }

  async getPartnerStatistics(partnerId: number, days = 30): Promise<PartnerDailyStatistics[]> {
    return this.makeResilientRequest<PartnerDailyStatistics[]>(
      `/admin/partners/${partnerId}/statistics`,
      'GET',
      undefined,
      { params: { days } }
    );
  }

  // Energy Management - 백엔드 엔드포인트 사용
  async getEnergyPool(): Promise<EnergyPool> {
    return this.makeResilientRequest<EnergyPool>('/admin/energy/pool');
  }

  async getEnergyStatus(): Promise<any> {
    return this.makeResilientRequest<any>('/admin/energy/status');
  }

  async rechargeEnergy(amount: number): Promise<EnergyTransaction> {
    return this.makeResilientRequest<EnergyTransaction>('/admin/energy/recharge', 'POST', { amount });
  }

  async allocateEnergy(partnerId: number, amount: number): Promise<EnergyTransaction> {
    return this.makeResilientRequest<EnergyTransaction>('/admin/energy/allocate', 'POST', {
      partner_id: partnerId,
      amount,
    });
  }

  async getEnergyTransactions(page = 1, size = 20): Promise<PaginatedResponse<EnergyTransaction>> {
    return this.makeResilientRequest<PaginatedResponse<EnergyTransaction>>('/admin/energy/transactions', 'GET', undefined, {
      params: { page, size },
    });
  }

  // Fee Management - 백엔드 엔드포인트 사용
  async getFeeConfigs(): Promise<FeeConfig[]> {
    return this.makeResilientRequest<FeeConfig[]>('/admin/fees/configs');
  }

  async createFeeConfig(data: CreateFeeConfigRequest): Promise<FeeConfig> {
    return this.makeResilientRequest<FeeConfig>('/admin/fees/configs', 'POST', data);
  }

  async updateFeeConfig(id: number, data: Partial<CreateFeeConfigRequest>): Promise<FeeConfig> {
    return this.makeResilientRequest<FeeConfig>(`/admin/fees/configs/${id}`, 'PUT', data);
  }

  async deleteFeeConfig(id: number): Promise<void> {
    return this.makeResilientRequest<void>(`/admin/fees/configs/${id}`, 'DELETE');
  }

  async getFeeRevenue(page = 1, size = 20, partnerId?: number): Promise<PaginatedResponse<FeeRevenue>> {
    return this.makeResilientRequest<PaginatedResponse<FeeRevenue>>('/admin/fees/revenue', 'GET', undefined, {
      params: { page, size, partner_id: partnerId },
    });
  }

  // System Admins
  async getSystemAdmins(): Promise<SystemAdmin[]> {
    return this.makeResilientRequest<SystemAdmin[]>('/admin/system/admins');
  }

  async createSystemAdmin(data: {
    username: string;
    email: string;
    full_name: string;
    password: string;
    role: 'super_admin' | 'admin' | 'operator';
  }): Promise<SystemAdmin> {
    return this.makeResilientRequest<SystemAdmin>('/admin/system/admins', 'POST', data);
  }

  async updateSystemAdmin(id: number, data: Partial<{
    email: string;
    full_name: string;
    role: 'super_admin' | 'admin' | 'operator';
    is_active: boolean;
  }>): Promise<SystemAdmin> {
    return this.makeResilientRequest<SystemAdmin>(`/admin/system/admins/${id}`, 'PUT', data);
  }

  async deleteSystemAdmin(id: number): Promise<void> {
    return this.makeResilientRequest<void>(`/admin/system/admins/${id}`, 'DELETE');
  }

  // 편의 메서드들 (external-energy-service 호환성을 위해)
  async get<T>(endpoint: string, options?: any): Promise<T> {
    return this.makeResilientRequest<T>(endpoint, 'GET', undefined, options);
  }

  async post<T>(endpoint: string, data?: any, options?: any): Promise<T> {
    return this.makeResilientRequest<T>(endpoint, 'POST', data, options);
  }

  async put<T>(endpoint: string, data?: any, options?: any): Promise<T> {
    return this.makeResilientRequest<T>(endpoint, 'PUT', data, options);
  }

  async delete<T>(endpoint: string, options?: any): Promise<T> {
    return this.makeResilientRequest<T>(endpoint, 'DELETE', undefined, options);
  }
}

export const apiClient = new ApiClient();
