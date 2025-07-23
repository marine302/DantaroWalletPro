'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { PageHeader } from '@/components/common/PageHeader'
import { UserStats } from '@/components/common/StatsCards'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { useUsers, useUserStats, useBulkUpdateUsers, useExportUsers, useCreateUser, useUpdateUser, useDeleteUser } from '@/lib/hooks'
import { withAuth } from '@/contexts/AuthContext'
import { UserManagementSection } from '@/components/users/UserFilters'
import { AddUserModal } from '@/components/users/AddUserModal'
import { UserDetailModal } from '@/components/users/UserDetailModal'
import { EditUserModal } from '@/components/users/EditUserModal'
import { DeleteUserModal } from '@/components/users/DeleteUserModal'
import type { User } from '@/types'
import type { UserFilters } from '@/types/user'

interface UserStatsData {
  total_users: number
  active_users: number
  new_users_today: number
  total_balance: number
  average_balance: number
  kyc_approved: number
  kyc_pending: number
}

// 백엔드 응답 타입 (실제 API 응답 구조)
interface UserStatsResponse extends UserStatsData {
  new_users: number
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
  const [isAddUserModalOpen, setIsAddUserModalOpen] = useState(false)
  
  // 개별 사용자 액션 모달 상태
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

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
  const updateUserMutation = useUpdateUser();
  const deleteUserMutation = useDeleteUser();

  // 폴백 데이터
  const fallbackUsers: User[] = [
    {
      id: '1',
      username: 'john_doe',
      email: 'john@example.com',
      walletAddress: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
      wallet_address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
      balance: 15000.50,
      status: 'active',
      kycStatus: 'approved',
      kyc_status: 'approved',
      createdAt: '2024-01-15T09:30:00Z',
      created_at: '2024-01-15T09:30:00Z',
      lastLogin: '2024-07-13T08:45:00Z',
      last_login: '2024-07-13T08:45:00Z',
      totalTransactions: 45,
      totalVolume: 150000.50,
      tier: 'premium'
    },
    {
      id: '2',
      username: 'jane_smith',
      email: 'jane@example.com',
      walletAddress: 'TMuA6YqfCeX8EhbfYEg5y7S4DqzSJireY9',
      wallet_address: 'TMuA6YqfCeX8EhbfYEg5y7S4DqzSJireY9',
      balance: 8750.25,
      status: 'active',
      kycStatus: 'approved',
      kyc_status: 'approved',
      createdAt: '2024-02-20T14:15:00Z',
      created_at: '2024-02-20T14:15:00Z',
      lastLogin: '2024-07-12T19:30:00Z',
      last_login: '2024-07-12T19:30:00Z',
      totalTransactions: 23,
      totalVolume: 87500.25,
      tier: 'basic'
    },
    {
      id: '3',
      username: 'bob_wilson',
      email: 'bob@example.com',
      walletAddress: 'TLPpXqUYssrZPCWwP1MUK8yqeZsKAFa2Z8',
      wallet_address: 'TLPpXqUYssrZPCWwP1MUK8yqeZsKAFa2Z8',
      balance: 2340.00,
      status: 'inactive',
      kycStatus: 'pending',
      kyc_status: 'pending',
      createdAt: '2024-03-10T11:00:00Z',
      created_at: '2024-03-10T11:00:00Z',
      lastLogin: '2024-07-01T16:20:00Z',
      last_login: '2024-07-01T16:20:00Z',
      totalTransactions: 8,
      totalVolume: 23400.00,
      tier: 'basic'
    }
  ];

  const fallbackStats: UserStatsData = {
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
  
  // 백엔드 응답을 프론트엔드 UserStatsData 형식으로 변환
  const statsResponse = statsData as UserStatsResponse | null;
  const stats: UserStatsData = statsResponse ? {
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

  const handleAddUser = async (userData: {
    username: string
    email: string
    tier: 'basic' | 'premium' | 'vip'
    send_welcome_email: boolean
  }) => {
    await createUserMutation.mutateAsync(userData)
    refetch() // 사용자 목록 새로고침
  }

  // 개별 사용자 액션 핸들러들
  const handleViewUser = (user: User) => {
    setSelectedUser(user)
    setIsDetailModalOpen(true)
  }

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    setIsEditModalOpen(true)
  }

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user)
    setIsDeleteModalOpen(true)
  }

  const handleUpdateUser = async (userData: Partial<User> & { id: string }) => {
    await updateUserMutation.mutateAsync({
      userId: userData.id,
      updates: userData
    })
    refetch() // 사용자 목록 새로고침
  }

  const handleConfirmDelete = async (userId: string) => {
    await deleteUserMutation.mutateAsync(userId)
    refetch() // 사용자 목록 새로고침
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
          <Button onClick={() => setIsAddUserModalOpen(true)} disabled={createUserMutation.isPending}>
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
          error={Boolean(error)}
          
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
          
          // 새로고침
          onRefresh={refetch}
          
          // 개별 사용자 액션
          onViewUser={handleViewUser}
          onEditUser={handleEditUser}
          onDeleteUser={handleDeleteUser}
        />
      </div>

      {/* 사용자 추가 모달 */}
      <AddUserModal
        isOpen={isAddUserModalOpen}
        onClose={() => setIsAddUserModalOpen(false)}
        onSubmit={handleAddUser}
        isLoading={createUserMutation.isPending}
      />

      {/* 사용자 상세보기 모달 */}
      <UserDetailModal
        user={selectedUser}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false)
          setSelectedUser(null)
        }}
      />

      {/* 사용자 편집 모달 */}
      <EditUserModal
        user={selectedUser}
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false)
          setSelectedUser(null)
        }}
        onSave={handleUpdateUser}
        isLoading={updateUserMutation.isPending}
      />

      {/* 사용자 삭제 확인 모달 */}
      <DeleteUserModal
        user={selectedUser}
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setSelectedUser(null)
        }}
        onConfirm={handleConfirmDelete}
        isLoading={deleteUserMutation.isPending}
      />
    </Sidebar>
  )
}

// 인증이 필요한 페이지로 래핑
export default withAuth(UsersPage);
