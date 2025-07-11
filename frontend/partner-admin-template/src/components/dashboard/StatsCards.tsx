'use client'

import { TrendingUp, TrendingDown, Users, CreditCard, BarChart3, Zap } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DashboardStats } from '@/types'
import { formatCurrency, formatNumber } from '@/lib/utils'

interface StatsCardsProps {
  stats: DashboardStats
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: '총 사용자',
      value: formatNumber(stats.totalUsers),
      change: stats.dailyGrowth,
      changeLabel: '전일 대비',
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: '총 잔액',
      value: formatCurrency(stats.totalBalance),
      change: stats.weeklyGrowth,
      changeLabel: '주간 대비',
      icon: CreditCard,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: '총 거래 건수',
      value: formatNumber(stats.totalTransactions),
      change: stats.dailyGrowth,
      changeLabel: '전일 대비',
      icon: BarChart3,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: '총 수익',
      value: formatCurrency(stats.totalRevenue),
      change: stats.monthlyGrowth,
      changeLabel: '월간 대비',
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <Card key={index} className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {card.title}
            </CardTitle>
            <div className={`h-8 w-8 rounded-full ${card.bgColor} flex items-center justify-center`}>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {card.change >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
              )}
              <span className={card.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                {card.change >= 0 ? '+' : ''}{card.change.toFixed(1)}%
              </span>
              <span className="ml-1">{card.changeLabel}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

interface EnergyPoolCardProps {
  energyPool: {
    totalEnergy: number
    availableEnergy: number
    stakeAmount: number
    freezeAmount: number
    dailyConsumption: number
    efficiency: number
    status: 'active' | 'inactive' | 'warning'
  }
}

export function EnergyPoolCard({ energyPool }: EnergyPoolCardProps) {
  const utilizationRate = ((energyPool.totalEnergy - energyPool.availableEnergy) / energyPool.totalEnergy) * 100

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600'
      case 'warning':
        return 'text-yellow-600'
      case 'inactive':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          에너지 풀 현황
        </CardTitle>
        <div className="h-8 w-8 rounded-full bg-yellow-50 flex items-center justify-center">
          <Zap className="h-4 w-4 text-yellow-600" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">총 에너지</span>
            <span className="font-semibold">{formatNumber(energyPool.totalEnergy)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">사용 가능</span>
            <span className="font-semibold">{formatNumber(energyPool.availableEnergy)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">사용률</span>
            <span className="font-semibold">{utilizationRate.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">상태</span>
            <span className={`font-semibold ${getStatusColor(energyPool.status)}`}>
              {energyPool.status.toUpperCase()}
            </span>
          </div>
          <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-500 to-yellow-500 transition-all duration-300"
              style={{ width: `${utilizationRate}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
