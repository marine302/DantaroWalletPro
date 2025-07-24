'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CreditCard, TrendingUp } from 'lucide-react'
import { TransactionHistory } from '@/types'
import { formatCurrency, formatDate } from '@/lib/utils'

interface RecentTransactionsProps {
  transactions: TransactionHistory[]
  onViewAll: () => void
}

export function RecentTransactions({ transactions, onViewAll }: RecentTransactionsProps) {
  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'withdrawal':
        return <CreditCard className="h-4 w-4 text-red-600" />
      case 'deposit':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      default:
        return <CreditCard className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'pending':
        return 'text-yellow-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'withdrawal': return '출금'
      case 'deposit': return '입금'
      default: return type
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return '완료'
      case 'pending': return '대기'
      case 'failed': return '실패'
      default: return status
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>최근 거래 내역</CardTitle>
        <CardDescription>
          최근 24시간 내 거래 현황
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {transactions.map((transaction) => (
            <div 
              key={transaction.id}
              className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                {getTransactionIcon(transaction.type)}
                <div>
                  <div className="font-medium">
                    {getTypeLabel(transaction.type)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(transaction.timestamp)}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  {formatCurrency(transaction.amount, transaction.currency)}
                </div>
                <div className={`text-sm ${getStatusColor(transaction.status)}`}>
                  {getStatusLabel(transaction.status)}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <Button variant="outline" className="w-full" onClick={onViewAll}>
            전체 거래 내역 보기
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
