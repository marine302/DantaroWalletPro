import { apiClient } from './api-client';

// 감사 및 컴플라이언스 관련 타입
export interface AuditLog {
  id: string;
  transactionId: string;
  action: string;
  userId: string;
  timestamp: string;
  details: Record<string, unknown>;
  riskLevel: 'low' | 'medium' | 'high';
  status: 'pending' | 'approved' | 'flagged';
}

export interface ComplianceStats {
  totalTransactions: number;
  flaggedTransactions: number;
  pendingReviews: number;
  complianceRate: number;
  avgRiskScore: number;
}

export interface SuspiciousActivity {
  id: string;
  type: string;
  description: string;
  riskScore: number;
  detectedAt: string;
  status: 'new' | 'investigating' | 'resolved' | 'false_positive';
}

// 외부 에너지 시장 관련 타입
export interface EnergyProvider {
  id: number;
  name: string;
  providerType: string;
  isActive: boolean;
  lastPrice: number;
  successRate: number;
  status: 'online' | 'offline' | 'maintenance';
}

export interface EnergyPurchase {
  id: number;
  providerId: number;
  energyAmount: number;
  pricePerEnergy: number;
  totalCost: number;
  status: 'pending' | 'approved' | 'executing' | 'completed' | 'failed';
  createdAt: string;
}

export interface MarketStats {
  totalProviders: number;
  activeProviders: number;
  totalEnergyPurchased: number;
  totalCostToday: number;
  averagePrice: number;
}

// 파트너 온보딩 관련 타입
export interface Partner {
  id: number;
  companyName: string;
  contactEmail: string;
  onboardingStage: string;
  status: 'active' | 'pending' | 'suspended' | 'rejected';
  registrationDate: string;
  riskScore: number;
}

export interface OnboardingStats {
  totalPartners: number;
  pendingApproval: number;
  activePartners: number;
  completedThisMonth: number;
  averageOnboardingTime: number;
  rejectionRate: number;
}

// API 서비스 클래스
export class SuperAdminService {
  // 감사 및 컴플라이언스 API
  async getAuditLogs(page: number = 1, limit: number = 20): Promise<{
    logs: AuditLog[];
    total: number;
  }> {
    return apiClient.get(`/audit/logs?page=${page}&limit=${limit}`);
  }

  async getComplianceStats(): Promise<ComplianceStats> {
    return apiClient.get('/audit/compliance-stats');
  }

  async getSuspiciousActivities(): Promise<SuspiciousActivity[]> {
    return apiClient.get('/audit/suspicious-activities');
  }

  async updateSuspiciousActivityStatus(
    id: string,
    status: SuspiciousActivity['status']
  ): Promise<void> {
    return apiClient.put(`/audit/suspicious-activities/${id}`, { status });
  }

  // 외부 에너지 시장 API
  async getEnergyProviders(): Promise<EnergyProvider[]> {
    return apiClient.get('/external-energy/providers');
  }

  async getMarketStats(): Promise<MarketStats> {
    return apiClient.get('/external-energy/market-stats');
  }

  async createEnergyPurchase(purchase: {
    providerId: number;
    energyAmount: number;
    margin: number;
  }): Promise<EnergyPurchase> {
    return apiClient.post('/external-energy/purchase', purchase);
  }

  async getEnergyPurchases(): Promise<{
    purchases: EnergyPurchase[];
    total: number;
  }> {
    // 백엔드 API가 /external-energy/purchase로 되어 있음 (복수형 아님)
    const _purchases = await apiClient.get('/external-energy/purchase');
    return {
      purchases: Array.isArray(purchases) ? purchases : [],
      total: Array.isArray(purchases) ? purchases.length : 0
    };
  }

  async updateProviderStatus(
    providerId: number,
    isActive: boolean
  ): Promise<void> {
    return apiClient.put(`/external-energy/providers/${providerId}`, { isActive });
  }

  // 파트너 온보딩 API
  async getPartners(page: number = 1, limit: number = 20): Promise<{
    partners: Partner[];
    total: number;
  }> {
    return apiClient.get(`/partner-onboarding/partners?page=${page}&limit=${limit}`);
  }

  async getOnboardingStats(): Promise<OnboardingStats> {
    return apiClient.get('/partner-onboarding/stats');
  }

  async approvePartner(partnerId: number): Promise<void> {
    return apiClient.post(`/partner-onboarding/partners/${partnerId}/approve`);
  }

  async rejectPartner(partnerId: number, reason: string): Promise<void> {
    return apiClient.post(`/partner-onboarding/partners/${partnerId}/reject`, { reason });
  }

  async advancePartnerStage(partnerId: number): Promise<void> {
    return apiClient.post(`/partner-onboarding/partners/${partnerId}/advance-stage`);
  }

  async updatePartnerRiskScore(partnerId: number, riskScore: number): Promise<void> {
    return apiClient.put(`/partner-onboarding/partners/${partnerId}/risk-score`, { riskScore });
  }
}

export const _superAdminService = new SuperAdminService();
export default superAdminService;
