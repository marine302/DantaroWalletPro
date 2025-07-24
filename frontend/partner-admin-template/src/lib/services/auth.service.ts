/**
 * 인증 서비스 - JWT 토큰 기반 로그인/회원가입 관리
 */

import { httpClient } from '../api';
import type { LoginCredentials, RegisterData, User, AuthResponse } from '../../types';
import { mockAuthService, shouldUseMockData } from './mock.service';

// API 응답 타입 정의
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
  user: User;
}

interface RegisterResponse {
  data: {
    success: boolean;
    message: string;
    data: {
      access_token: string;
      refresh_token: string;
      user: User;
      expires_in?: number;
    };
  };
}

interface RefreshTokenResponse {
  data: {
    success: boolean;
    message: string;
    data: {
      access_token: string;
      refresh_token: string;
    };
  };
}

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
    // 개발 환경에서는 Mock 데이터 사용
    if (shouldUseMockData()) {
      const response = await mockAuthService.login(credentials.email, credentials.password);
      
      if (response.success) {
        TokenManager.setTokens(
          response.data.access_token,
          response.data.refresh_token
        );
      }
      
      return response;
    }

    // 실제 API 호출
    const response = await httpClient.post<LoginResponse>('/auth/login', credentials as unknown as Record<string, unknown>);
    
    if (response.access_token) {
      TokenManager.setTokens(
        response.access_token,
        response.refresh_token
      );
    }
    
    // API 응답을 AuthResponse 형식으로 변환
    return {
      success: true,
      message: 'Login successful',
      data: {
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        user: response.user,
        expires_in: response.expires_in || 3600
      }
    };
  },

  /**
   * 회원가입
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    // 개발 환경에서는 Mock 데이터 사용
    if (shouldUseMockData()) {
      const response = await mockAuthService.register(data.email, data.username, data.password);
      
      if (response.success) {
        TokenManager.setTokens(
          response.data.access_token,
          response.data.refresh_token
        );
      }
      
      return response;
    }

    // 실제 API 호출
    const response = await httpClient.post<RegisterResponse>('/auth/register', data as unknown as Record<string, unknown>);
    
    if (response.data.success) {
      TokenManager.setTokens(
        response.data.data.access_token,
        response.data.data.refresh_token
      );
    }
    
    return {
      success: response.data.success,
      message: response.data.message,
      data: {
        access_token: response.data.data.access_token,
        refresh_token: response.data.data.refresh_token,
        user: response.data.data.user,
        expires_in: response.data.data.expires_in || 3600
      }
    };
  },

  /**
   * 로그아웃
   */
  async logout(): Promise<void> {
    try {
      await httpClient.post('/auth/logout');
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

    const response = await httpClient.post<RefreshTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });

    if (response.data.success) {
      TokenManager.setTokens(
        response.data.data.access_token,
        response.data.data.refresh_token
      );
      
      // 새로운 토큰으로 사용자 정보 조회
      try {
        const userInfo = await this.getCurrentUser();
        return {
          success: response.data.success,
          message: response.data.message,
          data: {
            access_token: response.data.data.access_token,
            refresh_token: response.data.data.refresh_token,
            user: userInfo,
            expires_in: 3600
          }
        };
      } catch {
        // 사용자 정보 조회 실패 시 기본 정보로 반환
        return {
          success: response.data.success,
          message: response.data.message,
          data: {
            access_token: response.data.data.access_token,
            refresh_token: response.data.data.refresh_token,
            user: {} as User, // 빈 사용자 객체
            expires_in: 3600
          }
        };
      }
    }

    throw new Error('Token refresh failed');
  },

  /**
   * 현재 사용자 정보 조회
   */
  async getCurrentUser(): Promise<User> {
    // 개발 환경에서는 Mock 데이터 사용
    if (shouldUseMockData()) {
      const { DEMO_PARTNER_ACCOUNT } = await import('./mock.service');
      return DEMO_PARTNER_ACCOUNT;
    }

    // 실제 API 호출
    const response = await httpClient.get<User>('/auth/me');
    return response;
  },

  /**
   * 비밀번호 변경
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await httpClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
  },

  /**
   * 비밀번호 재설정 요청
   */
  async requestPasswordReset(email: string): Promise<void> {
    await httpClient.post('/auth/forgot-password', { email });
  },

  /**
   * 비밀번호 재설정
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await httpClient.post('/auth/reset-password', {
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
