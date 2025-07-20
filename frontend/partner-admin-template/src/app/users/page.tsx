'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { PageHeader } from '@/components/common/PageHeader'
import { UserStats } from '@/components/common/StatsCards'
import { UserManagementSection } from '@/components/users/UserFilters'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { useUsers, useUserStats } from '@/lib/hooks'
import { withAuth } from '@/contexts/AuthContext'

interface User {
  id: string
  username: string
  email: string
  phone?: string
  wallet_address: string
  balance: number
  status: 'active' | 'inactive' | 'suspended' | 'pending'
  created_at: string
  last_login?: string
  kyc_status: 'none' | 'pending' | 'approved' | 'rejected'
  tier: 'basic' | 'premium' | 'vip'
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

  // ...existing code...
  // 실제 API 데이터 사용
  const { data: usersData, isLoading: usersLoading, isError: usersError } = useUsers(currentPage, 20);
  const { data: statsData, isLoading: statsLoading, isError: statsError } = useUserStats();

  // 폴백 데이터
  const fallbackUsers: User[] = [
    {
      id: '1',
      username: 'john_doe',
      email: 'john@example.com',
      phone: '+82-10-1234-5678',
      wallet_address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
      balance: 15000.50,
      status: 'active',
      created_at: '2024-01-15T09:30:00Z',
      last_login: '2024-07-13T08:45:00Z',
      kyc_status: 'approved',
      tier: 'premium',
      referral_code: 'JOHN2024',
      referred_by: undefined
    },
    {
      id: '2',
      username: 'jane_smith',
      email: 'jane@example.com',
      phone: '+82-10-9876-5432',
      wallet_address: 'TMuA6YqfCeX8EhbfYEg5y7S4DqzSJireY9',
      balance: 8750.25,
      status: 'active',
      created_at: '2024-02-20T14:15:00Z',
      last_login: '2024-07-12T19:30:00Z',
      kyc_status: 'approved',
      tier: 'basic',
      referral_code: 'JANE2024'
    },
    {
      id: '3',
      username: 'bob_wilson',
      email: 'bob@example.com',
      wallet_address: 'TLPpXqUYssrZPCWwP1MUK8yqeZsKAFa2Z8',
      balance: 2340.00,
      status: 'inactive',
      created_at: '2024-03-10T11:00:00Z',
      last_login: '2024-07-01T16:20:00Z',
      kyc_status: 'pending',
      tier: 'basic'
    },
    {
      id: '4',
      username: 'alice_johnson',
      email: 'alice@example.com',
      phone: '+82-10-5555-1234',
      wallet_address: 'TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs',
      balance: 45600.75,
      status: 'active',
      created_at: '2024-01-05T10:30:00Z',
      last_login: '2024-07-13T07:15:00Z',
      kyc_status: 'approved',
      tier: 'vip',
      referral_code: 'ALICE2024'
    },
    {
      id: '5',
      username: 'charlie_brown',
      email: 'charlie@example.com',
      wallet_address: 'TSSMHYeV2uE9qYH14Hvcs6HjRNjPYWMGpT',
      balance: 0.00,
      status: 'suspended',
      created_at: '2024-06-15T16:45:00Z',
      kyc_status: 'rejected',
      tier: 'basic'
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
  const users = (usersData as { users?: User[] })?.users || fallbackUsers;
  
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
      setSelectedUsers(users.map((u: User) => u.id))
    } else {
      setSelectedUsers([])
    }
  }

  const handleBulkAction = (action: string) => {
    console.log(`Bulk action: ${action} for users:`, selectedUsers)
    // TODO: 실제 벌크 액션 구현
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
          <Button onClick={() => console.log('Add user')}>
            <Plus className="h-4 w-4 mr-2" />
            사용자 추가
          </Button>
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
