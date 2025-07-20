/**
 * API 훅들 - React Query 기반 구현 (중복 제거 완료)
 * 참고 문서: Doc-24~31 모든 API 연동
 */
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  tronlinkApi, 
  partnerApi, 
  energyApi,
  authApi
} from './api';

// 새로운 API 서비스 imports
import { UserService } from './services/user.service';
import { WithdrawalService } from './services/withdrawal.service';
import { EnergyService } from './services/energy.service';
import { AnalyticsService } from './services/analytics.service';
import { realtimeManager, RealtimeMessage, RealtimeHookOptions } from './realtime';
import { useState, useEffect, useCallback, useRef } from 'react';

// =============================================================================
// 인증 관련 훅들
// =============================================================================

export const useAuth = () => {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.me,
    retry: 1,
  });
};

// =============================================================================
// TronLink 연동 훅들 (Doc-24)
// =============================================================================

export const useTronLinkStatus = () => {
  return useQuery({
    queryKey: ['tronlink', 'status'],
    queryFn: tronlinkApi.getStatus,
    refetchInterval: 30000,
  });
};

export const useTronLinkWallets = () => {
  return useQuery({
    queryKey: ['tronlink', 'wallets'],
    queryFn: tronlinkApi.getWallets,
  });
};

export const useTronLinkBalance = (walletAddress: string) => {
  return useQuery({
    queryKey: ['tronlink', 'balance', walletAddress],
    queryFn: () => tronlinkApi.getBalance(walletAddress),
    enabled: !!walletAddress,
    refetchInterval: 30000,
  });
};

export const useConnectWallet = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ walletAddress, signature }: { walletAddress: string; signature: string }) =>
      tronlinkApi.connect(walletAddress, signature),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tronlink'] });
    },
  });
};

// =============================================================================
// 파트너 관리 훅들 (Doc-25)
// =============================================================================

export const usePartnerProfile = () => {
  return useQuery({
    queryKey: ['partner', 'profile'],
    queryFn: partnerApi.getProfile,
  });
};

export const usePartnerStats = () => {
  return useQuery({
    queryKey: ['partner', 'stats'],
    queryFn: partnerApi.getStats,
    refetchInterval: 60000,
  });
};

export const useUsers = (page = 1, limit = 20) => {
  return useQuery({
    queryKey: ['partner', 'users', { page, limit }],
    queryFn: () => partnerApi.getUsers(page, limit),
  });
};

export const useUserStats = () => {
  return useQuery({
    queryKey: ['partner', 'user-stats'],
    queryFn: partnerApi.getUserStats,
    refetchInterval: 300000,
  });
};

export const useUpdatePartnerSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: partnerApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partner'] });
    },
  });
};

// =============================================================================
// 에너지 관리 훅들 (Doc-26, Doc-31)
// =============================================================================

export const useEnergyMonitoring = (partnerId: number) => {
  return useQuery({
    queryKey: ['energy', 'monitoring', partnerId],
    queryFn: () => energyApi.getMonitoringData(partnerId),
    enabled: !!partnerId,
    refetchInterval: 10000,
  });
};

export const useEnergyDashboard = (partnerId: number) => {
  return useQuery({
    queryKey: ['energy', 'dashboard', partnerId],
    queryFn: () => energyApi.getDashboard(partnerId),
    enabled: !!partnerId,
    refetchInterval: 30000,
  });
};

export const useEnergyAnalytics = (partnerId: number) => {
  return useQuery({
    queryKey: ['energy', 'analytics', partnerId],
    queryFn: () => energyApi.getAnalytics(partnerId),
    enabled: !!partnerId,
  });
};

export const useEnergyPoolStatus = (partnerId: number) => {
  return useQuery({
    queryKey: ['energy', 'pool', partnerId],
    queryFn: () => energyApi.getPoolStatus(partnerId),
    enabled: !!partnerId,
    refetchInterval: 30000,
  });
};

export const useEnergyTransactions = (partnerId: number, page = 1, limit = 20) => {
  return useQuery({
    queryKey: ['energy', 'transactions', partnerId, { page, limit }],
    queryFn: () => energyApi.getTransactions(partnerId, { page, limit }),
    enabled: !!partnerId,
  });
};

export const useStakeForEnergy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ partnerId, amount }: { partnerId: number; amount: number }) =>
      energyApi.stakeForEnergy(partnerId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['energy'] });
    },
  });
};

// =============================================================================
// 사용자 관리 훅들 (확장)
// =============================================================================

export const useUsersAdvanced = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['users', 'advanced', params],
    queryFn: () => UserService.getUsers(params),
    keepPreviousData: true,
  });
};

export const useUser = (id: string) => {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => UserService.getUser(id),
    enabled: !!id,
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: UserService.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => 
      UserService.updateUser(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['users', id] });
    },
  });
};

// =============================================================================
// 출금 관리 훅들 (확장)
// =============================================================================

export const useWithdrawals = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['withdrawals', params],
    queryFn: () => WithdrawalService.getWithdrawals(params),
    keepPreviousData: true,
  });
};

export const useWithdrawal = (id: string) => {
  return useQuery({
    queryKey: ['withdrawals', id],
    queryFn: () => WithdrawalService.getWithdrawal(id),
    enabled: !!id,
  });
};

export const useApproveWithdrawal = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, adminNotes }: { id: string; adminNotes?: string }) =>
      WithdrawalService.approveWithdrawal(id, adminNotes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawals'] });
    },
  });
};

export const useRejectWithdrawal = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, reason, adminNotes }: { id: string; reason: string; adminNotes?: string }) =>
      WithdrawalService.rejectWithdrawal(id, reason, adminNotes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawals'] });
    },
  });
};

export const useWithdrawalStats = () => {
  return useQuery({
    queryKey: ['withdrawals', 'stats'],
    queryFn: WithdrawalService.getWithdrawalStats,
    refetchInterval: 30000,
  });
};

// =============================================================================
// 에너지 관리 훅들 (확장)
// =============================================================================

export const useEnergyPools = () => {
  return useQuery({
    queryKey: ['energy', 'pools'],
    queryFn: EnergyService.getEnergyPools,
    refetchInterval: 30000,
  });
};

export const useEnergyPoolsAdvanced = () => {
  return useQuery({
    queryKey: ['energy', 'pools', 'advanced'],
    queryFn: EnergyService.getEnergyPools,
    refetchInterval: 30000,
  });
};

export const useEnergyTransactionsAdvanced = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['energy', 'transactions', 'advanced', params],
    queryFn: () => EnergyService.getEnergyTransactions(params),
    keepPreviousData: true,
  });
};

export const useEnergyStats = () => {
  return useQuery({
    queryKey: ['energy', 'stats'],
    queryFn: EnergyService.getEnergyStats,
    refetchInterval: 60000,
  });
};

export const useRealTimeEnergyData = () => {
  return useQuery({
    queryKey: ['energy', 'realtime'],
    queryFn: EnergyService.getRealTimeEnergyData,
    refetchInterval: 5000,
  });
};

export const useCreateEnergyPool = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: EnergyService.createEnergyPool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['energy', 'pools'] });
    },
  });
};

// =============================================================================
// 분석 및 대시보드 훅들
// =============================================================================

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: AnalyticsService.getDashboardStats,
    refetchInterval: 30000,
  });
};

export const useUserAnalytics = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['analytics', 'users', params],
    queryFn: () => AnalyticsService.getUserAnalytics(params),
    keepPreviousData: true,
  });
};

export const useTransactionAnalytics = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['analytics', 'transactions', params],
    queryFn: () => AnalyticsService.getTransactionAnalytics(params),
    keepPreviousData: true,
  });
};

export const useRevenueAnalytics = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['analytics', 'revenue', params],
    queryFn: () => AnalyticsService.getRevenueAnalytics(params),
    keepPreviousData: true,
  });
};

export const usePerformanceAnalytics = (params: Record<string, unknown> = {}) => {
  return useQuery({
    queryKey: ['analytics', 'performance', params],
    queryFn: () => AnalyticsService.getPerformanceAnalytics(params),
    keepPreviousData: true,
  });
};

// =============================================================================
// 실시간 데이터 훅들
// =============================================================================

export function useRealtime<T>(options: RealtimeHookOptions) {
  const [data, setData] = useState<T | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const subscriptionRef = useRef<string | null>(null);

  const handleMessage = useCallback((message: RealtimeMessage<T>) => {
    setData(message.payload);
  }, []);

  useEffect(() => {
    const setupConnection = async () => {
      try {
        if (options.useSSE) {
          await realtimeManager.sse.connect(
            options.sseEndpoint || '/api/events',
            [options.channel]
          );
          subscriptionRef.current = realtimeManager.sse.subscribe(options.channel, handleMessage);
          setConnected(true);
        } else {
          if (options.autoConnect !== false) {
            await realtimeManager.ws.connect();
          }
          subscriptionRef.current = realtimeManager.ws.subscribe(options.channel, handleMessage);
          setConnected(realtimeManager.ws.isConnected);
        }
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Connection failed');
        setConnected(false);
      }
    };

    setupConnection();

    return () => {
      if (subscriptionRef.current) {
        if (options.useSSE) {
          realtimeManager.sse.unsubscribe(subscriptionRef.current);
        } else {
          realtimeManager.ws.unsubscribe(subscriptionRef.current);
        }
      }
    };
  }, [options.channel, options.autoConnect, options.useSSE, options.sseEndpoint, handleMessage]);

  const reconnect = useCallback(async () => {
    try {
      if (!options.useSSE) {
        await realtimeManager.ws.connect();
        setConnected(realtimeManager.ws.isConnected);
        setError(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reconnection failed');
    }
  }, [options.useSSE]);

  const send = useCallback((message: Record<string, unknown>) => {
    if (!options.useSSE && realtimeManager.ws.isConnected) {
      realtimeManager.ws.send(message);
    }
  }, [options.useSSE]);

  return {
    data,
    connected,
    error,
    reconnect,
    send
  };
}

// =============================================================================
// 유틸리티 훅들
// =============================================================================

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      if (typeof window !== 'undefined') {
        const item = window.localStorage.getItem(key);
        return item ? JSON.parse(item) : initialValue;
      }
      return initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue] as const;
}

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
