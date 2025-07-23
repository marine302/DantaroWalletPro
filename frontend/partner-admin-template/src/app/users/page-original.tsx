'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { PageHeader } from '@/components/common/PageHeader'
import { UserStats } from '@/components/common/StatsCards'
import { UserManagementSection } from '@/components/users/UserFilters'
import { Button } from '@/components/ui/button'
import { Plus, RefreshCw } from 'lucide-react'
import { useUsers, useUserStats, useBulkUpdateUsers, useExportUsers, useCreateUser } from '@/lib/hooks'
import { withAuth } from '@/contexts/AuthContext'
import type { User as BaseUser } from '@/types'
import type { UserFilters } from '@/types/user'

// 확장된 사용자 인터페이스 (추가 필드 포함) - 현재 미사용이지만 추후 확장을 위해 유지
// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface ExtendedUser extends BaseUser {
  phone?: string
  wallet_address?: string // 호환성을 위해
  created_at?: string // 호환성을 위해  
  last_login?: string // 호환성을 위해
  kyc_status?: 'none' | 'pending' | 'approved' | 'rejected' // 호환성을 위해
  tier?: 'basic' | 'premium' | 'vip'
  referral_code?: string
  referred_by?: string
}

interface UserStats {
  total_users: number
  active_users: number
  new_users_today: number
  total_balance: number
  average_balance: number
  kyc_approved: number
  kyc_pending: number
}

// 백엔드 응답 타입 (실제 API 응답 구조)
interface UserStatsResponse {
  total_users: number
  active_users: number
  new_users: number
  new_users_today: number
  total_balance: number
  average_balance: number
  kyc_approved: number
  kyc_pending: number
  daily_growth: number
  weekly_growth: number
  activity_rate: number
}

function UsersPage() {
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [kycFilter, setKycFilter] = useState<string>('')
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])

  // 필터가 변경되면 첫 페이지로 이동
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, kycFilter]);

  // 필터 객체 생성
  const filters = React.useMemo((): UserFilters => {
    const filterObj: UserFilters = {};
    if (searchTerm) filterObj.search = searchTerm;
    if (statusFilter) filterObj.status = statusFilter as 'active' | 'inactive' | 'suspended' | 'pending';
    if (kycFilter) filterObj.kycStatus = kycFilter as 'none' | 'pending' | 'approved' | 'rejected';
    return filterObj;
  }, [searchTerm, statusFilter, kycFilter]);

  // 실제 API 데이터 사용 (필터 적용)
  const { data: usersData, isLoading: usersLoading, isError: usersError, refetch } = useUsers(currentPage, 20, filters);
  const { data: statsData, isLoading: statsLoading, isError: statsError } = useUserStats();
  
  // 디버깅을 위한 로그
  console.log('Users Data:', usersData);
  console.log('Stats Data:', statsData);
  console.log('Loading states:', { usersLoading, statsLoading });
  console.log('Error states:', { usersError, statsError });
  
  // 벌크 액션 mutations
  const bulkUpdateMutation = useBulkUpdateUsers();
  const exportMutation = useExportUsers();
  const createUserMutation = useCreateUser();

  // 폴백 데이터
  const fallbackUsers: BaseUser[] = [
    {
      id: '1',
      username: 'john_doe',
      email: 'john@example.com',
      phone: '+82-10-1234-5678',
      walletAddress: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
      balance: 15000.50,
      status: 'active',
      createdAt: '2024-01-15T09:30:00Z',
      lastLogin: '2024-07-13T08:45:00Z',
      kycStatus: 'approved',
      tier: 'premium',
      totalTransactions: 0,
      totalVolume: 0
    },
    {
      id: '2',
      username: 'jane_smith',
      email: 'jane@example.com',
      phone: '+82-10-9876-5432',
      walletAddress: 'TMuA6YqfCeX8EhbfYEg5y7S4DqzSJireY9',
      balance: 8750.25,
      status: 'active',
      createdAt: '2024-02-20T14:15:00Z',
      lastLogin: '2024-07-12T19:30:00Z',
      kycStatus: 'approved',
      tier: 'basic',
      totalTransactions: 0,
      totalVolume: 0
    },
    {
      id: '3',
      username: 'bob_wilson',
      email: 'bob@example.com',
      walletAddress: 'TLPpXqUYssrZPCWwP1MUK8yqeZsKAFa2Z8',
      balance: 2340.00,
      status: 'inactive',
      createdAt: '2024-03-10T11:00:00Z',
      lastLogin: '2024-07-01T16:20:00Z',
      kycStatus: 'pending',
      tier: 'basic',
      totalTransactions: 0,
      totalVolume: 0
    },
    {
      id: '4',
      username: 'alice_johnson',
      email: 'alice@example.com',
      phone: '+82-10-5555-1234',
      walletAddress: 'TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs',
      balance: 45600.75,
      status: 'active',
      createdAt: '2024-01-05T10:30:00Z',
      lastLogin: '2024-07-13T07:15:00Z',
      kycStatus: 'approved',
      tier: 'vip',
      totalTransactions: 0,
      totalVolume: 0
    },
    {
      id: '5',
      username: 'charlie_brown',
      email: 'charlie@example.com',
      walletAddress: 'TSSMHYeV2uE9qYH14Hvcs6HjRNjPYWMGpT',
      balance: 0.00,
      status: 'suspended',
      createdAt: '2024-06-15T16:45:00Z',
      lastLogin: '2024-06-20T10:00:00Z',
      kycStatus: 'rejected',
      tier: 'basic',
      totalTransactions: 0,
      totalVolume: 0
    }
  ];

  const fallbackStats: UserStats = {
    total_users: 1247,
    active_users: 892,
    new_users_today: 23,
    total_balance: 2847352.75,
    average_balance: 2284.12,
    kyc_approved: 756,
    kyc_pending: 89
  };

  // 데이터 매핑
  const users = (usersData as { users?: BaseUser[] })?.users || fallbackUsers;
  
  // 백엔드 응답을 프론트엔드 UserStats 형식으로 변환
  const statsResponse = statsData as UserStatsResponse | null;
  const stats: UserStats = statsResponse ? {
    total_users: statsResponse.total_users || 0,
    active_users: statsResponse.active_users || 0,
    new_users_today: statsResponse.new_users_today || 0,
    total_balance: statsResponse.total_balance || 0,
    average_balance: statsResponse.average_balance || 0,
    kyc_approved: statsResponse.kyc_approved || 0,
    kyc_pending: statsResponse.kyc_pending || 0
  } : fallbackStats;

  const handleUserSelect = (userId: string) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedUsers(users.map((u: BaseUser) => u.id))
    } else {
      setSelectedUsers([])
    }
  }

  const handleBulkAction = async (action: string) => {
    if (selectedUsers.length === 0) {
      alert('선택된 사용자가 없습니다.');
      return;
    }

    try {
      switch (action) {
        case 'activate':
          await bulkUpdateMutation.mutateAsync({
            userIds: selectedUsers,
            updates: { status: 'active' }
          });
          alert(`${selectedUsers.length}명의 사용자가 활성화되었습니다.`);
          break;
          
        case 'deactivate':
          await bulkUpdateMutation.mutateAsync({
            userIds: selectedUsers,
            updates: { status: 'inactive' }
          });
          alert(`${selectedUsers.length}명의 사용자가 비활성화되었습니다.`);
          break;
          
        case 'export':
          const csvData = await exportMutation.mutateAsync(filters);
          const blob = new Blob([csvData], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
          a.click();
          window.URL.revokeObjectURL(url);
          break;
          
        default:
          console.log(`Unknown action: ${action}`);
      }
      
      // 선택 해제
      setSelectedUsers([]);
      
    } catch (error) {
      console.error('Bulk action failed:', error);
      alert('작업 실행 중 오류가 발생했습니다.');
    }
  }

  const handleAddUser = async () => {
    const username = prompt('사용자명을 입력하세요:');
    const email = prompt('이메일을 입력하세요:');
    
    if (!username || !email) {
      alert('사용자명과 이메일을 모두 입력해야 합니다.');
      return;
    }

    // 간단한 이메일 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert('올바른 이메일 형식을 입력하세요.');
      return;
    }

    try {
      await createUserMutation.mutateAsync({
        username,
        email,
        tier: 'basic',
        send_welcome_email: true
      });
      alert('사용자가 성공적으로 추가되었습니다.');
    } catch (error) {
      console.error('Failed to create user:', error);
      alert('사용자 추가 중 오류가 발생했습니다.');
    }
  }

  const handleRefresh = () => {
    refetch();
  }

  const loading = usersLoading || statsLoading
  const error = usersError || statsError

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        {/* 페이지 헤더 */}
        <PageHeader
          title="사용자 관리"
          description="플랫폼 사용자 현황 및 관리"
          showDownload={true}
        >
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={usersLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${usersLoading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
            <Button onClick={handleAddUser} disabled={createUserMutation.isPending}>
              <Plus className="h-4 w-4 mr-2" />
              {createUserMutation.isPending ? '추가 중...' : '사용자 추가'}
            </Button>
          </div>
        </PageHeader>

        {/* 통계 카드 */}
        <UserStats data={stats} loading={loading} />

        {/* 사용자 관리 섹션 */}
        <UserManagementSection
          // 필터 상태
          searchTerm={searchTerm}
          statusFilter={statusFilter}
          kycFilter={kycFilter}
          onSearchChange={setSearchTerm}
          onStatusFilterChange={setStatusFilter}
          onKycFilterChange={setKycFilter}
          
          // 테이블 데이터
          users={users}
          loading={loading}
          error={error}
          
          // 선택 상태
          selectedUsers={selectedUsers}
          onUserSelect={handleUserSelect}
          onSelectAll={handleSelectAll}
          
          // 벌크 액션
          onBulkActivate={() => handleBulkAction('activate')}
          onBulkDeactivate={() => handleBulkAction('deactivate')}
          onBulkExport={() => handleBulkAction('export')}
          
          // 페이지네이션
          currentPage={currentPage}
          totalItems={stats.total_users}
          itemsPerPage={20}
          onPageChange={setCurrentPage}
        />
      </div>
    </Sidebar>
  )
}

// 인증이 필요한 페이지로 래핑
export default withAuth(UsersPage);
