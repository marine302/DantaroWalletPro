/**
 * 사용자 관리 API 서비스
 */

import { apiClient } from '../api-client';
import { User, UserCreateData, UserUpdateData } from '@/types';
import type { ApiResponse } from '@/types';

export interface UserListParams {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;
  role?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export class UserService {
  // 사용자 목록 조회
  static async getUsers(params: UserListParams = {}): Promise<ApiResponse<PaginatedResponse<User>>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/users${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<PaginatedResponse<User>>(endpoint);
  }

  // 사용자 상세 조회
  static async getUser(id: string): Promise<ApiResponse<User>> {
    return apiClient.get<User>(`/users/${id}`);
  }

  // 사용자 생성
  static async createUser(userData: UserCreateData): Promise<ApiResponse<User>> {
    return apiClient.post<User>('/users', userData);
  }

  // 사용자 수정
  static async updateUser(id: string, userData: UserUpdateData): Promise<ApiResponse<User>> {
    return apiClient.patch<User>(`/users/${id}`, userData);
  }

  // 사용자 삭제
  static async deleteUser(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`/users/${id}`);
  }

  // 사용자 상태 변경
  static async updateUserStatus(id: string, status: string): Promise<ApiResponse<User>> {
    return apiClient.patch<User>(`/users/${id}/status`, { status });
  }

  // 사용자 권한 변경
  static async updateUserRole(id: string, role: string): Promise<ApiResponse<User>> {
    return apiClient.patch<User>(`/users/${id}/role`, { role });
  }

  // 사용자 통계
  static async getUserStats(): Promise<ApiResponse<{
    total: number;
    active: number;
    inactive: number;
    suspended: number;
    newThisMonth: number;
    growthRate: number;
  }>> {
    return apiClient.get('/users/stats');
  }

  // 사용자 활동 로그
  static async getUserActivities(userId: string, params: {
    page?: number;
    limit?: number;
    from?: string;
    to?: string;
  } = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/users/${userId}/activities${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<PaginatedResponse<any>>(endpoint);
  }
}
