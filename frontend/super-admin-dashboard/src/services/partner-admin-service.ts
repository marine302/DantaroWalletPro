import { apiClient } from './api-client';

// 파트너 관리자 대시보드 관련 타입
export interface User {
  id: string;
  username: string;
  email: string;
  phone?: string;
  walletAddress: string;
  balance: number;
  status: 'active' | 'inactive' | 'suspended' | 'pending';
  createdAt: string;
  lastLogin?: string;
  kycStatus: 'none' | 'pending' | 'approved' | 'rejected';
  tier: 'basic' | 'premium' | 'vip';
}

export interface UserStats {
  totalUsers: number;
  activeUsers: number;
  newUsersToday: number;
  totalBalance: number;
  averageBalance: number;
  kycApproved: number;
  kycPending: number;
}

export interface WithdrawalRequest {
  id: string;
  userId: string;
  userName: string;
  amount: number;
  currency: string;
  destinationAddress: string;
  status: 'pending' | 'approved' | 'processing' | 'completed' | 'failed' | 'rejected';
  requestTime: string;
  processedTime?: string;
  transactionHash?: string;
  fee: number;
}

export interface WithdrawalStats {
  totalRequests: number;
  pendingRequests: number;
  completedToday: number;
  totalAmountToday: number;
  averageProcessingTime: number;
  successRate: number;
}

export interface EnergyPool {
  id: string;
  name: string;
  totalCapacity: number;
  availableCapacity: number;
  usedCapacity: number;
  pricePerUnit: number;
  status: 'active' | 'maintenance' | 'depleted';
  createdAt: string;
  lastUpdated: string;
  rentalCount: number;
  revenue: number;
}

export interface EnergyStats {
  totalPools: number;
  totalCapacity: number;
  totalUsed: number;
  totalAvailable: number;
  utilizationRate: number;
  totalRevenue: number;
  activeRentals: number;
  avgPricePerUnit: number;
}

export interface EnergyTransaction {
  id: string;
  userId: string;
  userName: string;
  poolId: string;
  poolName: string;
  amount: number;
  pricePerUnit: number;
  totalCost: number;
  type: 'rental' | 'purchase' | 'refund';
  status: 'pending' | 'completed' | 'failed';
  createdAt: string;
  expiresAt?: string;
}

export interface PartnerProfile {
  id: string;
  companyName: string;
  contactEmail: string;
  apiKeyId: string;
  status: 'active' | 'suspended' | 'maintenance';
  plan: 'basic' | 'pro' | 'enterprise';
  monthlyQuota: number;
  usedQuota: number;
  createdAt: string;
  lastActiveAt: string;
}

export interface AnalyticsData {
  period: string;
  users: number;
  transactions: number;
  revenue: number;
  energyUsage: number;
}

// API 서비스 클래스
export class PartnerAdminService {
  // 사용자 관리 API
  async getUsers(page: number = 1, limit: number = 20, filters?: {
    status?: string;
    kycStatus?: string;
    tier?: string;
    search?: string;
  }): Promise<{
    users: User[];
    total: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });
    return apiClient.get(`/partner/users?${params}`);
  }

  async getUserStats(): Promise<UserStats> {
    return apiClient.get('/partner/users/stats');
  }

  async updateUserStatus(userId: string, status: User['status']): Promise<void> {
    return apiClient.put(`/partner/users/${userId}/status`, { status });
  }

  async updateUserTier(userId: string, tier: User['tier']): Promise<void> {
    return apiClient.put(`/partner/users/${userId}/tier`, { tier });
  }

  async getUserDetails(userId: string): Promise<User> {
    return apiClient.get(`/partner/users/${userId}`);
  }

  // 출금 관리 API
  async getWithdrawalRequests(page: number = 1, limit: number = 20, filters?: {
    status?: string;
    currency?: string;
    dateFrom?: string;
    dateTo?: string;
  }): Promise<{
    requests: WithdrawalRequest[];
    total: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });
    return apiClient.get(`/partner/withdrawals?${params}`);
  }

  async getWithdrawalStats(): Promise<WithdrawalStats> {
    return apiClient.get('/partner/withdrawals/stats');
  }

  async approveWithdrawal(requestId: string): Promise<void> {
    return apiClient.post(`/partner/withdrawals/${requestId}/approve`);
  }

  async rejectWithdrawal(requestId: string, reason: string): Promise<void> {
    return apiClient.post(`/partner/withdrawals/${requestId}/reject`, { reason });
  }

  async processBatchWithdrawal(requestIds: string[]): Promise<void> {
    return apiClient.post('/partner/withdrawals/batch-process', { requestIds });
  }

  // 에너지 관리 API
  async getEnergyPools(page: number = 1, limit: number = 20): Promise<{
    pools: EnergyPool[];
    total: number;
  }> {
    return apiClient.get(`/partner/energy/pools?page=${page}&limit=${limit}`);
  }

  async getEnergyStats(): Promise<EnergyStats> {
    return apiClient.get('/partner/energy/stats');
  }

  async getEnergyTransactions(page: number = 1, limit: number = 20, filters?: {
    type?: string;
    status?: string;
    dateFrom?: string;
    dateTo?: string;
  }): Promise<{
    transactions: EnergyTransaction[];
    total: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });
    return apiClient.get(`/partner/energy/transactions?${params}`);
  }

  async createEnergyPool(pool: {
    name: string;
    totalCapacity: number;
    pricePerUnit: number;
  }): Promise<EnergyPool> {
    return apiClient.post('/partner/energy/pools', pool);
  }

  async updateEnergyPool(poolId: string, updates: Partial<EnergyPool>): Promise<void> {
    return apiClient.put(`/partner/energy/pools/${poolId}`, updates);
  }

  async deleteEnergyPool(poolId: string): Promise<void> {
    return apiClient.delete(`/partner/energy/pools/${poolId}`);
  }

  // 분석 및 통계 API
  async getAnalyticsData(period: 'day' | 'week' | 'month' | 'year'): Promise<AnalyticsData[]> {
    return apiClient.get(`/partner/analytics?period=${period}`);
  }

  async getPartnerProfile(): Promise<PartnerProfile> {
    return apiClient.get('/partner/profile');
  }

  async updatePartnerProfile(updates: Partial<PartnerProfile>): Promise<void> {
    return apiClient.put('/partner/profile', updates);
  }

  // 알림 및 설정 API
  async getNotifications(page: number = 1, limit: number = 20): Promise<{
    notifications: Array<{
      id: string;
      title: string;
      message: string;
      type: 'info' | 'warning' | 'error' | 'success';
      isRead: boolean;
      createdAt: string;
    }>;
    total: number;
  }> {
    return apiClient.get(`/partner/notifications?page=${page}&limit=${limit}`);
  }

  async markNotificationAsRead(notificationId: string): Promise<void> {
    return apiClient.put(`/partner/notifications/${notificationId}/read`);
  }

  async getSettings(): Promise<{
    autoApprovalEnabled: boolean;
    maxWithdrawalAmount: number;
    notificationPreferences: {
      email: boolean;
      sms: boolean;
      push: boolean;
    };
  }> {
    return apiClient.get('/partner/settings');
  }

  async updateSettings(settings: {
    autoApprovalEnabled?: boolean;
    maxWithdrawalAmount?: number;
    notificationPreferences?: {
      email?: boolean;
      sms?: boolean;
      push?: boolean;
    };
  }): Promise<void> {
    return apiClient.put('/partner/settings', settings);
  }
}

export const partnerAdminService = new PartnerAdminService();
export default partnerAdminService;
