/**
 * API 훅들 - React Query 기반 실제 구현
 * 참고 문서: Doc-24~31 모든 API 연동
 */
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  tronlinkApi, 
  partnerApi, 
  energyApi, 
  withdrawalApi, 
  onboardingApi, 
  auditApi,
  authApi,
  energyRentalApi 
} from './api';

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
    refetchInterval: 30000, // 30초마다 상태 확인
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
    refetchInterval: 60000, // 1분마다 갱신
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
    refetchInterval: 300000, // 5분마다 갱신
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
    refetchInterval: 10000, // 10초마다 실시간 모니터링
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
// 에너지 렌탈 서비스 훅들 (Doc-31)
// =============================================================================

export const useEnergyRentalOverview = () => {
  return useQuery({
    queryKey: ['energy', 'rental', 'overview'],
    queryFn: energyRentalApi.getOverview,
    refetchInterval: 60000, // 1분마다 업데이트
  });
};

export const useEnergyRentalPools = () => {
  return useQuery({
    queryKey: ['energy', 'rental', 'pools'],
    queryFn: energyRentalApi.getPools,
    refetchInterval: 30000, // 30초마다 업데이트
  });
};

export const useEnergyRentalTransactions = (page = 1, limit = 20) => {
  return useQuery({
    queryKey: ['energy', 'rental', 'transactions', { page, limit }],
    queryFn: () => energyRentalApi.getTransactions(page, limit),
  });
};

export const useCreateEnergyPool = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ name, stake_amount, rental_rate }: { 
      name: string; 
      stake_amount: number; 
      rental_rate: number 
    }) => energyRentalApi.createPool({ name, stake_amount, rental_rate }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['energy', 'rental'] });
    },
  });
};

export const useUpdateEnergyPool = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ poolId, updates }: { poolId: string; updates: Record<string, unknown> }) =>
      energyRentalApi.updatePool(poolId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['energy', 'rental'] });
    },
  });
};

export const useDeleteEnergyPool = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (poolId: string) => energyRentalApi.deletePool(poolId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['energy', 'rental'] });
    },
  });
};

export const useEnergyRentalAnalytics = (period = '30d') => {
  return useQuery({
    queryKey: ['energy', 'rental', 'analytics', period],
    queryFn: () => energyRentalApi.getAnalytics(period),
  });
};

// =============================================================================
// 출금 관리 훅들 (Doc-28)
// =============================================================================

export const useWithdrawalRequests = (page = 1, limit = 20, status?: string) => {
  return useQuery({
    queryKey: ['withdrawal', 'requests', { page, limit, status }],
    queryFn: () => withdrawalApi.getRequests(page, limit, status),
  });
};

// 출금 정책 관리 훅들 (Doc-28 고급 기능)
export const useWithdrawalPolicies = () => {
  return useQuery({
    queryKey: ['withdrawal', 'policies'],
    queryFn: withdrawalApi.getPolicies,
  });
};

export const useWithdrawalPolicy = () => {
  return useQuery({
    queryKey: ['withdrawal', 'policy'],
    queryFn: withdrawalApi.getPolicy,
  });
};

export const useUpdateWithdrawalPolicy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ policyId, updates }: { policyId: string; updates: Record<string, unknown> }) =>
      withdrawalApi.updatePolicy(policyId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawal', 'policies'] });
      queryClient.invalidateQueries({ queryKey: ['withdrawal', 'policy'] });
    },
  });
};

export const useCreateWithdrawalPolicy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (policyData: Record<string, unknown>) =>
      withdrawalApi.createPolicy(policyData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawal', 'policies'] });
    },
  });
};

export const useDeleteWithdrawalPolicy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (policyId: string) => withdrawalApi.deletePolicy(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawal', 'policies'] });
    },
  });
};

// =============================================================================
// 온보딩 자동화 훅들 (Doc-29)
// =============================================================================

export const useOnboardingProgress = () => {
  return useQuery({
    queryKey: ['onboarding', 'progress'],
    queryFn: onboardingApi.getProgress,
    refetchInterval: 60000, // 1분마다 진행률 업데이트
  });
};

export const useOnboardingSteps = () => {
  return useQuery({
    queryKey: ['onboarding', 'steps'],
    queryFn: onboardingApi.getSteps,
  });
};

export const useOnboardingChecklist = () => {
  return useQuery({
    queryKey: ['onboarding', 'checklist'],
    queryFn: onboardingApi.getChecklist,
  });
};

export const useCompleteOnboardingStep = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ stepId, data }: { stepId: string; data?: Record<string, unknown> }) =>
      onboardingApi.completeStep(stepId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding'] });
    },
  });
};

// =============================================================================
// 감사 및 컴플라이언스 훅들 (Doc-30)
// =============================================================================

export const useAuditLogs = (options: {
  search?: string;
  period?: string;
  risk_level?: string;
  page?: number;
  limit?: number;
} = {}) => {
  return useQuery({
    queryKey: ['audit', 'logs', options],
    queryFn: () => auditApi.getLogs(options),
    refetchInterval: 30000, // 30초마다 업데이트
  });
};

export const useComplianceReports = () => {
  return useQuery({
    queryKey: ['audit', 'compliance', 'reports'],
    queryFn: auditApi.getComplianceReports,
  });
};

export const useSecurityEvents = (options: {
  event_type?: string;
  severity?: string;
  status?: string;
} = {}) => {
  return useQuery({
    queryKey: ['audit', 'security', 'events', options],
    queryFn: () => auditApi.getSecurityEvents(options),
    refetchInterval: 15000, // 15초마다 업데이트
  });
};

export const useGenerateComplianceReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ type, period }: { type: string; period: string }) =>
      auditApi.generateReport(type, period),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'compliance'] });
    },
  });
};

export const useUpdateSecurityEvent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ eventId, updates }: { eventId: string; updates: Record<string, unknown> }) =>
      auditApi.updateSecurityEvent(eventId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'security'] });
    },
  });
};

// =============================================================================
// 종합 분석 훅들 (복합 데이터)
// =============================================================================

export const useComprehensiveAnalytics = (partnerId: number) => {
  const energyAnalytics = useEnergyAnalytics(partnerId);
  const partnerStats = usePartnerStats();
  const withdrawalRequests = useWithdrawalRequests(1, 10);
  
  return {
    energy: energyAnalytics,
    partner: partnerStats,
    withdrawals: withdrawalRequests,
    isLoading: energyAnalytics.isLoading || partnerStats.isLoading || withdrawalRequests.isLoading,
    isError: energyAnalytics.isError || partnerStats.isError || withdrawalRequests.isError,
  };
};

// =============================================================================
// 대시보드 메인 데이터 훅
// =============================================================================

export const useDashboardData = (partnerId: number) => {
  const tronlinkStatus = useTronLinkStatus();
  const partnerStats = usePartnerStats();
  const energyDashboard = useEnergyDashboard(partnerId);
  const recentWithdrawals = useWithdrawalRequests(1, 5);
  
  return {
    tronlink: tronlinkStatus,
    stats: partnerStats,
    energy: energyDashboard,
    withdrawals: recentWithdrawals,
    isLoading: tronlinkStatus.isLoading || partnerStats.isLoading || energyDashboard.isLoading,
    isError: tronlinkStatus.isError || partnerStats.isError || energyDashboard.isError,
  };
};
