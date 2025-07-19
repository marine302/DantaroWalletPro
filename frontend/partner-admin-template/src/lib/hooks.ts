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
    // const interval = setInterval(fetchStatus, 10000); // 임시 비활성화 (개발 중)
    // return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 사용자 목록 훅
export const useUsers = (page: number = 1, limit: number = 20, search?: string, status?: string) => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const result = await api.users.getUsers({ page, limit, search, status });
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [page, limit, search, status]);

  return { data, loading, error };
};

// 사용자 통계 훅
export const useUserStats = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        console.log('Fetching user stats...');
        const result = await api.users.getUserStats();
        console.log('User stats result:', result);
        setData(result);
      } catch (err) {
        console.error('Error fetching user stats:', err);
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    // const interval = setInterval(fetchStats, 30000); // 임시 비활성화 (개발 중)
    // return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 사용자 KYC 상태 업데이트 훅
export const useUpdateUserKYC = () => {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const updateKYC = async (userId: string, status: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.users.updateKYCStatus(userId, status);
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { updateKYC, loading, error };
};

// 사용자 상태 업데이트 훅
export const useUpdateUserStatus = () => {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const updateStatus = async (userId: string, status: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.users.updateUserStatus(userId, status);
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { updateStatus, loading, error };
};

// 에너지 풀 상태 훅 - 실제 API에 맞게 수정
export const useEnergyPoolStatus = (partnerId: number = 1) => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        // 실제 에너지 모니터링 API 호출 (에너지 풀 상태 대신)
        const result = await api.energy.getMonitoringData(partnerId);
        setData(result);
      } catch (err) {
        setError(err as Error);
        console.error('에너지 모니터링 데이터 로드 실패:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    // const interval = setInterval(fetchStatus, 30000); // 임시 비활성화 (개발 중)
    // return () => clearInterval(interval);
  }, [partnerId]);

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
    // const interval = setInterval(fetchData, 60000); // 임시 비활성화 (개발 중) // 1분마다 갱신
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 수익 분석 훅
export const useRevenueAnalytics = (period: string = '30d') => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.analytics.getRevenueAnalytics(period);
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [period]);

  return { data, loading, error };
};

// 거래 분석 훅
export const useTransactionAnalytics = (period: string = '7d') => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.analytics.getTransactionAnalytics(period);
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [period]);

  return { data, loading, error };
};

// 사용자 활동 분석 훅
export const useUserActivityAnalytics = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.analytics.getUserActivityAnalytics();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // const interval = setInterval(fetchData, 60000); // 임시 비활성화 (개발 중) // 1분마다 갱신
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 비용 분석 훅
export const useCostAnalytics = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.analytics.getCostAnalytics();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // const interval = setInterval(fetchData, 60000); // 임시 비활성화 (개발 중) // 1분마다 갱신
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
};

// 종합 분석 데이터 훅 (모든 분석 데이터를 통합)
export const useComprehensiveAnalytics = (period: string = '30d') => {
  const { data: dashboardData, loading: dashboardLoading, error: dashboardError } = useAnalyticsDashboard();
  const { data: revenueData, loading: revenueLoading, error: revenueError } = useRevenueAnalytics(period);
  const { data: transactionData, loading: transactionLoading, error: transactionError } = useTransactionAnalytics(period);
  const { data: userData, loading: userLoading, error: userError } = useUserActivityAnalytics();
  const { data: costData, loading: costLoading, error: costError } = useCostAnalytics();

  const loading = dashboardLoading || revenueLoading || transactionLoading || userLoading || costLoading;
  const error = dashboardError || revenueError || transactionError || userError || costError;

  return {
    data: {
      dashboard: dashboardData,
      revenue: revenueData,
      transactions: transactionData,
      users: userData,
      costs: costData
    },
    loading,
    error
  };
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

// 출금 요청 목록 훅
export const useWithdrawalRequests = (page = 1, limit = 20, status?: string) => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.withdrawal.getRequests(page, limit, status);
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [page, limit, status]);

  return { data, loading, error };
};

// 출금 정책 훅
export const useWithdrawalPolicy = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.withdrawal.getPolicy();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

// 배치 출금 훅
export const useWithdrawalBatches = () => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.withdrawal.getBatches();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

// 사용자 로그인 히스토리 조회
export const useUserLoginHistory = (userId: string, page: number = 1, limit: number = 20) => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchLoginHistory = async () => {
      try {
        setLoading(true);
        const result = await api.users.getUserLoginHistory(userId, { page, limit });
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchLoginHistory();
  }, [userId, page, limit]);

  return { data, loading, error };
};

// 에너지 풀 상세 데이터 훅
export const useEnergyPoolDetails = (partnerId: number = 1) => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const result = await api.energy.getPoolStatus(partnerId);
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
    // const interval = setInterval(fetchDetails, 30000); // 임시 비활성화 (개발 중) // 30초마다 갱신
    return () => clearInterval(interval);
  }, [partnerId]);

  return { data, loading, error };
};

// 에너지 거래 내역 훅
export const useEnergyTransactions = (partnerId: number = 1, page: number = 1, limit: number = 20) => {
  const [data, setData] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const result = await api.energy.getTransactions(partnerId, { page, limit });
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [partnerId, page, limit]);

  return { data, loading, error };
};

// 에너지 스테이킹 액션 훅
export const useEnergyStaking = () => {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const stakeForEnergy = async (partnerId: number, amount: number) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.energy.stakeForEnergy(partnerId, amount);
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const unstakeEnergy = async (partnerId: number, amount: number) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.energy.unstake(partnerId, amount);
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { stakeForEnergy, unstakeEnergy, loading, error };
};
