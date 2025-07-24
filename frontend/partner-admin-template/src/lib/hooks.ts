// 실제 hooks.ts - 사용자 관리 기능 구현
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService, type UserFilters, type CreateUserRequest, type UpdateUserRequest } from './services/user.service';

// 사용자 관리 훅들
export const useUsers = (page: number = 1, limit: number = 20, filters: UserFilters = {}) => {
  return useQuery({
    queryKey: ['users', page, limit, filters],
    queryFn: () => userService.getUsers(page, limit, filters),
    staleTime: 5 * 60 * 1000, // 5분
  });
};

export const useUserStats = () => {
  return useQuery({
    queryKey: ['userStats'],
    queryFn: () => userService.getUserStats(),
    staleTime: 2 * 60 * 1000, // 2분
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (userData: CreateUserRequest) => userService.createUser(userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['userStats'] });
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: UpdateUserRequest }) => 
      userService.updateUser(userId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['userStats'] });
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (userId: string) => userService.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['userStats'] });
    },
  });
};

export const useBulkUpdateUsers = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userIds, updates }: { userIds: string[]; updates: Partial<UpdateUserRequest> }) => 
      userService.bulkUpdateUsers(userIds, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['userStats'] });
    },
  });
};

export const useExportUsers = () => {
  return useMutation({
    mutationFn: (filters: UserFilters = {}) => userService.exportUsers(filters),
  });
};

// 기존 임시 스텁들 (다른 페이지에서 사용)
export const useWithdrawals = () => {
  return { data: [], isLoading: false, error: null, isError: false };
};

export const useWithdrawalStats = () => {
  return { data: null, isLoading: false, error: null, isError: false };
};

export const useDashboardStats = () => {
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
