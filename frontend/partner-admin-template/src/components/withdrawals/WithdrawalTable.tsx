'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  CheckCircle, 
  Clock, 
  XCircle,
  Loader2,
  Zap,
  TrendingUp
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { WithdrawalRequest } from '@/types'

interface WithdrawalTableProps {
  withdrawals: WithdrawalRequest[]
  loading: boolean
  error: boolean
  selectedRequests: string[]
  onRequestSelect: (requestId: string) => void
  onSelectAll: (checked: boolean) => void
  onApprove: (requestId: string) => void
  onReject: (requestId: string) => void
  onViewDetails: (requestId: string) => void
}

export function WithdrawalTable({
  withdrawals,
  loading,
  error,
  selectedRequests,
  onRequestSelect,
  onSelectAll,
  onApprove,
  onReject,
  onViewDetails
}: WithdrawalTableProps) {
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

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-medium text-gray-600">
              <input 
                type="checkbox" 
                className="rounded border-gray-300"
                checked={selectedRequests.length === withdrawals.length && withdrawals.length > 0}
                onChange={(e) => onSelectAll(e.target.checked)}
              />
            </th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">요청 ID</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">사용자</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">금액</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">에너지/수익</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">대상 주소</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">상태</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">요청 시간</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">작업</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={9} className="px-4 py-8 text-center">
                <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                <p className="text-gray-500 mt-2">출금 요청을 불러오는 중...</p>
              </td>
            </tr>
          ) : error ? (
            <tr>
              <td colSpan={9} className="px-4 py-8 text-center text-red-600">
                출금 요청을 불러오는데 실패했습니다.
              </td>
            </tr>
          ) : withdrawals.length === 0 ? (
            <tr>
              <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                검색 조건에 맞는 출금 요청이 없습니다.
              </td>
            </tr>
          ) : (
            withdrawals.map((withdrawal) => (
              <tr key={withdrawal.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-4">
                  <input 
                    type="checkbox" 
                    className="rounded border-gray-300"
                    checked={selectedRequests.includes(withdrawal.id)}
                    onChange={() => onRequestSelect(withdrawal.id)}
                  />
                </td>
                <td className="py-3 px-4 font-mono text-sm text-gray-900">
                  {withdrawal.id}
                </td>
                <td className="py-3 px-4 text-gray-900">
                  <div>
                    <p className="font-medium">{withdrawal.user_name}</p>
                    <p className="text-sm text-gray-500">{withdrawal.user_id}</p>
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-900">
                  <div>
                    <p className="font-medium">{formatCurrency(withdrawal.amount)} {withdrawal.currency}</p>
                    <p className="text-sm text-gray-500">
                      수수료: {formatCurrency(withdrawal.fee)} {withdrawal.fee_currency || withdrawal.currency}
                    </p>
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-900">
                  <div className="space-y-1">
                    {withdrawal.energy_consumed !== undefined && (
                      <div className="flex items-center gap-1 text-sm">
                        <Zap className="w-3 h-3 text-yellow-500" />
                        <span className="text-gray-600">{withdrawal.energy_consumed.toLocaleString()} Energy</span>
                      </div>
                    )}
                    {withdrawal.energy_cost !== undefined && (
                      <div className="text-xs text-gray-500">
                        비용: {formatCurrency(withdrawal.energy_cost)} TRX
                      </div>
                    )}
                    {withdrawal.profit_margin !== undefined && (
                      <div className="flex items-center gap-1 text-sm">
                        <TrendingUp className="w-3 h-3 text-green-500" />
                        <span className={`font-medium ${withdrawal.profit_margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {withdrawal.profit_margin >= 0 ? '+' : ''}{formatCurrency(withdrawal.profit_margin)} {withdrawal.fee_currency || 'USDT'}
                        </span>
                      </div>
                    )}
                    {(withdrawal.energy_consumed === undefined && withdrawal.energy_cost === undefined && withdrawal.profit_margin === undefined) && (
                      <div className="text-xs text-gray-400">
                        에너지 정보 없음
                      </div>
                    )}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs text-gray-900">
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
                <td className="py-3 px-4 text-sm text-gray-600">
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
                        <Button 
                          size="sm" 
                          className="bg-green-600 hover:bg-green-700 text-white"
                          onClick={() => onApprove(withdrawal.id)}
                        >
                          승인
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="text-red-600 border-red-600 hover:bg-red-50"
                          onClick={() => onReject(withdrawal.id)}
                        >
                          거절
                        </Button>
                      </>
                    )}
                    <Button 
                      size="sm" 
                      variant="ghost"
                      onClick={() => onViewDetails(withdrawal.id)}
                    >
                      상세
                    </Button>
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
