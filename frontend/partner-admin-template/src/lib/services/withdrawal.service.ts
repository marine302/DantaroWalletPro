/**
 * 출금 관리 API 서비스
 */

import { apiClient, ApiResponse, PaginatedResponse } from '../api-client';
import { Withdrawal, WithdrawalCreateData, WithdrawalUpdateData } from '@/types';

export interface WithdrawalListParams {
  page?: number;
  limit?: number;
  status?: string;
  userId?: string;
  currency?: string;
  minAmount?: number;
  maxAmount?: number;
  from?: string;
  to?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export class WithdrawalService {
  // 출금 목록 조회
  static async getWithdrawals(params: WithdrawalListParams = {}): Promise<ApiResponse<PaginatedResponse<Withdrawal>>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/withdrawals${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<PaginatedResponse<Withdrawal>>(endpoint);
  }

  // 출금 상세 조회
  static async getWithdrawal(id: string): Promise<ApiResponse<Withdrawal>> {
    return apiClient.get<Withdrawal>(`/withdrawals/${id}`);
  }

  // 출금 요청 생성
  static async createWithdrawal(data: WithdrawalCreateData): Promise<ApiResponse<Withdrawal>> {
    return apiClient.post<Withdrawal>('/withdrawals', data);
  }

  // 출금 승인
  static async approveWithdrawal(id: string, adminNotes?: string): Promise<ApiResponse<Withdrawal>> {
    return apiClient.patch<Withdrawal>(`/withdrawals/${id}/approve`, { adminNotes });
  }

  // 출금 거부
  static async rejectWithdrawal(id: string, reason: string, adminNotes?: string): Promise<ApiResponse<Withdrawal>> {
    return apiClient.patch<Withdrawal>(`/withdrawals/${id}/reject`, { reason, adminNotes });
  }

  // 출금 취소
  static async cancelWithdrawal(id: string, reason: string): Promise<ApiResponse<Withdrawal>> {
    return apiClient.patch<Withdrawal>(`/withdrawals/${id}/cancel`, { reason });
  }

  // 출금 처리 완료
  static async completeWithdrawal(id: string, txHash: string, adminNotes?: string): Promise<ApiResponse<Withdrawal>> {
    return apiClient.patch<Withdrawal>(`/withdrawals/${id}/complete`, { txHash, adminNotes });
  }

  // 출금 통계
  static async getWithdrawalStats(): Promise<ApiResponse<{
    totalAmount: number;
    totalCount: number;
    pendingAmount: number;
    pendingCount: number;
    approvedAmount: number;
    approvedCount: number;
    rejectedCount: number;
    dailyStats: Array<{
      date: string;
      amount: number;
      count: number;
    }>;
  }>> {
    return apiClient.get('/withdrawals/stats');
  }

  // 출금 한도 설정 조회
  static async getWithdrawalLimits(): Promise<ApiResponse<{
    dailyLimit: number;
    monthlyLimit: number;
    minAmount: number;
    maxAmount: number;
    fees: Record<string, number>;
  }>> {
    return apiClient.get('/withdrawals/limits');
  }

  // 출금 한도 설정 업데이트
  static async updateWithdrawalLimits(limits: {
    dailyLimit?: number;
    monthlyLimit?: number;
    minAmount?: number;
    maxAmount?: number;
    fees?: Record<string, number>;
  }): Promise<ApiResponse<any>> {
    return apiClient.patch('/withdrawals/limits', limits);
  }

  // 일괄 처리
  static async bulkProcess(ids: string[], action: 'approve' | 'reject' | 'cancel', data?: any): Promise<ApiResponse<{
    success: string[];
    failed: Array<{ id: string; error: string }>;
  }>> {
    return apiClient.post('/withdrawals/bulk-process', {
      ids,
      action,
      data
    });
  }
}
