'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, LucideIcon, DollarSign, TrendingDown as CostIcon, TrendingUp as GrowthIcon, Activity } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

// 기본 통계 카드
interface StatsCardProps {
  title: string
  value: string | number
  growth?: number
  icon: LucideIcon
  iconColor: string
  subtitle?: string
  isPositiveGrowth?: boolean
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  growth,
  icon: Icon,
  iconColor,
  subtitle,
  isPositiveGrowth = true
}) => {
  const displayValue = typeof value === 'number' ? formatCurrency(value) : value

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {title}
        </CardTitle>
        <Icon className={`h-4 w-4 ${iconColor}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {displayValue}
        </div>
        {growth !== undefined && (
          <div className="flex items-center text-xs mt-1">
            {isPositiveGrowth ? (
              <TrendingUp className="w-3 h-3 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-3 h-3 text-red-500 mr-1" />
            )}
            <span className={isPositiveGrowth ? "text-green-600" : "text-red-600"}>
              {isPositiveGrowth ? '+' : ''}{growth}%
            </span>
            {subtitle && (
              <span className="text-gray-500 dark:text-gray-400 ml-1">{subtitle}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// 분석 페이지용 통계 카드 그리드
interface AnalyticsStatsProps {
  data: {
    revenue: { total: number; growth: number }
    costs: { total: number; growth: number }
    profit: { total: number; margin: number; growth: number }
    transactions: { volume: number; total: number; growth: number }
  }
  period: string
}

export const AnalyticsStats: React.FC<AnalyticsStatsProps> = ({ data, period }) => {
  const getPeriodLabel = (period: string) => {
    switch (period) {
      case '7d': return '최근 7일'
      case '30d': return '최근 30일'
      case '90d': return '최근 90일'
      case '1y': return '최근 1년'
      default: return '최근 30일'
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <StatsCard
        title="총 수익"
        value={data.revenue.total}
        growth={data.revenue.growth}
        icon={DollarSign}
        iconColor="text-green-500"
        subtitle={getPeriodLabel(period)}
        isPositiveGrowth={true}
      />
      <StatsCard
        title="총 비용"
        value={data.costs.total}
        growth={data.costs.growth}
        icon={CostIcon}
        iconColor="text-red-500"
        subtitle={getPeriodLabel(period)}
        isPositiveGrowth={false}
      />
      <StatsCard
        title="순이익"
        value={data.profit.total}
        growth={data.profit.growth}
        icon={GrowthIcon}
        iconColor="text-blue-500"
        subtitle={`마진 ${data.profit.margin}%`}
        isPositiveGrowth={true}
      />
      <StatsCard
        title="거래량"
        value={data.transactions.volume}
        growth={data.transactions.growth}
        icon={Activity}
        iconColor="text-purple-500"
        subtitle={`${data.transactions.total}건`}
        isPositiveGrowth={true}
      />
    </div>
  )
}

// 사용자 관리 페이지용 통계 카드 그리드
interface UserStatsProps {
  data: {
    total_users: number
    active_users: number
    new_users_today: number
    total_balance: number
    average_balance: number
    kyc_approved: number
    kyc_pending: number
  }
  loading: boolean
}

export const UserStats: React.FC<UserStatsProps> = ({ data, loading }) => {
  const LoadingIcon = () => (
    <div className="w-6 h-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
  )

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">전체 사용자</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? <LoadingIcon /> : data.total_users.toLocaleString()}
              </p>
            </div>
            <div className="w-8 h-8 text-blue-600">👥</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">활성 사용자</p>
              <p className="text-2xl font-bold text-green-600">
                {loading ? <LoadingIcon /> : data.active_users.toLocaleString()}
              </p>
            </div>
            <div className="w-8 h-8 text-green-600">✅</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">신규 사용자 (오늘)</p>
              <p className="text-2xl font-bold text-blue-600">
                {loading ? <LoadingIcon /> : `+${data.new_users_today}`}
              </p>
            </div>
            <div className="w-8 h-8 text-blue-600">➕</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">총 잔액</p>
              <p className="text-2xl font-bold text-purple-600">
                {loading ? <LoadingIcon /> : formatCurrency(data.total_balance, 'USDT')}
              </p>
            </div>
            <div className="w-8 h-8 text-purple-600">💰</div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
