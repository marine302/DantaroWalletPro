/**
 * External Energy API 연동 서비스
 * 백엔드 API와 연동하여 외부 에너지 공급업체 데이터를 관리합니다.
 * 백엔드 스키마와 정확히 일치하는 타입 정의
 */

import { apiClient } from '@/lib/api';

// 백엔드 ProviderStatus enum과 정확히 일치
export type ProviderStatus = 'online' | 'offline' | 'maintenance';

// 백엔드 ProviderFees 스키마와 정확히 일치
export interface ProviderFees {
  tradingFee: number;
  withdrawalFee: number;
}

// 백엔드 EnergyProviderResponse 스키마와 정확히 일치
export interface ExternalEnergyProvider {
  id: string;
  name: string;
  status: ProviderStatus;
  pricePerEnergy: number;
  availableEnergy: number;
  reliability: number;
  avgResponseTime: number;
  minOrderSize: number;
  maxOrderSize: number;
  fees: ProviderFees;
  lastUpdated: string;
}

// 백엔드 MarketSummary 스키마와 정확히 일치
export interface ExternalMarketSummary {
  bestPrice: number;
  bestProvider: string;
  totalProviders: number;
  activeProviders: number;
  avgPrice: number;
  priceChange24h: number;
  totalVolume: number;
  lastUpdated: string;
}

// 백엔드 API 응답 래퍼
export interface ProvidersListResponse {
  success: boolean;
  data: ExternalEnergyProvider[];
}

export interface ProviderDetailResponse {
  success: boolean;
  data: ExternalEnergyProvider;
}

export interface MarketSummaryResponse {
  success: boolean;
  data: ExternalMarketSummary;
}

export interface ExternalEnergyOrder {
  providerId: string;
  amount: number;
  orderType: 'market' | 'limit';
  duration: number;
  priceLimit?: number;
}

export interface ExternalEnergyOrderResponse {
  id: string;
  providerId: string;
  userId: string;
  amount: number;
  price: number;
  totalCost: number;
  orderType: 'market' | 'limit';
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  duration: number;
  fees: {
    trading: number;
    withdrawal: number;
  };
  externalOrderId?: string;
  transactionHash?: string;
  createdAt: string;
  filledAt?: string;
}

export interface EnergyPurchaseRequest {
  energy_amount: number;
  target_address: string;
}

export interface UserEnergyBalance {
  address: string;
  balance: number;
  lastUpdated: string;
}

export interface SystemStatus {
  status: string;
  providers: Array<{
    name: string;
    status: string;
    lastCheck: string;
  }>;
  totalActiveProviders: number;
  systemLoad: number;
  lastUpdated: string;
}

class ExternalEnergyService {
  private readonly baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000/api/v1';

    console.log('🔌 External Energy Service initialized:', {
      baseURL: this.baseURL
    });
  }

  /**
   * 공개 공급업체 목록 조회 (인증 불필요)
   */
  async getPublicProviders(): Promise<ExternalEnergyProvider[]> {
    try {
      const _response = await fetch(`${this.baseURL}/public/providers`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: ProvidersListResponse = await response.json();
      return data.data;
    } catch (error) {
      console.error('Failed to fetch public providers:', error);
      return this.getMockProviders();
    }
  }

  /**
   * 공급업체 요약 정보 조회 (인증 불필요)
   */
  async getProvidersSummary(): Promise<ExternalMarketSummary> {
    try {
      const _response = await fetch(`${this.baseURL}/public/providers/summary`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: MarketSummaryResponse = await response.json();
      return data.data;
    } catch (error) {
      console.error('Failed to fetch providers summary:', error);
      return this.getMockMarketSummary();
    }
  }

  /**
   * 모든 활성 에너지 공급업체 목록 조회 (인증 필요)
   */
  async getProviders(): Promise<ExternalEnergyProvider[]> {
    try {
      console.log('🔌 Fetching providers from backend...');
      const _response = await apiClient.makeResilientRequest<ProvidersListResponse>(
        '/external-energy/providers'
      );
      console.log('✅ Providers fetched successfully:', response);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch providers:', error);
      return this.getMockProviders();
    }
  }

  /**
   * 공급업체 상태 확인 (Health Check)
   */
  async getProvidersHealth(): Promise<any[]> {
    try {
      console.log('🔌 Checking providers health...');
      const _response = await apiClient.makeResilientRequest<{ success: boolean; data: any[] }>(
        '/external-energy/providers/health'
      );
      console.log('✅ Providers health checked successfully:', response);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to check providers health:', error);
      return [];
    }
  }

  /**
   * 특정 공급업체 가격 정보 조회
   */
  async getProviderPrices(providerName: string): Promise<any> {
    try {
      console.log(`🔌 Fetching prices for ${providerName}...`);
      const _response = await apiClient.makeResilientRequest<{ success: boolean; data: any }>(
        `/external-energy/providers/${providerName}/prices`
      );
      console.log('✅ Provider prices fetched successfully:', response);
      return response.data;
    } catch (error) {
      console.error(`❌ Failed to fetch prices for ${providerName}:`, error);
      return null;
    }
  }

  /**
   * 특정 공급업체에서 주소별 에너지 잔액 조회
   */
  async getProviderBalance(providerName: string, address: string): Promise<UserEnergyBalance | null> {
    try {
      console.log(`🔌 Fetching balance for ${providerName} at ${address}...`);
      const _response = await apiClient.makeResilientRequest<{ success: boolean; data: any }>(
        `/external-energy/providers/${providerName}/balance?address=${address}`
      );
      console.log('✅ Provider balance fetched successfully:', response);
      return response.data;
    } catch (error) {
      console.error(`❌ Failed to fetch balance for ${providerName}:`, error);
      return null;
    }
  }

  /**
   * 멀티 공급업체 에너지 구매
   */
  async purchaseEnergyMultiProvider(request: EnergyPurchaseRequest): Promise<any> {
    try {
      return await apiClient.post('/external-energy/purchase/multi-provider', request);
    } catch (error) {
      console.error('Failed to purchase energy from multi-provider:', error);
      throw error;
    }
  }

  /**
   * 파트너 에너지 구매
   */
  async purchaseEnergyPartner(request: EnergyPurchaseRequest): Promise<any> {
    try {
      return await apiClient.post('/external-energy/partner/purchase', request);
    } catch (error) {
      console.error('Failed to purchase energy for partner:', error);
      throw error;
    }
  }

  /**
   * 사용자 에너지 잔액 조회
   */
  async getUserEnergyBalance(address: string): Promise<UserEnergyBalance | null> {
    try {
      return await apiClient.get(`/external-energy/user/balance?address=${address}`);
    } catch (error) {
      console.error('Failed to fetch user energy balance:', error);
      return null;
    }
  }

  /**
   * 시스템 상태 조회
   */
  async getSystemStatus(): Promise<SystemStatus> {
    try {
      return await apiClient.get('/external-energy/management/system-status');
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      return this.getMockSystemStatus();
    }
  }

  /**
   * 관리자 공급업체 목록 조회
   */
  async getAdminProviders(): Promise<ExternalEnergyProvider[]> {
    try {
      return await apiClient.get('/external-energy/admin/providers');
    } catch (error) {
      console.error('Failed to fetch admin providers:', error);
      return this.getMockProviders();
    }
  }

  /**
   * Mock 데이터 생성 메서드들
   */
  private getMockProviders(): ExternalEnergyProvider[] {
    return [
      {
        id: 'provider-1',
        name: 'EnergyTron',
        status: 'online',
        pricePerEnergy: 0.85,
        availableEnergy: 1500000,
        reliability: 99.5,
        avgResponseTime: 120,
        minOrderSize: 1000,
        maxOrderSize: 100000,
        fees: {
          tradingFee: 0.1,
          withdrawalFee: 0.05
        },
        lastUpdated: new Date().toISOString()
      },
      {
        id: 'provider-2',
        name: 'TronNRG',
        status: 'online',
        pricePerEnergy: 0.92,
        availableEnergy: 2000000,
        reliability: 98.8,
        avgResponseTime: 95,
        minOrderSize: 500,
        maxOrderSize: 150000,
        fees: {
          tradingFee: 0.15,
          withdrawalFee: 0.08
        },
        lastUpdated: new Date().toISOString()
      },
      {
        id: 'provider-3',
        name: 'PowerNet',
        status: 'maintenance',
        pricePerEnergy: 0.78,
        availableEnergy: 800000,
        reliability: 97.2,
        avgResponseTime: 180,
        minOrderSize: 2000,
        maxOrderSize: 50000,
        fees: {
          tradingFee: 0.12,
          withdrawalFee: 0.06
        },
        lastUpdated: new Date().toISOString()
      }
    ];
  }

  private getMockMarketSummary(): ExternalMarketSummary {
    return {
      bestPrice: 0.78,
      bestProvider: 'PowerNet',
      totalProviders: 3,
      activeProviders: 2,
      avgPrice: 0.85,
      priceChange24h: -2.3,
      totalVolume: 4300000,
      lastUpdated: new Date().toISOString()
    };
  }

  private getMockSystemStatus(): SystemStatus {
    return {
      status: 'operational',
      providers: [
        { name: 'EnergyTron', status: 'online', lastCheck: new Date().toISOString() },
        { name: 'TronNRG', status: 'online', lastCheck: new Date().toISOString() },
        { name: 'PowerNet', status: 'maintenance', lastCheck: new Date().toISOString() }
      ],
      totalActiveProviders: 2,
      systemLoad: 75,
      lastUpdated: new Date().toISOString()
    };
  }
}

export const _externalEnergyService = new ExternalEnergyService();
