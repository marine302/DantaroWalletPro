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

  constructor() {
    // 개발 모드에서는 Mock 서버 사용
    const baseURL = process.env.NODE_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001")
      : (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1");
    
    console.log('API Base URL:', baseURL);
    console.log('Environment:', process.env.NODE_ENV);
    
    this.client = axios.create({
      baseURL,
      timeout: 10000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
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
    this.client.interceptors.response.use(
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
    const response: AxiosResponse<AuthResponse> = await this.client.post('/auth/login', credentials);
    this.setAuthToken(response.data.access_token);
    return response.data;
  }

  async superAdminLogin(credentials: LoginRequest): Promise<AuthResponse> {
    console.log('Attempting login with:', { email: credentials.email, baseURL: this.client.defaults.baseURL });
    const response: AxiosResponse<AuthResponse> = await this.client.post('/auth/login', credentials);
    console.log('Login response:', response.data);
    this.setAuthToken(response.data.access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    this.removeAuthToken();
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response: AxiosResponse<DashboardStats> = await this.client.get('/admin/dashboard/stats');
    return response.data;
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response: AxiosResponse<SystemHealth> = await this.client.get('/admin/system/health');
    return response.data;
  }

  // Partners
  async getPartners(page = 1, size = 20): Promise<PaginatedResponse<Partner>> {
    const response: AxiosResponse<PaginatedResponse<Partner>> = await this.client.get('/partners/', {
      params: { page, size },
    });
    return response.data;
  }

  async getPartner(id: number): Promise<Partner> {
    const response: AxiosResponse<Partner> = await this.client.get(`/partners/${id}`);
    return response.data;
  }

  async createPartner(data: CreatePartnerRequest): Promise<Partner> {
    const response: AxiosResponse<Partner> = await this.client.post('/admin/partners', data);
    return response.data;
  }

  async updatePartner(id: number, data: UpdatePartnerRequest): Promise<Partner> {
    const response: AxiosResponse<Partner> = await this.client.put(`/admin/partners/${id}`, data);
    return response.data;
  }

  async deletePartner(id: number): Promise<void> {
    await this.client.delete(`/admin/partners/${id}`);
  }

  async getPartnerConfig(partnerId: number): Promise<PartnerConfig> {
    const response: AxiosResponse<PartnerConfig> = await this.client.get(`/admin/partners/${partnerId}/config`);
    return response.data;
  }

  async getPartnerStatistics(partnerId: number, days = 30): Promise<PartnerDailyStatistics[]> {
    const response: AxiosResponse<PartnerDailyStatistics[]> = await this.client.get(
      `/admin/partners/${partnerId}/statistics`,
      { params: { days } }
    );
    return response.data;
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
