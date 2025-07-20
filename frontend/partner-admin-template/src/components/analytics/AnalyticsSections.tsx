'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Users, Activity } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

// 수익/비용 구성 분석
interface BreakdownItem {
  name: string
  value: number
  percentage: number
}

interface BreakdownSectionProps {
  title: string
  data: BreakdownItem[]
  total: number
  color: 'green' | 'red'
}

export const BreakdownSection: React.FC<BreakdownSectionProps> = ({
  title,
  data,
  total,
  color
}) => {
  const colorClasses = {
    green: {
      bg: 'bg-green-600',
      text: 'text-green-800 dark:text-green-300',
      bgLight: 'bg-green-50 dark:bg-green-900/20',
      totalText: 'text-green-900 dark:text-green-200'
    },
    red: {
      bg: 'bg-red-600',
      text: 'text-red-800 dark:text-red-300',
      bgLight: 'bg-red-50 dark:bg-red-900/20',
      totalText: 'text-red-900 dark:text-red-200'
    }
  }

  const colors = colorClasses[color]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-gray-900 dark:text-gray-100">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-300">{item.name}</span>
                <div className="text-right">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {formatCurrency(item.value)}
                  </span>
                  <span className="text-xs text-gray-500 ml-2">
                    ({item.percentage.toFixed(1)}%)
                  </span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`${colors.bg} h-2 rounded-full`}
                  style={{ width: `${item.percentage}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>

        <div className={`mt-6 p-4 ${colors.bgLight} rounded-lg`}>
          <div className="flex items-center justify-between">
            <span className={`text-sm font-medium ${colors.text}`}>총 {title.replace(' 구성', '')}</span>
            <span className={`text-lg font-bold ${colors.totalText}`}>
              {formatCurrency(total)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// 사용자/거래 통계 섹션
interface UserStatsData {
  total: number
  active: number
  growth: number
  retention: number
}

interface TransactionStatsData {
  total: number
  volume: number
  avgSize: number
  growth: number
}

interface StatsBoxProps {
  userStats: UserStatsData
  transactionStats: TransactionStatsData
}

export const UserTransactionStats: React.FC<StatsBoxProps> = ({
  userStats,
  transactionStats
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 사용자 통계 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-gray-100">사용자 통계</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">총 사용자</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {userStats.total.toLocaleString()}
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>

            <div className="flex justify-between items-center p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">활성 사용자</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {userStats.active.toLocaleString()}
                </p>
              </div>
              <div className="text-right">
                <Badge className="bg-green-100 text-green-800">
                  {((userStats.active / userStats.total) * 100).toFixed(1)}%
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-blue-600 dark:text-blue-300">성장률</p>
                <p className="text-lg font-bold text-blue-900 dark:text-blue-200">
                  +{userStats.growth}%
                </p>
              </div>
              <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm text-purple-600 dark:text-purple-300">리텐션</p>
                <p className="text-lg font-bold text-purple-900 dark:text-purple-200">
                  {userStats.retention}%
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 거래 통계 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-gray-100">거래 통계</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">총 거래 수</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {transactionStats.total.toLocaleString()}
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>

            <div className="flex justify-between items-center p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">총 거래량</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(transactionStats.volume)}
                </p>
              </div>
              <div className="text-right">
                <Badge className="bg-blue-100 text-blue-800">
                  +{transactionStats.growth}%
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm text-green-600 dark:text-green-300">평균 거래액</p>
                <p className="text-lg font-bold text-green-900 dark:text-green-200">
                  {formatCurrency(transactionStats.avgSize)}
                </p>
              </div>
              <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <p className="text-sm text-orange-600 dark:text-orange-300">일평균 거래</p>
                <p className="text-lg font-bold text-orange-900 dark:text-orange-200">
                  {Math.round(transactionStats.total / 30)}건
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
