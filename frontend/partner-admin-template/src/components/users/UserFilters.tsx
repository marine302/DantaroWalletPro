'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, RefreshCw } from 'lucide-react'
import { BulkActions } from './BulkActions'
import { UserTable } from './UserTable'
import { Pagination } from './Pagination'
import type { User } from '@/types'

interface UserManagementSectionProps {
  // 필터 상태
  searchTerm: string
  statusFilter: string
  kycFilter: string
  onSearchChange: (value: string) => void
  onStatusFilterChange: (value: string) => void
  onKycFilterChange: (value: string) => void
  
  // 테이블 데이터
  users: User[]
  loading: boolean
  error: boolean
  
  // 선택 상태
  selectedUsers: string[]
  onUserSelect: (userId: string) => void
  onSelectAll: (checked: boolean) => void
  
  // 벌크 액션
  onBulkActivate: () => void
  onBulkDeactivate: () => void
  onBulkExport: () => void
  
  // 페이지네이션
  currentPage: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  
  // 새로고침
  onRefresh?: () => void
  
  // 사용자 액션
  onViewUser?: (user: User) => void
  onEditUser?: (user: User) => void
  onDeleteUser?: (user: User) => void
}

export function UserManagementSection({
  searchTerm,
  statusFilter,
  kycFilter,
  onSearchChange,
  onStatusFilterChange,
  onKycFilterChange,
  users,
  loading,
  error,
  selectedUsers,
  onUserSelect,
  onSelectAll,
  onBulkActivate,
  onBulkDeactivate,
  onBulkExport,
  currentPage,
  totalItems,
  itemsPerPage,
  onPageChange,
  onRefresh,
  onViewUser,
  onEditUser,
  onDeleteUser
}: UserManagementSectionProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>사용자 목록</CardTitle>
            <CardDescription>사용자 검색 및 필터링</CardDescription>
          </div>
          {onRefresh && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* 필터 및 검색 */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="사용자명, 이메일, 지갑 주소로 검색..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">모든 상태</option>
            <option value="active">활성</option>
            <option value="inactive">비활성</option>
            <option value="suspended">정지</option>
            <option value="pending">대기</option>
          </select>
          <select
            value={kycFilter}
            onChange={(e) => onKycFilterChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">모든 KYC</option>
            <option value="approved">승인</option>
            <option value="pending">대기</option>
            <option value="rejected">거부</option>
            <option value="none">미제출</option>
          </select>
        </div>

        {/* 벌크 액션 */}
        <BulkActions
          selectedCount={selectedUsers.length}
          onActivate={onBulkActivate}
          onDeactivate={onBulkDeactivate}
          onExport={onBulkExport}
        />

        {/* 사용자 테이블 */}
        <UserTable
          users={users}
          loading={loading}
          error={error}
          selectedUsers={selectedUsers}
          onUserSelect={onUserSelect}
          onSelectAll={onSelectAll}
          onViewUser={onViewUser}
          onEditUser={onEditUser}
          onDeleteUser={onDeleteUser}
        />

        {/* 페이지네이션 */}
        <Pagination
          currentPage={currentPage}
          totalItems={totalItems}
          itemsPerPage={itemsPerPage}
          displayedItems={users.length}
          onPageChange={onPageChange}
        />
      </CardContent>
    </Card>
  )
}
