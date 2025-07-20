/**
 * 에너지 관리 API 서비스
 */

import { apiClient, ApiResponse, PaginatedResponse } from '../api-client';
import { EnergyPool, EnergyTransaction, EnergyRental, EnergySettings } from '@/types';

export interface EnergyListParams {
  page?: number;
  limit?: number;
  type?: string;
  status?: string;
  userId?: string;
  from?: string;
  to?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export class EnergyService {
  // 에너지 풀 목록 조회
  static async getEnergyPools(): Promise<ApiResponse<EnergyPool[]>> {
    return apiClient.get<EnergyPool[]>('/energy/pools');
  }

  // 에너지 풀 상세 조회
  static async getEnergyPool(id: string): Promise<ApiResponse<EnergyPool>> {
    return apiClient.get<EnergyPool>(`/energy/pools/${id}`);
  }

  // 에너지 풀 생성
  static async createEnergyPool(data: Partial<EnergyPool>): Promise<ApiResponse<EnergyPool>> {
    return apiClient.post<EnergyPool>('/energy/pools', data);
  }

  // 에너지 풀 업데이트
  static async updateEnergyPool(id: string, data: Partial<EnergyPool>): Promise<ApiResponse<EnergyPool>> {
    return apiClient.patch<EnergyPool>(`/energy/pools/${id}`, data);
  }

  // 에너지 풀 삭제
  static async deleteEnergyPool(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`/energy/pools/${id}`);
  }

  // 에너지 거래 내역 조회
  static async getEnergyTransactions(params: EnergyListParams = {}): Promise<ApiResponse<PaginatedResponse<EnergyTransaction>>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/energy/transactions${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<PaginatedResponse<EnergyTransaction>>(endpoint);
  }

  // 에너지 거래 상세 조회
  static async getEnergyTransaction(id: string): Promise<ApiResponse<EnergyTransaction>> {
    return apiClient.get<EnergyTransaction>(`/energy/transactions/${id}`);
  }

  // 에너지 렌탈 목록 조회
  static async getEnergyRentals(params: EnergyListParams = {}): Promise<ApiResponse<PaginatedResponse<EnergyRental>>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/energy/rentals${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<PaginatedResponse<EnergyRental>>(endpoint);
  }

  // 에너지 렌탈 생성
  static async createEnergyRental(data: Partial<EnergyRental>): Promise<ApiResponse<EnergyRental>> {
    return apiClient.post<EnergyRental>('/energy/rentals', data);
  }

  // 에너지 렌탈 업데이트
  static async updateEnergyRental(id: string, data: Partial<EnergyRental>): Promise<ApiResponse<EnergyRental>> {
    return apiClient.patch<EnergyRental>(`/energy/rentals/${id}`, data);
  }

  // 에너지 렌탈 취소
  static async cancelEnergyRental(id: string, reason: string): Promise<ApiResponse<EnergyRental>> {
    return apiClient.patch<EnergyRental>(`/energy/rentals/${id}/cancel`, { reason });
  }

  // 에너지 설정 조회
  static async getEnergySettings(): Promise<ApiResponse<EnergySettings>> {
    return apiClient.get<EnergySettings>('/energy/settings');
  }

  // 에너지 설정 업데이트
  static async updateEnergySettings(settings: Partial<EnergySettings>): Promise<ApiResponse<EnergySettings>> {
    return apiClient.patch<EnergySettings>('/energy/settings', settings);
  }

  // 에너지 통계
  static async getEnergyStats(): Promise<ApiResponse<{
    totalEnergy: number;
    usedEnergy: number;
    availableEnergy: number;
    totalPools: number;
    activePools: number;
    totalRentals: number;
    activeRentals: number;
    dailyUsage: Array<{
      date: string;
      usage: number;
      rental: number;
    }>;
    poolDistribution: Array<{
      poolId: string;
      poolName: string;
      energy: number;
      percentage: number;
    }>;
  }>> {
    return apiClient.get('/energy/stats');
  }

  // 실시간 에너지 모니터링
  static async getRealTimeEnergyData(): Promise<ApiResponse<{
    currentUsage: number;
    peakUsage: number;
    averageUsage: number;
    efficiency: number;
    alerts: Array<{
      id: string;
      type: string;
      message: string;
      timestamp: string;
    }>;
  }>> {
    return apiClient.get('/energy/realtime');
  }
}
