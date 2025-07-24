'use client'

import React, { useState, useMemo } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { PageHeader } from '@/components/common/PageHeader'
import { WithdrawalStats } from '@/components/withdrawals/WithdrawalStats'
import { WithdrawalManagementSection } from '@/components/withdrawals/WithdrawalFilters'
import { Button } from '@/components/ui/button'
import { CheckCircle } from 'lucide-react'
// import { useWithdrawalRequests } from '@/lib/hooks'

interface WithdrawalRequest {
  id: string
  user_id: string
  user_name: string
  amount: number
  currency: string
  destination_address: string
  status: 'pending' | 'approved' | 'processing' | 'completed' | 'failed' | 'rejected'
  request_time: string
  processed_time?: string
  transaction_hash?: string
  fee: number
  fee_currency: 'USDT' | 'TRX'  // 수수료 통화
}

export default function WithdrawalsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedRequests, setSelectedRequests] = useState<string[]>([])
  // const [currentPage] = useState(1) // TODO: 페이지네이션 구현 시 사용

  // 폴백 데이터 (API 실패 시)
  const fallbackWithdrawals: WithdrawalRequest[] = useMemo(() => [
    {
      id: 'wd_001',
      user_id: 'user_123',
      user_name: 'John Doe',
      amount: 1000.50,
      currency: 'TRX',
      destination_address: 'TQn9Y2khEsLMG73Dj2yB7KJEky1AbcDef123',
      status: 'pending',
      request_time: '2025-01-15T10:30:00Z',
      fee: 10.0,
      fee_currency: 'USDT'
    },
    {
      id: 'wd_002', 
      user_id: 'user_456',
      user_name: 'Jane Smith',
      amount: 500.25,
      currency: 'TRX',
      destination_address: 'TLyqzVGLV1srkB7dToTAEqgDrZ5xyz789',
      status: 'completed',
      request_time: '2025-01-15T09:15:00Z',
      processed_time: '2025-01-15T09:30:00Z',
      transaction_hash: '0x123abc456def...',
      fee: 5.0,
      fee_currency: 'USDT'
    },
    {
      id: 'wd_003',
      user_id: 'user_789',
      user_name: 'Bob Wilson',
      amount: 2500.00,
      currency: 'TRX',
      destination_address: 'TMn8X3vFgHj9Kl2PqRs4TuvWxy123abc',
      status: 'failed',
      request_time: '2025-01-15T08:45:00Z',
      processed_time: '2025-01-15T09:00:00Z',
      fee: 25.0,
      fee_currency: 'USDT'
    }
  ], []);

  // API 데이터 매핑 (백엔드 없으므로 폴백 데이터 사용)
  const withdrawals = fallbackWithdrawals;

  // 검색 및 필터링
  const filteredWithdrawals = useMemo(() => {
    return withdrawals.filter(withdrawal => {
      const matchesSearch = searchTerm === '' || 
        withdrawal.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        withdrawal.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        withdrawal.destination_address.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || withdrawal.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    });
  }, [withdrawals, searchTerm, statusFilter]);

  const handleRequestSelect = (requestId: string) => {
    setSelectedRequests(prev => 
      prev.includes(requestId) 
        ? prev.filter(id => id !== requestId)
        : [...prev, requestId]
    )
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRequests(filteredWithdrawals.map(w => w.id))
    } else {
      setSelectedRequests([])
    }
  }

  // 배치 승인 처리
  const handleBatchApproval = () => {
    console.log('배치 승인 요청:', selectedRequests);
    setSelectedRequests([]);
  };

  const handleApprove = (requestId: string) => {
    console.log('승인:', requestId);
  };

  const handleReject = (requestId: string) => {
    console.log('거절:', requestId);
  };

  const handleViewDetails = (requestId: string) => {
    console.log('상세 보기:', requestId);
  };

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        {/* 페이지 헤더 */}
        <PageHeader
          title="출금 관리"
          description="사용자 출금 요청을 관리하고 승인합니다"
          showDownload={true}
          onRefresh={() => console.log('Refresh withdrawals')}
        >
          {selectedRequests.length > 0 && (
            <Button onClick={handleBatchApproval}>
              <CheckCircle className="h-4 w-4 mr-2" />
              일괄 승인 ({selectedRequests.length})
            </Button>
          )}
        </PageHeader>

        {/* 통계 카드 */}
        <WithdrawalStats withdrawals={withdrawals} />

        {/* 출금 관리 섹션 */}
        <WithdrawalManagementSection
          // 필터 상태
          searchTerm={searchTerm}
          statusFilter={statusFilter}
          onSearchChange={setSearchTerm}
          onStatusFilterChange={setStatusFilter}
          
          // 테이블 데이터
          withdrawals={filteredWithdrawals}
          loading={false}
          error={false}
          
          // 선택 상태
          selectedRequests={selectedRequests}
          onRequestSelect={handleRequestSelect}
          onSelectAll={handleSelectAll}
          
          // 액션
          onApprove={handleApprove}
          onReject={handleReject}
          onViewDetails={handleViewDetails}
        />
      </div>
    </Sidebar>
  )
}
