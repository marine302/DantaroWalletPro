'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { StatsCards, EnergyPoolCard } from '@/components/dashboard/StatsCards'
import { WalletConnection } from '@/components/wallet/WalletConnection'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bell, RefreshCw, AlertTriangle, TrendingUp, CreditCard } from 'lucide-react'
import { DashboardStats, TransactionHistory, Notification } from '@/types'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function DashboardPage() {
  const [stats] = useState<DashboardStats>({
    totalUsers: 1250,
    totalBalance: 845620.50,
    totalTransactions: 3420,
    totalRevenue: 15420.75,
    dailyGrowth: 2.3,
    weeklyGrowth: 8.7,
    monthlyGrowth: 12.4
  })

  const [energyPool] = useState({
    totalEnergy: 1000000,
    availableEnergy: 750000,
    stakeAmount: 50000,
    freezeAmount: 25000,
    dailyConsumption: 15000,
    efficiency: 85.5,
    status: 'active' as const
  })

  const [recentTransactions] = useState<TransactionHistory[]>([
    {
      id: '1',
      type: 'withdrawal',
      amount: 500.50,
      currency: 'TRX',
      from: 'TQn9Y2khEsLMG73Dj2yB7KJEky1...',
      to: 'TLyqzVGLV1srkB7dToTAEqgDrZ5...',
      status: 'completed',
      timestamp: '2024-01-15T10:30:00Z',
      txHash: '0x123abc...'
    },
    {
      id: '2',
      type: 'deposit',
      amount: 1200.00,
      currency: 'TRX',
      from: 'TLyqzVGLV1srkB7dToTAEqgDrZ5...',
      to: 'TQn9Y2khEsLMG73Dj2yB7KJEky1...',
      status: 'pending',
      timestamp: '2024-01-15T10:25:00Z'
    },
    {
      id: '3',
      type: 'energy',
      amount: 10000,
      currency: 'ENERGY',
      from: 'System',
      to: 'Energy Pool',
      status: 'completed',
      timestamp: '2024-01-15T10:20:00Z'
    }
  ])

  const [notifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'warning',
      title: '에너지 풀 임계값 경고',
      message: '에너지 풀 사용률이 75%를 초과했습니다.',
      timestamp: '2024-01-15T10:30:00Z',
      read: false
    },
    {
      id: '2',
      type: 'success',
      title: '일괄 출금 완료',
      message: '50건의 출금 요청이 성공적으로 처리되었습니다.',
      timestamp: '2024-01-15T10:15:00Z',
      read: false
    },
    {
      id: '3',
      type: 'info',
      title: '새로운 사용자 등록',
      message: '15명의 새로운 사용자가 등록되었습니다.',
      timestamp: '2024-01-15T10:00:00Z',
      read: true
    }
  ])

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'withdrawal':
        return <CreditCard className="h-4 w-4 text-red-600" />
      case 'deposit':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'energy':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
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

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'success':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'info':
        return <Bell className="h-4 w-4 text-blue-600" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      default:
        return <Bell className="h-4 w-4 text-gray-600" />
    }
  }

  return (
    <Sidebar>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
            <p className="text-gray-600">파트너 관리자 통합 대시보드</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              새로고침
            </Button>
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              알림 ({notifications.filter(n => !n.read).length})
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <StatsCards stats={stats} />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Energy Pool & Wallet */}
          <div className="space-y-6">
            <EnergyPoolCard energyPool={energyPool} />
            <WalletConnection />
          </div>

          {/* Middle Column - Recent Transactions */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>최근 거래 내역</CardTitle>
                <CardDescription>
                  최근 24시간 내 거래 현황
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentTransactions.map((transaction) => (
                    <div 
                      key={transaction.id}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        {getTransactionIcon(transaction.type)}
                        <div>
                          <div className="font-medium capitalize">
                            {transaction.type === 'withdrawal' ? '출금' : 
                             transaction.type === 'deposit' ? '입금' : 
                             transaction.type === 'energy' ? '에너지' : transaction.type}
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
                        <div className={`text-sm capitalize ${getStatusColor(transaction.status)}`}>
                          {transaction.status === 'completed' ? '완료' : 
                           transaction.status === 'pending' ? '대기' : 
                           transaction.status === 'failed' ? '실패' : transaction.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t">
                  <Button variant="outline" className="w-full">
                    전체 거래 내역 보기
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle>알림 센터</CardTitle>
            <CardDescription>
              최근 시스템 알림 및 경고
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {notifications.slice(0, 3).map((notification) => (
                <div 
                  key={notification.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    notification.read ? 'bg-gray-50 border-gray-200' : 'bg-blue-50 border-blue-200'
                  }`}
                >
                  {getNotificationIcon(notification.type)}
                  <div className="flex-1">
                    <div className="font-medium">{notification.title}</div>
                    <div className="text-sm text-gray-600">{notification.message}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatDate(notification.timestamp)}
                    </div>
                  </div>
                  {!notification.read && (
                    <div className="h-2 w-2 bg-blue-600 rounded-full" />
                  )}
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button variant="outline" className="w-full">
                모든 알림 보기
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Sidebar>
  )
}
