/**
 * 분석 및 대시보드 API 서비스
 */

import { apiClient } from '../api-client';
import { DashboardStats, ChartData } from '@/types';
import type { ApiResponse } from '@/types';

export interface AnalyticsParams {
  from?: string;
  to?: string;
  granularity?: 'hour' | 'day' | 'week' | 'month';
  metrics?: string[];
  groupBy?: string[];
}

export class AnalyticsService {
  // 대시보드 통계 조회
  static async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    return apiClient.get<DashboardStats>('/analytics/dashboard');
  }

  // 사용자 분석
  static async getUserAnalytics(params: AnalyticsParams = {}): Promise<ApiResponse<{
    userGrowth: ChartData[];
    userActivity: ChartData[];
    userRetention: ChartData[];
    userSegments: Array<{
      segment: string;
      count: number;
      percentage: number;
    }>;
    topUsers: Array<{
      userId: string;
      username: string;
      activity: number;
      value: number;
    }>;
  }>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/analytics/users${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  }

  // 거래 분석
  static async getTransactionAnalytics(params: AnalyticsParams = {}): Promise<ApiResponse<{
    transactionVolume: ChartData[];
    transactionCount: ChartData[];
    averageTransactionSize: ChartData[];
    transactionsByType: Array<{
      type: string;
      count: number;
      volume: number;
      percentage: number;
    }>;
    topTransactions: Array<{
      id: string;
      amount: number;
      type: string;
      timestamp: string;
      userId: string;
    }>;
  }>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/analytics/transactions${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  }

  // 에너지 분석
  static async getEnergyAnalytics(params: AnalyticsParams = {}): Promise<ApiResponse<{
    energyUsage: ChartData[];
    energyEfficiency: ChartData[];
    poolPerformance: Array<{
      poolId: string;
      poolName: string;
      usage: number;
      efficiency: number;
      roi: number;
    }>;
    rentalTrends: ChartData[];
    costAnalysis: ChartData[];
  }>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/analytics/energy${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  }

  // 수익 분석
  static async getRevenueAnalytics(params: AnalyticsParams = {}): Promise<ApiResponse<{
    revenue: ChartData[];
    profit: ChartData[];
    revenueBySource: Array<{
      source: string;
      amount: number;
      percentage: number;
      growth: number;
    }>;
    monthlyRecurring: ChartData[];
    projections: ChartData[];
  }>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/analytics/revenue${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  }

  // 성능 분석
  static async getPerformanceAnalytics(params: AnalyticsParams = {}): Promise<ApiResponse<{
    systemHealth: {
      cpu: number;
      memory: number;
      disk: number;
      network: number;
    };
    responseTime: ChartData[];
    errorRate: ChartData[];
    throughput: ChartData[];
    alerts: Array<{
      id: string;
      severity: string;
      message: string;
      timestamp: string;
      resolved: boolean;
    }>;
  }>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/analytics/performance${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  }

  // 커스텀 리포트 생성
  static async generateCustomReport(config: {
    name: string;
    description?: string;
    metrics: string[];
    filters: Record<string, any>;
    groupBy?: string[];
    dateRange: {
      from: string;
      to: string;
    };
    format?: 'json' | 'csv' | 'pdf';
  }): Promise<ApiResponse<{
    reportId: string;
    downloadUrl?: string;
    data?: any;
  }>> {
    return apiClient.post('/analytics/reports/custom', config);
  }

  // 리포트 다운로드
  static async downloadReport(reportId: string, format: 'csv' | 'pdf' = 'csv'): Promise<ApiResponse<{
    downloadUrl: string;
  }>> {
    return apiClient.get(`/analytics/reports/${reportId}/download?format=${format}`);
  }
}
