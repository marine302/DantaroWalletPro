/**
 * 에너지 렌탈 API 클라이언트
 * 실제 백엔드 연결을 위한 구조
 */

import { apiClient } from '../api-client';
import { ENERGY_RENTAL_CONFIG } from '../config';
import type { 
  EnergyRentalPlan, 
  EnergyRental, 
  EnergyUsageStats, 
  EnergyBilling, 
  EnergySupplyStatus,
  EnergyUsagePrediction
} from '../../types';

// URL 파라미터 치환 유틸리티
function buildUrl(template: string, params: Record<string, string | number>): string {
  return Object.entries(params).reduce((url, [key, value]) => {
    return url.replace(`:${key}`, String(value));
  }, template);
}

// 에너지 렌탈 API 클래스
export class EnergyRentalApi {
  
  /**
   * 사용 가능한 렌탈 플랜 조회
   */
  async getAvailablePlans(): Promise<EnergyRentalPlan[]> {
    try {
      const response = await apiClient.get<EnergyRentalPlan[]>(
        ENERGY_RENTAL_CONFIG.ENDPOINTS.PLANS
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch rental plans:', error);
      throw error;
    }
  }

  /**
   * 특정 파트너의 에너지 사용 통계 조회
   */
  async getPartnerUsageStats(partnerId: string, period: string = '30d'): Promise<EnergyUsageStats> {
    try {
      const url = buildUrl(ENERGY_RENTAL_CONFIG.ENDPOINTS.PARTNER_USAGE, { partnerId });
      const response = await apiClient.get<EnergyUsageStats>(`${url}?period=${period}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch usage stats:', error);
      throw error;
    }
  }

  /**
   * 파트너 청구 이력 조회
   */
  async getPartnerBilling(partnerId: string): Promise<EnergyBilling[]> {
    try {
      const url = buildUrl(ENERGY_RENTAL_CONFIG.ENDPOINTS.PARTNER_BILLING, { partnerId });
      const response = await apiClient.get<EnergyBilling[]>(url);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch billing history:', error);
      throw error;
    }
  }

  /**
   * 파트너 현재 에너지 할당 정보 조회
   */
  async getPartnerAllocation(partnerId: string): Promise<EnergyRental | null> {
    try {
      const url = buildUrl(ENERGY_RENTAL_CONFIG.ENDPOINTS.PARTNER_ALLOCATION, { partnerId });
      const response = await apiClient.get<EnergyRental>(url);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch partner allocation:', error);
      return null;
    }
  }

  /**
   * 에너지 풀 상태 조회
   */
  async getPoolsStatus(): Promise<EnergySupplyStatus> {
    try {
      const response = await apiClient.get<EnergySupplyStatus>(
        ENERGY_RENTAL_CONFIG.ENDPOINTS.POOLS_STATUS
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch pools status:', error);
      throw error;
    }
  }

  /**
   * 시스템 상태 조회
   */
  async getSystemStatus(): Promise<{
    status: 'healthy' | 'degraded' | 'outage';
    last_update: string;
    issues?: string[];
  }> {
    try {
      const response = await apiClient.get<{
        status: 'healthy' | 'degraded' | 'outage';
        last_update: string;
        issues?: string[];
      }>(ENERGY_RENTAL_CONFIG.ENDPOINTS.SYSTEM_STATUS);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      throw error;
    }
  }

  /**
   * 에너지 렌탈 요청
   */
  async rentEnergy(request: {
    partner_id: string;
    plan_id: string;
    duration_hours: number;
    energy_amount: number;
  }): Promise<EnergyRental> {
    try {
      const response = await apiClient.post<EnergyRental>(
        ENERGY_RENTAL_CONFIG.ENDPOINTS.RENT_ENERGY,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to rent energy:', error);
      throw error;
    }
  }

  /**
   * 렌탈 기간 연장
   */
  async extendRental(rentalId: string, additionalHours: number): Promise<EnergyRental> {
    try {
      const response = await apiClient.post<EnergyRental>(
        ENERGY_RENTAL_CONFIG.ENDPOINTS.EXTEND_RENTAL,
        { rental_id: rentalId, additional_hours: additionalHours }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to extend rental:', error);
      throw error;
    }
  }

  /**
   * 렌탈 취소
   */
  async cancelRental(rentalId: string): Promise<{ success: boolean; refund_amount?: number }> {
    try {
      const response = await apiClient.post<{ success: boolean; refund_amount?: number }>(
        ENERGY_RENTAL_CONFIG.ENDPOINTS.CANCEL_RENTAL,
        { rental_id: rentalId }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to cancel rental:', error);
      throw error;
    }
  }

  /**
   * 에너지 사용량 예측
   */
  async predictUsage(partnerId: string, forecastDays: number = 7): Promise<EnergyUsagePrediction> {
    try {
      const response = await apiClient.get<EnergyUsagePrediction>(
        `${ENERGY_RENTAL_CONFIG.ENDPOINTS.USAGE_PREDICTION}?partner_id=${partnerId}&forecast_days=${forecastDays}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to predict usage:', error);
      throw error;
    }
  }

  /**
   * 실시간 에너지 모니터링 (WebSocket 대용으로 폴링)
   */
  async startEnergyMonitoring(
    partnerId: string, 
    callback: (usage: EnergyUsageStats) => void,
    interval: number = ENERGY_RENTAL_CONFIG.POLL_INTERVALS.USAGE_STATS
  ): Promise<() => void> {
    const intervalId = setInterval(async () => {
      try {
        const usage = await this.getPartnerUsageStats(partnerId, '1d');
        callback(usage);
      } catch (error) {
        console.error('Failed to fetch real-time usage:', error);
      }
    }, interval);

    // cleanup 함수 반환
    return () => clearInterval(intervalId);
  }
}

// 싱글톤 인스턴스
export const energyRentalApi = new EnergyRentalApi();

// 백엔드 연결 상태 확인 함수
export async function checkBackendConnection(): Promise<boolean> {
  try {
    await energyRentalApi.getSystemStatus();
    return true;
  } catch (error) {
    console.warn('Backend connection failed:', error);
    return false;
  }
}

// 에너지 렌탈 API 초기화
export async function initializeEnergyRentalApi(): Promise<void> {
  console.log('Initializing Energy Rental API...');
  
  const isConnected = await checkBackendConnection();
  
  if (isConnected) {
    console.log('✅ Energy Rental API connected successfully');
  } else {
    console.warn('⚠️ Energy Rental API connection failed - using mock data');
  }
}

export default energyRentalApi;
