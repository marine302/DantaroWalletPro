// 임시 hooks.ts - 빌드를 위한 최소한의 스텁

export const useUsers = (page?: number, limit?: number) => {
  return { data: [], isLoading: false, error: null, isError: false };
};

export const useUserStats = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useWithdrawals = () => {
  return { data: [], isLoading: false, error: null, isError: false };
};

export const useWithdrawalStats = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useDashboardStats = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useEnergyTransactions = () => {
  return { data: [], isLoading: false, error: null, isError: false };
};

export const useEnergyPools = () => {
  return { data: [], isLoading: false, error: null, isError: false };
};

export const useEnergyPoolStatus = (partnerId?: number) => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useAnalyticsOverview = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useUserAnalytics = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useTransactionAnalytics = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useRevenueAnalytics = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useSystemAnalytics = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};
