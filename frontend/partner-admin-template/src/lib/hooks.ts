/**
 * API 훅들 - 임시 구현 (React Query 설치 전)
 * TODO: @tanstack/react-query 설치 후 실제 구현으로 교체
 */
'use client';

import React from 'react';
import api from './api';

// =============================================================================
// 기본 훅들 - 실제 API 호출
// =============================================================================

// TronLink 상태 훅
export const useTronLinkStatus = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const result = await api.tronlink.getStatus();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // 10초마다 갱신
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 에너지 풀 상태 훅
export const useEnergyPoolStatus = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const result = await api.energy.getPoolStatus();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // 5초마다 갱신
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 파트너 프로필 훅
export const usePartnerProfile = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const result = await api.partner.getProfile();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  return { data, loading, error };
};

// 분석 대시보드 데이터 훅
export const useAnalyticsDashboard = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.analytics.getDashboardData();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // 1분마다 갱신
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// WebSocket 연결 훅
export const useWebSocket = () => {
  React.useEffect(() => {
    api.ws.connect();
    
    return () => {
      api.ws.disconnect();
    };
  }, []);

  const subscribe = React.useCallback((eventType: string, callback: (data: unknown) => void) => {
    api.ws.on(eventType, callback);
    
    return () => {
      api.ws.off(eventType, callback);
    };
  }, []);

  return { subscribe };
};

// =============================================================================
// 유틸리티 훅들
// =============================================================================

// API 인증 훅
export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);

  React.useEffect(() => {
    const token = api.utils.restoreAuthToken();
    setIsAuthenticated(!!token);
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    try {
      const result = await api.auth.login(email, password) as { token?: string };
      if (result.token) {
        api.utils.setAuthToken(result.token);
        setIsAuthenticated(true);
      }
      return result;
    } catch (error) {
      setIsAuthenticated(false);
      throw error;
    }
  }, []);

  const logout = React.useCallback(async () => {
    try {
      await api.auth.logout();
    } finally {
      api.utils.removeAuthToken();
      setIsAuthenticated(false);
    }
  }, []);

  return { isAuthenticated, login, logout };
};

// 에러 처리 훅
export const useApiError = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const handleApiCall = React.useCallback(async <T,>(apiCall: () => Promise<T>): Promise<T | null> => {
    try {
      setError(null);
      return await apiCall();
    } catch (err) {
      setError(err as Error);
      console.error('API Error:', err);
      return null;
    }
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  return { error, handleApiCall, clearError };
};
