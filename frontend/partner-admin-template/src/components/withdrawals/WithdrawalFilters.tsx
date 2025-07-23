'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'
import { WithdrawalTable } from './WithdrawalTable'
import { WithdrawalRequest } from '@/types'

interface WithdrawalManagementSectionProps {
  // 필터 상태
  searchTerm: string
  statusFilter: string
  onSearchChange: (value: string) => void
  onStatusFilterChange: (value: string) => void
  
  // 테이블 데이터
  withdrawals: WithdrawalRequest[]
  loading: boolean
  error: boolean
  
  // 선택 상태
  selectedRequests: string[]
  onRequestSelect: (requestId: string) => void
  onSelectAll: (checked: boolean) => void
  
  // 액션
  onApprove: (requestId: string) => void
  onReject: (requestId: string) => void
  onViewDetails: (requestId: string) => void
}

export function WithdrawalManagementSection({
  searchTerm,
  statusFilter,
  onSearchChange,
  onStatusFilterChange,
  withdrawals,
  loading,
  error,
  selectedRequests,
  onRequestSelect,
  onSelectAll,
  onApprove,
  onReject,
  onViewDetails
}: WithdrawalManagementSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-gray-900">출금 요청 목록</CardTitle>
        <CardDescription className="text-gray-600">
          사용자들의 출금 요청을 확인하고 처리할 수 있습니다.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* 필터 및 검색 */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="사용자 이름, 요청 ID 또는 주소로 검색..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
          <select 
            value={statusFilter} 
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900"
          >
            <option value="all">모든 상태</option>
            <option value="pending">대기 중</option>
            <option value="approved">승인됨</option>
            <option value="processing">처리 중</option>
            <option value="completed">완료</option>
            <option value="failed">실패</option>
            <option value="rejected">거절</option>
          </select>
        </div>

        {/* 출금 요청 테이블 */}
        <WithdrawalTable
          withdrawals={withdrawals}
          loading={loading}
          error={error}
          selectedRequests={selectedRequests}
          onRequestSelect={onRequestSelect}
          onSelectAll={onSelectAll}
          onApprove={onApprove}
          onReject={onReject}
          onViewDetails={onViewDetails}
        />
      </CardContent>
    </Card>
  )
}
