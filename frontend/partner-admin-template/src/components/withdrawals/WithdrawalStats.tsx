'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle, CheckCircle, Clock, XCircle, Zap, TrendingUp } from 'lucide-react'
import { WithdrawalRequest } from '@/types'
import { formatCurrency } from '@/lib/utils'

interface WithdrawalStatsProps {
  withdrawals: WithdrawalRequest[]
  loading?: boolean
}

export function WithdrawalStats({ withdrawals, loading = false }: WithdrawalStatsProps) {
  const LoadingIcon = () => (
    <div className="w-6 h-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
  )

  const pendingCount = withdrawals.filter(w => w.status === 'pending').length
  const completedCount = withdrawals.filter(w => w.status === 'completed').length
  const failedCount = withdrawals.filter(w => w.status === 'failed' || w.status === 'rejected').length

  // 에너지 및 수익 통계 계산
  const totalEnergyConsumed = withdrawals
    .filter(w => w.energy_consumed !== undefined)
    .reduce((sum, w) => sum + (w.energy_consumed || 0), 0)

  const totalProfitMargin = withdrawals
    .filter(w => w.profit_margin !== undefined)
    .reduce((sum, w) => sum + (w.profit_margin || 0), 0)

  return (
    <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-900">전체 요청</CardTitle>
          <AlertTriangle className="h-4 w-4 text-gray-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-gray-900">
            {loading ? <LoadingIcon /> : withdrawals.length}
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-900">대기 중</CardTitle>
          <Clock className="h-4 w-4 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-yellow-600">
            {loading ? <LoadingIcon /> : pendingCount}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-900">완료</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {loading ? <LoadingIcon /> : completedCount}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-900">실패/거절</CardTitle>
          <XCircle className="h-4 w-4 text-red-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">
            {loading ? <LoadingIcon /> : failedCount}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-900">총 에너지 사용</CardTitle>
          <Zap className="h-4 w-4 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold text-gray-900">
            {loading ? <LoadingIcon /> : `${(totalEnergyConsumed / 1000).toLocaleString()}K`}
          </div>
          <p className="text-xs text-gray-500">Energy</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-900">총 수익</CardTitle>
          <TrendingUp className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className={`text-xl font-bold ${totalProfitMargin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {loading ? <LoadingIcon /> : `${totalProfitMargin >= 0 ? '+' : ''}${formatCurrency(totalProfitMargin)}`}
          </div>
          <p className="text-xs text-gray-500">USDT</p>
        </CardContent>
      </Card>
    </div>
  )
}
