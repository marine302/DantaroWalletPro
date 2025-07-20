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
  authApi 
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
// 출금 관리 훅들 (Doc-28)
// =============================================================================

export const useWithdrawalRequests = (page = 1, limit = 20, status?: string) => {
  return useQuery({
    queryKey: ['withdrawal', 'requests', { page, limit, status }],
    queryFn: () => withdrawalApi.getRequests(page, limit, status),
  });
};

export const useWithdrawalPolicy = () => {
  return useQuery({
    queryKey: ['withdrawal', 'policy'],
    queryFn: withdrawalApi.getPolicy,
  });
};

export const useWithdrawalBatches = () => {
  return useQuery({
    queryKey: ['withdrawal', 'batches'],
    queryFn: withdrawalApi.getBatches,
  });
};

export const useCreateWithdrawalRequest = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: withdrawalApi.createRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawal', 'requests'] });
    },
  });
};

export const useUpdateWithdrawalPolicy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: withdrawalApi.updatePolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withdrawal', 'policy'] });
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

export const useAuditLogs = (page = 1, limit = 50, filters?: Record<string, unknown>) => {
  return useQuery({
    queryKey: ['audit', 'logs', { page, limit, filters }],
    queryFn: () => auditApi.getLogs(page, limit, filters),
  });
};

export const useSuspiciousTransactions = () => {
  return useQuery({
    queryKey: ['audit', 'suspicious-transactions'],
    queryFn: auditApi.getSuspiciousTransactions,
    refetchInterval: 60000, // 1분마다 확인
  });
};

export const useComplianceStatus = () => {
  return useQuery({
    queryKey: ['audit', 'compliance-status'],
    queryFn: auditApi.getComplianceStatus,
    refetchInterval: 300000, // 5분마다 확인
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
