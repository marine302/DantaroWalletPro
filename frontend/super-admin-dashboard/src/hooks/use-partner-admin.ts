import { useState, useEffect, useCallback } from 'react';
import { partnerAdminService, User, UserStats, WithdrawalRequest, WithdrawalStats, EnergyPool, EnergyStats, EnergyTransaction, PartnerProfile, AnalyticsData } from '@/services/partner-admin-service';

// 공통 API 상태 타입
interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// 사용자 관리 훅
export function useUsers(page: number = 1, limit: number = 20, filters?: {
  status?: string;
  kycStatus?: string;
  tier?: string;
  search?: string;
}) {
  const [state, setState] = useState<ApiState<{ users: User[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getUsers(page, limit, filters);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch users' });
    }
  }, [page, limit, filters]);

  const updateUserStatus = useCallback(async (userId: string, status: User['status']) => {
    try {
      await partnerAdminService.updateUserStatus(userId, status);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to update user status:', error);
      return false;
    }
  }, [fetchData]);

  const updateUserTier = useCallback(async (userId: string, tier: User['tier']) => {
    try {
      await partnerAdminService.updateUserTier(userId, tier);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to update user tier:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, updateUserStatus, updateUserTier };
}

export function useUserStats() {
  const [state, setState] = useState<ApiState<UserStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getUserStats();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch user stats' });
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export function useUserDetails(userId: string) {
  const [state, setState] = useState<ApiState<User>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    if (!userId) return;
    
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getUserDetails(userId);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch user details' });
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

// 출금 관리 훅
export function useWithdrawalRequests(page: number = 1, limit: number = 20, filters?: {
  status?: string;
  currency?: string;
  dateFrom?: string;
  dateTo?: string;
}) {
  const [state, setState] = useState<ApiState<{ requests: WithdrawalRequest[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getWithdrawalRequests(page, limit, filters);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch withdrawal requests' });
    }
  }, [page, limit, filters]);

  const approveWithdrawal = useCallback(async (requestId: string) => {
    try {
      await partnerAdminService.approveWithdrawal(requestId);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to approve withdrawal:', error);
      return false;
    }
  }, [fetchData]);

  const rejectWithdrawal = useCallback(async (requestId: string, reason: string) => {
    try {
      await partnerAdminService.rejectWithdrawal(requestId, reason);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to reject withdrawal:', error);
      return false;
    }
  }, [fetchData]);

  const processBatchWithdrawal = useCallback(async (requestIds: string[]) => {
    try {
      await partnerAdminService.processBatchWithdrawal(requestIds);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to process batch withdrawal:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    ...state, 
    refetch: fetchData, 
    approveWithdrawal, 
    rejectWithdrawal, 
    processBatchWithdrawal 
  };
}

export function useWithdrawalStats() {
  const [state, setState] = useState<ApiState<WithdrawalStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getWithdrawalStats();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch withdrawal stats' });
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

// 에너지 관리 훅
export function useEnergyPools(page: number = 1, limit: number = 20) {
  const [state, setState] = useState<ApiState<{ pools: EnergyPool[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getEnergyPools(page, limit);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch energy pools' });
    }
  }, [page, limit]);

  const createPool = useCallback(async (pool: {
    name: string;
    totalCapacity: number;
    pricePerUnit: number;
  }) => {
    try {
      await partnerAdminService.createEnergyPool(pool);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to create energy pool:', error);
      return false;
    }
  }, [fetchData]);

  const updatePool = useCallback(async (poolId: string, updates: Partial<EnergyPool>) => {
    try {
      await partnerAdminService.updateEnergyPool(poolId, updates);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to update energy pool:', error);
      return false;
    }
  }, [fetchData]);

  const deletePool = useCallback(async (poolId: string) => {
    try {
      await partnerAdminService.deleteEnergyPool(poolId);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to delete energy pool:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    ...state, 
    refetch: fetchData, 
    createPool, 
    updatePool, 
    deletePool 
  };
}

export function useEnergyStats() {
  const [state, setState] = useState<ApiState<EnergyStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getEnergyStats();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch energy stats' });
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export function useEnergyTransactions(page: number = 1, limit: number = 20, filters?: {
  type?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
}) {
  const [state, setState] = useState<ApiState<{ transactions: EnergyTransaction[]; total: number }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getEnergyTransactions(page, limit, filters);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch energy transactions' });
    }
  }, [page, limit, filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

// 분석 및 프로필 훅
export function useAnalyticsData(period: 'day' | 'week' | 'month' | 'year') {
  const [state, setState] = useState<ApiState<AnalyticsData[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getAnalyticsData(period);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch analytics data' });
    }
  }, [period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export function usePartnerProfile() {
  const [state, setState] = useState<ApiState<PartnerProfile>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getPartnerProfile();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch partner profile' });
    }
  }, []);

  const updateProfile = useCallback(async (updates: Partial<PartnerProfile>) => {
    try {
      await partnerAdminService.updatePartnerProfile(updates);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to update partner profile:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, updateProfile };
}

// 알림 및 설정 훅
export function useNotifications(page: number = 1, limit: number = 20) {
  const [state, setState] = useState<ApiState<{
    notifications: Array<{
      id: string;
      title: string;
      message: string;
      type: 'info' | 'warning' | 'error' | 'success';
      isRead: boolean;
      createdAt: string;
    }>;
    total: number;
  }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getNotifications(page, limit);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch notifications' });
    }
  }, [page, limit]);

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await partnerAdminService.markNotificationAsRead(notificationId);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, markAsRead };
}

export function useSettings() {
  const [state, setState] = useState<ApiState<{
    autoApprovalEnabled: boolean;
    maxWithdrawalAmount: number;
    notificationPreferences: {
      email: boolean;
      sms: boolean;
      push: boolean;
    };
  }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const data = await partnerAdminService.getSettings();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error instanceof Error ? error.message : 'Failed to fetch settings' });
    }
  }, []);

  const updateSettings = useCallback(async (settings: {
    autoApprovalEnabled?: boolean;
    maxWithdrawalAmount?: number;
    notificationPreferences?: {
      email?: boolean;
      sms?: boolean;
      push?: boolean;
    };
  }) => {
    try {
      await partnerAdminService.updateSettings(settings);
      await fetchData(); // 데이터 새로고침
      return true;
    } catch (error) {
      console.error('Failed to update settings:', error);
      return false;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData, updateSettings };
}
