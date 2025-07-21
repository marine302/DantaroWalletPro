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
    const baseURL = process.env.NODE_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001")
      : (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1");
    
    // 백엔드 API 사용 여부 결정
    this.useBackendAPI = process.env.NEXT_PUBLIC_USE_BACKEND_API === 'true';
    
    console.log('🔧 API Client Configuration:', {
      baseURL,
      useBackendAPI: this.useBackendAPI,
      environment: process.env.NODE_ENV,
      mockURL: "http://localhost:3001",
      backendURL: process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1"
    });
    
    this.client = axios.create({
      baseURL,
      timeout: 10000,
    });

    // Request interceptor to add auth token (모든 클라이언트에 적용)
    [this.client, this.mockClient, this.backendClient].forEach(client => {
      client.interceptors.request.use(
        (config) => {
          const token = this.getAuthToken();
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
  private async makeResilientRequest<T>(
    endpoint: string, 
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    data?: any,
    options?: any
  ): Promise<T> {
    const requestConfig = {
      method: method.toLowerCase(),
      ...options,
      ...(data && ['post', 'put'].includes(method.toLowerCase()) && { data })
    };

    // 1. 백엔드 API 사용이 활성화된 경우 먼저 시도
    if (this.useBackendAPI) {
      try {
        console.log(`🚀 Trying Backend API: ${method} ${endpoint}`);
        const response: AxiosResponse<T> = await this.backendClient.request({
          url: endpoint,
          ...requestConfig
        });
        console.log(`✅ Backend API Success: ${method} ${endpoint}`);
        return response.data;
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
    const response = await this.makeResilientRequest<AuthResponse>('/auth/login', 'POST', credentials);
    this.setAuthToken(response.access_token);
    return response;
  }

  async superAdminLogin(credentials: LoginRequest): Promise<AuthResponse> {
    console.log('Attempting login with:', { email: credentials.email });
    const response = await this.makeResilientRequest<AuthResponse>('/auth/login', 'POST', credentials);
    console.log('Login response:', response);
    this.setAuthToken(response.access_token);
    return response;
  }

  async logout(): Promise<void> {
    this.removeAuthToken();
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return this.makeResilientRequest<DashboardStats>('/admin/dashboard/stats');
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return this.makeResilientRequest<SystemHealth>('/admin/system/health');
  }

  // Partners
  async getPartners(page = 1, size = 20): Promise<PaginatedResponse<Partner>> {
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

  // Energy Management
  async getEnergyPool(): Promise<EnergyPool> {
    const response: AxiosResponse<EnergyPool> = await this.client.get('/admin/energy/pool');
    return response.data;
  }

  async rechargeEnergy(amount: number): Promise<EnergyTransaction> {
    const response: AxiosResponse<EnergyTransaction> = await this.client.post('/admin/energy/recharge', {
      amount,
    });
    return response.data;
  }

  async allocateEnergy(partnerId: number, amount: number): Promise<EnergyTransaction> {
    const response: AxiosResponse<EnergyTransaction> = await this.client.post('/admin/energy/allocate', {
      partner_id: partnerId,
      amount,
    });
    return response.data;
  }

  async getEnergyTransactions(page = 1, size = 20): Promise<PaginatedResponse<EnergyTransaction>> {
    const response: AxiosResponse<PaginatedResponse<EnergyTransaction>> = await this.client.get('/admin/energy/transactions', {
      params: { page, size },
    });
    return response.data;
  }

  // Fee Management
  async getFeeConfigs(): Promise<FeeConfig[]> {
    const response: AxiosResponse<FeeConfig[]> = await this.client.get('/admin/fees/configs');
    return response.data;
  }

  async createFeeConfig(data: CreateFeeConfigRequest): Promise<FeeConfig> {
    const response: AxiosResponse<FeeConfig> = await this.client.post('/admin/fees/configs', data);
    return response.data;
  }

  async updateFeeConfig(id: number, data: Partial<CreateFeeConfigRequest>): Promise<FeeConfig> {
    const response: AxiosResponse<FeeConfig> = await this.client.put(`/admin/fees/configs/${id}`, data);
    return response.data;
  }

  async deleteFeeConfig(id: number): Promise<void> {
    await this.client.delete(`/admin/fees/configs/${id}`);
  }

  async getFeeRevenue(page = 1, size = 20, partnerId?: number): Promise<PaginatedResponse<FeeRevenue>> {
    const response: AxiosResponse<PaginatedResponse<FeeRevenue>> = await this.client.get('/admin/fees/revenue', {
      params: { page, size, partner_id: partnerId },
    });
    return response.data;
  }

  // System Admins
  async getSystemAdmins(): Promise<SystemAdmin[]> {
    const response: AxiosResponse<SystemAdmin[]> = await this.client.get('/admin/system/admins');
    return response.data;
  }

  async createSystemAdmin(data: {
    username: string;
    email: string;
    full_name: string;
    password: string;
    role: 'super_admin' | 'admin' | 'operator';
  }): Promise<SystemAdmin> {
    const response: AxiosResponse<SystemAdmin> = await this.client.post('/admin/system/admins', data);
    return response.data;
  }

  async updateSystemAdmin(id: number, data: Partial<{
    email: string;
    full_name: string;
    role: 'super_admin' | 'admin' | 'operator';
    is_active: boolean;
  }>): Promise<SystemAdmin> {
    const response: AxiosResponse<SystemAdmin> = await this.client.put(`/admin/system/admins/${id}`, data);
    return response.data;
  }

  async deleteSystemAdmin(id: number): Promise<void> {
    await this.client.delete(`/admin/system/admins/${id}`);
  }
}

export const apiClient = new ApiClient();
