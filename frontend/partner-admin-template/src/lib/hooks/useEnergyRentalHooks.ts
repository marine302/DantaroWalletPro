/**
 * 에너지 렌탈 관련 React 훅
 * 실제 백엔드 연결을 위한 구조
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { energyRentalApi } from '../services/energy-rental-api';
import { ENERGY_RENTAL_CONFIG } from '../config';
import type { 
  EnergyUsageStats
} from '../../types';

// 파트너 ID (현재 로그인한 파트너의 ID)
const getCurrentPartnerId = (): string => {
  // TODO: 실제로는 인증 컨텍스트에서 가져와야 함
  if (typeof window !== 'undefined') {
    return localStorage.getItem('partner_id') || 'partner_001';
  }
  return 'partner_001';
};

// 에너지 렌탈 플랜 조회 훅
export function useEnergyRentalPlans() {
  return useQuery({
    queryKey: ['energy-rental-plans'],
    queryFn: () => energyRentalApi.getAvailablePlans(),
    staleTime: 5 * 60 * 1000, // 5분
    retry: 2,
  });
}

// 파트너 에너지 사용 통계 훅
export function usePartnerUsageStats(period: string = '30d') {
  const partnerId = getCurrentPartnerId();
  
  return useQuery({
    queryKey: ['partner-usage-stats', partnerId, period],
    queryFn: () => energyRentalApi.getPartnerUsageStats(partnerId, period),
    refetchInterval: ENERGY_RENTAL_CONFIG.POLL_INTERVALS.USAGE_STATS,
    retry: 2,
  });
}

// 파트너 청구 이력 훅
export function usePartnerBilling() {
  const partnerId = getCurrentPartnerId();
  
  return useQuery({
    queryKey: ['partner-billing', partnerId],
    queryFn: () => energyRentalApi.getPartnerBilling(partnerId),
    staleTime: 2 * 60 * 1000, // 2분
    retry: 2,
  });
}

// 파트너 현재 할당 정보 훅
export function usePartnerAllocation() {
  const partnerId = getCurrentPartnerId();
  
  return useQuery({
    queryKey: ['partner-allocation', partnerId],
    queryFn: () => energyRentalApi.getPartnerAllocation(partnerId),
    staleTime: 30 * 1000, // 30초
    retry: 2,
  });
}

// 에너지 풀 상태 훅
export function useEnergyPoolsStatus() {
  return useQuery({
    queryKey: ['energy-pools-status'],
    queryFn: () => energyRentalApi.getPoolsStatus(),
    refetchInterval: ENERGY_RENTAL_CONFIG.POLL_INTERVALS.SYSTEM_STATUS,
    retry: 2,
  });
}

// 시스템 상태 훅
export function useSystemStatus() {
  return useQuery({
    queryKey: ['energy-system-status'],
    queryFn: () => energyRentalApi.getSystemStatus(),
    refetchInterval: ENERGY_RENTAL_CONFIG.POLL_INTERVALS.SYSTEM_STATUS,
    retry: 1,
  });
}

// 에너지 사용량 예측 훅
export function useUsagePrediction(forecastDays: number = 7) {
  const partnerId = getCurrentPartnerId();
  
  return useQuery({
    queryKey: ['usage-prediction', partnerId, forecastDays],
    queryFn: () => energyRentalApi.predictUsage(partnerId, forecastDays),
    staleTime: 10 * 60 * 1000, // 10분
    enabled: !!partnerId,
    retry: 2,
  });
}

// 에너지 렌탈 뮤테이션 훅
export function useRentEnergy() {
  const queryClient = useQueryClient();
  const partnerId = getCurrentPartnerId();
  
  return useMutation({
    mutationFn: (request: {
      plan_id: string;
      duration_hours: number;
      energy_amount: number;
    }) => energyRentalApi.rentEnergy({
      partner_id: partnerId,
      ...request
    }),
    onSuccess: () => {
      // 관련 쿼리 무효화
      queryClient.invalidateQueries({ queryKey: ['partner-allocation'] });
      queryClient.invalidateQueries({ queryKey: ['partner-usage-stats'] });
      queryClient.invalidateQueries({ queryKey: ['partner-billing'] });
      queryClient.invalidateQueries({ queryKey: ['energy-pools-status'] });
    },
  });
}

// 렌탈 연장 뮤테이션 훅
export function useExtendRental() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ rentalId, additionalHours }: {
      rentalId: string;
      additionalHours: number;
    }) => energyRentalApi.extendRental(rentalId, additionalHours),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partner-allocation'] });
      queryClient.invalidateQueries({ queryKey: ['partner-billing'] });
    },
  });
}

// 렌탈 취소 뮤테이션 훅
export function useCancelRental() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (rentalId: string) => energyRentalApi.cancelRental(rentalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partner-allocation'] });
      queryClient.invalidateQueries({ queryKey: ['partner-billing'] });
      queryClient.invalidateQueries({ queryKey: ['energy-pools-status'] });
    },
  });
}

// 실시간 에너지 모니터링 훅
export function useRealTimeEnergyMonitoring() {
  const [usage, setUsage] = useState<EnergyUsageStats | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const partnerId = getCurrentPartnerId();

  const startMonitoring = useCallback(async () => {
    if (isMonitoring || !partnerId) return;

    setIsMonitoring(true);
    try {
      const cleanup = await energyRentalApi.startEnergyMonitoring(partnerId, (newUsage) => {
        setUsage(newUsage);
      });
      cleanupRef.current = cleanup;
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      setIsMonitoring(false);
    }
  }, [isMonitoring, partnerId]);

  const stopMonitoring = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    setIsMonitoring(false);
  }, []);

  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, [stopMonitoring]);

  return {
    usage,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
  };
}

// 에너지 렌탈 종합 상태 훅 (대시보드용)
export function useEnergyRentalOverview() {
  const plansQuery = useEnergyRentalPlans();
  const usageQuery = usePartnerUsageStats();
  const allocationQuery = usePartnerAllocation();
  const poolsQuery = useEnergyPoolsStatus();
  const systemQuery = useSystemStatus();

  const isLoading = plansQuery.isLoading || 
                   usageQuery.isLoading || 
                   allocationQuery.isLoading || 
                   poolsQuery.isLoading || 
                   systemQuery.isLoading;

  const hasError = plansQuery.isError || 
                   usageQuery.isError || 
                   allocationQuery.isError || 
                   poolsQuery.isError || 
                   systemQuery.isError;

  return {
    plans: plansQuery.data || [],
    usage: usageQuery.data,
    allocation: allocationQuery.data,
    pools: poolsQuery.data,
    system: systemQuery.data,
    isLoading,
    hasError,
    refetch: () => {
      plansQuery.refetch();
      usageQuery.refetch();
      allocationQuery.refetch();
      poolsQuery.refetch();
      systemQuery.refetch();
    }
  };
}

// 백엔드 연결 상태 훅
export function useBackendConnection() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        await energyRentalApi.getSystemStatus();
        setIsConnected(true);
      } catch (error) {
        console.error('Failed to check connection:', error);
        setIsConnected(false);
      }
    };

    checkConnection();
    
    // 주기적으로 연결 상태 확인
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return { isConnected };
}
