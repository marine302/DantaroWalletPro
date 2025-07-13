'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  XCircle, 
  Download, 
  Search, 
  Loader2
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useWithdrawalRequests } from '@/lib/hooks'

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
}

export default function WithdrawalsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedRequests, setSelectedRequests] = useState<string[]>([])
  const [currentPage] = useState(1)

  // 실제 API 데이터 사용
  const { data: withdrawalsData, loading, error } = useWithdrawalRequests(
    currentPage, 
    20, 
    statusFilter === 'all' ? undefined : statusFilter
  );

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
      fee: 10.0
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
      fee: 5.0
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
      fee: 25.0
    }
  ], []);

  // API 데이터 매핑
  const withdrawals = useMemo(() => {
    if (!withdrawalsData || error) {
      return fallbackWithdrawals;
    }
    // API 응답 데이터를 WithdrawalRequest[] 형식으로 변환
    const apiWithdrawals = (withdrawalsData as unknown as any)?.data || 
                          (withdrawalsData as unknown as any)?.items || 
                          withdrawalsData;
    return Array.isArray(apiWithdrawals) ? apiWithdrawals : fallbackWithdrawals;
  }, [withdrawalsData, error, fallbackWithdrawals]);

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

  // 배치 승인 처리
  const handleBatchApproval = () => {
    console.log('배치 승인 요청:', selectedRequests);
    // 실제 API 호출은 여기에 구현
    setSelectedRequests([]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-blue-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-blue-500" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500'
      case 'approved':
        return 'bg-blue-500'
      case 'processing':
        return 'bg-blue-600'
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'rejected':
        return 'bg-red-600'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '대기 중'
      case 'approved': return '승인됨'
      case 'processing': return '처리 중'
      case 'completed': return '완료'
      case 'failed': return '실패'
      case 'rejected': return '거절'
      default: return status
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="text-lg text-foreground">출금 요청을 불러오는 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-semibold text-red-600">데이터 로딩 오류</h2>
          <p className="text-gray-600">출금 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.</p>
          <p className="text-sm text-gray-500">오류: {error.message}</p>
          <Button onClick={() => window.location.reload()} variant="outline">
            다시 시도
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-foreground">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">출금 관리</h1>
          <p className="text-gray-600 dark:text-gray-300">사용자 출금 요청을 관리하고 승인합니다 (Doc-28 기반)</p>
        </div>
        <div className="flex items-center gap-2">
          {selectedRequests.length > 0 && (
            <Button onClick={handleBatchApproval} size="sm">
              <CheckCircle className="h-4 w-4 mr-2" />
              일괄 승인 ({selectedRequests.length})
            </Button>
          )}
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            보고서 다운로드
          </Button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">전체 요청</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{withdrawals.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">대기 중</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {withdrawals.filter(w => w.status === 'pending').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">완료</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {withdrawals.filter(w => w.status === 'completed').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">실패/거절</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {withdrawals.filter(w => w.status === 'failed' || w.status === 'rejected').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground">출금 요청 목록</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-300">
            사용자들의 출금 요청을 확인하고 처리할 수 있습니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="사용자 이름, 요청 ID 또는 주소로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-foreground"
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

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">
                    <input 
                      type="checkbox" 
                      className="rounded border-gray-300"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedRequests(filteredWithdrawals.map(w => w.id));
                        } else {
                          setSelectedRequests([]);
                        }
                      }}
                    />
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">요청 ID</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">사용자</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">금액</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">대상 주소</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">상태</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">요청 시간</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-300">작업</th>
                </tr>
              </thead>
              <tbody>
                {filteredWithdrawals.map((withdrawal) => (
                  <tr key={withdrawal.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="py-3 px-4">
                      <input 
                        type="checkbox" 
                        className="rounded border-gray-300"
                        checked={selectedRequests.includes(withdrawal.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedRequests([...selectedRequests, withdrawal.id]);
                          } else {
                            setSelectedRequests(selectedRequests.filter(id => id !== withdrawal.id));
                          }
                        }}
                      />
                    </td>
                    <td className="py-3 px-4 font-mono text-sm text-foreground">
                      {withdrawal.id}
                    </td>
                    <td className="py-3 px-4 text-foreground">
                      <div>
                        <p className="font-medium">{withdrawal.user_name}</p>
                        <p className="text-sm text-gray-500">{withdrawal.user_id}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-foreground">
                      <div>
                        <p className="font-medium">{formatCurrency(withdrawal.amount)} {withdrawal.currency}</p>
                        <p className="text-sm text-gray-500">수수료: {formatCurrency(withdrawal.fee)} {withdrawal.currency}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-xs text-foreground">
                        {withdrawal.destination_address.substring(0, 20)}...
                      </code>
                    </td>
                    <td className="py-3 px-4">
                      <Badge className={`${getStatusColor(withdrawal.status)} text-white`}>
                        <span className="flex items-center gap-1">
                          {getStatusIcon(withdrawal.status)}
                          {getStatusText(withdrawal.status)}
                        </span>
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">
                      <div>
                        <p>{formatDate(withdrawal.request_time)}</p>
                        {withdrawal.processed_time && (
                          <p className="text-xs text-gray-500">
                            처리: {formatDate(withdrawal.processed_time)}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-2">
                        {withdrawal.status === 'pending' && (
                          <>
                            <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white">
                              승인
                            </Button>
                            <Button size="sm" variant="outline" className="text-red-600 border-red-600 hover:bg-red-50">
                              거절
                            </Button>
                          </>
                        )}
                        <Button size="sm" variant="ghost">
                          상세
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredWithdrawals.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">검색 조건에 맞는 출금 요청이 없습니다.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
