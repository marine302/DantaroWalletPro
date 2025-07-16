import { useState, useEffect, useCallback } from 'react';
import { superAdminService, AuditLog, ComplianceStats, SuspiciousActivity, EnergyProvider, MarketStats, EnergyPurchase, Partner, OnboardingStats } from '@/services/super-admin-service';

// 공통 API 상태 타입
interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// 감사 및 컴플라이언스 훅
export function useAuditLogs(page: number = 1, limit: number = 20) {
  const [state, setState] = useState<ApiState<{ logs: AuditLog[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getAuditLogs(page, limit);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch audit logs' });
    }
  }, [page, limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export function useComplianceStats() {
  const [state, setState] = useState<ApiState<ComplianceStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getComplianceStats();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch compliance stats' });
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export function useSuspiciousActivities() {
  const [state, setState] = useState<ApiState<SuspiciousActivity[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getSuspiciousActivities();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch suspicious activities' });
    }
  }, []);

  const updateActivityStatus = useCallback(async (id: string, status: SuspiciousActivity['status']) => {
    try {
      await superAdminService.updateSuspiciousActivityStatus(id, status);
      await fetchData(); // 데이터 새로고침
    } catch (error) {
      console.error('Failed to update activity status:', error);
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, updateActivityStatus };
}

// 외부 에너지 시장 훅
export function useEnergyProviders() {
  const [state, setState] = useState<ApiState<EnergyProvider[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getEnergyProviders();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch energy providers' });
    }
  }, []);

  const updateProviderStatus = useCallback(async (providerId: number, isActive: boolean) => {
    try {
      await superAdminService.updateProviderStatus(providerId, isActive);
      await fetchData(); // 데이터 새로고침
    } catch (error) {
      console.error('Failed to update provider status:', error);
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, updateProviderStatus };
}

export function useMarketStats() {
  const [state, setState] = useState<ApiState<MarketStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getMarketStats();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch market stats' });
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export function useEnergyPurchases() {
  const [state, setState] = useState<ApiState<{ purchases: EnergyPurchase[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getEnergyPurchases();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch energy purchases' });
    }
  }, []);

  const createPurchase = useCallback(async (purchase: { providerId: number; energyAmount: number; margin: number; }) => {
    try {
      await superAdminService.createEnergyPurchase(purchase);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to create energy purchase:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, createPurchase };
}

// 파트너 온보딩 훅
export function usePartners(page: number = 1, limit: number = 20) {
  const [state, setState] = useState<ApiState<{ partners: Partner[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getPartners(page, limit);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch partners' });
    }
  }, [page, limit]);

  const approvePartner = useCallback(async (partnerId: number) => {
    try {
      await superAdminService.approvePartner(partnerId);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to approve partner:', error);
      return false;
    }
  }, [fetchData]);

  const rejectPartner = useCallback(async (partnerId: number, reason: string) => {
    try {
      await superAdminService.rejectPartner(partnerId, reason);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to reject partner:', error);
      return false;
    }
  }, [fetchData]);

  const advancePartnerStage = useCallback(async (partnerId: number) => {
    try {
      await superAdminService.advancePartnerStage(partnerId);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to advance partner stage:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    ...state, 
    refetch: fetchData, 
    approvePartner, 
    rejectPartner, 
    advancePartnerStage 
  };
}

export function useOnboardingStats() {
  const [state, setState] = useState<ApiState<OnboardingStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await superAdminService.getOnboardingStats();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch onboarding stats' });
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

// 실시간 업데이트를 위한 폴링 훅
export function usePolling(callback: () => void, interval: number = 30000) {
  useEffect(() => {
    const timer = setInterval(callback, interval);
    return () => clearInterval(timer);
  }, [callback, interval]);
}

// 에러 토스트 알림을 위한 훅 (실제 토스트 라이브러리와 연동 시 사용)
export function useErrorToast() {
  return useCallback((error: string) => {
    console.error('Error:', error);
    // 실제 토스트 라이브러리 호출
    // toast.error(error);
  }, []);
}
