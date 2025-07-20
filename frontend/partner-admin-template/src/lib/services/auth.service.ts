/**
 * 인증 서비스 - JWT 토큰 기반 로그인/회원가입 관리
 */

import { apiClient } from '../api-client';
import type { LoginCredentials, RegisterData, User, AuthResponse } from '../../types';

// JWT 토큰 저장/관리
export class TokenManager {
  private static readonly TOKEN_KEY = process.env.NEXT_PUBLIC_JWT_COOKIE_NAME || 'dantaro_admin_token';
  private static readonly REFRESH_TOKEN_KEY = process.env.NEXT_PUBLIC_REFRESH_TOKEN_COOKIE_NAME || 'dantaro_admin_refresh';

  static setTokens(accessToken: string, refreshToken?: string): void {
    if (typeof window === 'undefined') return;
    
    // 보안을 위해 httpOnly 쿠키 사용을 권장하지만, 개발 단계에서는 localStorage 사용
    localStorage.setItem(this.TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }
  }

  static getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static clearTokens(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  static isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}

export const authService = {
  /**
   * 로그인
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    
    if (response.data.success) {
      TokenManager.setTokens(
        response.data.data.access_token,
        response.data.data.refresh_token
      );
    }
    
    return response.data;
  },

  /**
   * 회원가입
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data);
    
    if (response.data.success) {
      TokenManager.setTokens(
        response.data.data.access_token,
        response.data.data.refresh_token
      );
    }
    
    return response.data;
  },

  /**
   * 로그아웃
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      TokenManager.clearTokens();
    }
  },

  /**
   * 토큰 갱신
   */
  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new Error('Refresh token not found');
    }

    const response = await apiClient.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });

    if (response.data.success) {
      TokenManager.setTokens(
        response.data.data.access_token,
        response.data.data.refresh_token
      );
    }

    return response.data;
  },

  /**
   * 현재 사용자 정보 조회
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<{ data: User }>('/auth/me');
    return response.data.data;
  },

  /**
   * 비밀번호 변경
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
  },

  /**
   * 비밀번호 재설정 요청
   */
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/auth/forgot-password', { email });
  },

  /**
   * 비밀번호 재설정
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword
    });
  },

  /**
   * 현재 인증 상태 확인
   */
  isAuthenticated(): boolean {
    return TokenManager.isAuthenticated();
  },

  /**
   * 인증 헤더 가져오기
   */
  getAuthHeader(): string | null {
    const token = TokenManager.getAccessToken();
    return token ? `Bearer ${token}` : null;
  }
};

export default authService;
