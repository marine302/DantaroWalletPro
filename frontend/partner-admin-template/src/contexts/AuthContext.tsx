/**
 * 인증 컨텍스트 - 전역 인증 상태 관리
 */

'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authService, TokenManager } from '../lib/services/auth.service';
import { httpClient } from '../lib/api';
import type { AuthUser, LoginCredentials, RegisterData } from '../types';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; message: string }>;
  register: (data: RegisterData) => Promise<{ success: boolean; message: string }>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  updateUser: (userData: Partial<AuthUser>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && TokenManager.isAuthenticated();

  // 컴포넌트 마운트 시 인증 상태 확인
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // 토큰 변경 시 API 클라이언트 헤더 업데이트
  useEffect(() => {
    const token = TokenManager.getAccessToken();
    if (token) {
      httpClient.setAuthToken(token);
    } else {
      httpClient.clearAuthToken();
    }
  }, [user]);

  /**
   * 인증 상태 확인
   */
  const checkAuthStatus = async () => {
    try {
      setIsLoading(true);
      
      if (!TokenManager.isAuthenticated()) {
        setUser(null);
        return;
      }

      // 현재 사용자 정보 가져오기
      const userData = await authService.getCurrentUser();
      setUser(userData as AuthUser);
      
    } catch (error) {
      console.error('Auth check failed:', error);
      
      // 토큰이 유효하지 않으면 제거
      TokenManager.clearTokens();
      setUser(null);
      
      // 토큰 갱신 시도
      try {
        await authService.refreshToken();
        const userData = await authService.getCurrentUser();
        setUser(userData as AuthUser);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 로그인
   */
  const login = async (credentials: LoginCredentials): Promise<{ success: boolean; message: string }> => {
    try {
      setIsLoading(true);
      
      const response = await authService.login(credentials);
      
      if (response.success) {
        setUser(response.data.user as AuthUser);
        return { success: true, message: 'Login successful' };
      } else {
        return { success: false, message: response.message || 'Login failed' };
      }
    } catch (error: unknown) {
      console.error('Login error:', error);
      return { 
        success: false, 
        message: error && typeof error === 'object' && 'message' in error 
          ? String(error.message) 
          : 'Login failed. Please try again.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 회원가입
   */
  const register = async (data: RegisterData): Promise<{ success: boolean; message: string }> => {
    try {
      setIsLoading(true);
      
      const response = await authService.register(data);
      
      if (response.success) {
        setUser(response.data.user as AuthUser);
        return { success: true, message: 'Registration successful' };
      } else {
        return { success: false, message: response.message || 'Registration failed' };
      }
    } catch (error: unknown) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        message: error && typeof error === 'object' && 'message' in error 
          ? String(error.message) 
          : 'Registration failed. Please try again.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 로그아웃
   */
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      TokenManager.clearTokens();
      httpClient.clearAuthToken();
    }
  };

  /**
   * 인증 상태 갱신
   */
  const refreshAuth = async () => {
    await checkAuthStatus();
  };

  /**
   * 사용자 정보 업데이트
   */
  const updateUser = (userData: Partial<AuthUser>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshAuth,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * 인증 컨텍스트 훅
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * 인증이 필요한 컴포넌트를 위한 HOC
 */
export function withAuth<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
        </div>
      );
    }

    if (!isAuthenticated) {
      // 로그인 페이지로 리다이렉트하거나 로그인 컴포넌트 표시
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    return <Component {...props} />;
  };
}

export default AuthContext;
