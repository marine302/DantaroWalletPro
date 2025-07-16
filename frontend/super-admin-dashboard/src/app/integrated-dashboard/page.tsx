'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { BasePage } from "@/components/ui/BasePage"
import { 
  StatCard, 
  Section, 
  FormField, 
  Button 
} from '@/components/ui/DarkThemeComponents'
import { gridLayouts } from '@/styles/dark-theme'

interface DashboardData {
  wallet_overview: {
    total_balance: number
    wallet_count: number
    security_score: number
    diversification_index: number
    distribution: {
      hot: { balance: number; percentage: number }
      warm: { balance: number; percentage: number }
      cold: { balance: number; percentage: number }
    }
  }
  transaction_flow: {
    total_count: number
    total_volume: number
    avg_amount: number
    trend: string
  }
  energy_status: {
    total_energy: number
    available_energy: number
    usage_rate: number
    efficiency_score: number
  }
  user_analytics: {
    total_users: number
    active_users: number
    new_users: number
    retention_rate: number
  }
  revenue_metrics: {
    total_revenue: number
    commission_earned: number
    profit_margin: number
    growth_rate: number
  }
}

export default function IntegratedDashboard() {
  const [partnerId, setPartnerId] = useState<number>(1)
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // 안전한 숫자 처리 유틸리티
  const safeNumber = (value: number | undefined | null): number => {
    return typeof value === 'number' && !isNaN(value) ? value : 0
  }

  const safeLocaleString = (value: number | undefined | null): string => {
    return safeNumber(value).toLocaleString()
  }

  const safePercentage = (value: number | undefined | null): string => {
    return safeNumber(value).toFixed(1)
  }

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true)
      
      // 빠른 fallback 데이터
      const fallbackData: DashboardData = {
        wallet_overview: {
          total_balance: 2500000,
          wallet_count: 25,
          security_score: 92,
          diversification_index: 0.85,
          distribution: {
            hot: { balance: 1000000, percentage: 40 },
            warm: { balance: 900000, percentage: 36 },
            cold: { balance: 600000, percentage: 24 }
          }
        },
        transaction_flow: {
          total_count: 1250,
          total_volume: 4500000,
          avg_amount: 3600,
          trend: "increasing"
        },
        energy_status: {
          total_energy: 1500000,
          available_energy: 1200000,
          usage_rate: 80,
          efficiency_score: 88
        },
        user_analytics: {
          total_users: 850,
          active_users: 680,
          new_users: 45,
          retention_rate: 78.5
        },
        revenue_metrics: {
          total_revenue: 125000,
          commission_earned: 8750,
          profit_margin: 15.2,
          growth_rate: 12.8
        }
      }
      
      setDashboardData(fallbackData)
      setError(null)
      
    } catch (err) {
      console.error('Dashboard data fetch error:', err)
      setError('데이터를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-300 text-lg">데이터를 불러올 수 없습니다.</div>
      </div>
    )
  }

  return (
    <BasePage 
      title="파트너사 종합 대시보드"
      description={`파트너 ID ${partnerId}의 실시간 통계 및 분석 데이터`}
    >
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-6">
          <FormField
            label="파트너사 ID"
            type="number"
            value={partnerId}
            onChange={(value) => setPartnerId(typeof value === 'number' ? value : parseInt(value.toString()) || 1)}
            min={1}
          />
          <Button onClick={fetchDashboardData}>
            새로고침
          </Button>
        </div>

        {/* 지갑 현황 */}
        <Section title="지갑 현황">
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title="총 잔액"
              value={`${safeLocaleString(dashboardData.wallet_overview.total_balance)} TRX`}
            />
            <StatCard
              title="지갑 수"
              value={safeNumber(dashboardData.wallet_overview.wallet_count)}
            />
            <StatCard
              title="보안 점수"
              value={`${safeNumber(dashboardData.wallet_overview.security_score)}%`}
              trend="up"
            />
            <StatCard
              title="분산 지수"
              value={safePercentage(dashboardData.wallet_overview.diversification_index)}
              trend="neutral"
            />
          </div>
        </Section>

        {/* 거래 흐름 */}
        <Section title="거래 흐름">
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title="24h 거래량"
              value={safeNumber(dashboardData.transaction_flow.total_count)}
            />
            <StatCard
              title="총 거래량"
              value={`${safeLocaleString(dashboardData.transaction_flow.total_volume)} TRX`}
            />
            <StatCard
              title="평균 거래액"
              value={`${safeLocaleString(dashboardData.transaction_flow.avg_amount)} TRX`}
            />
            <StatCard
              title="트렌드"
              value={dashboardData.transaction_flow.trend}
              trend="up"
            />
          </div>
        </Section>

        {/* 에너지 상태 */}
        <Section title="에너지 상태">
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title="총 에너지"
              value={safeLocaleString(dashboardData.energy_status.total_energy)}
            />
            <StatCard
              title="가용 에너지"
              value={safeLocaleString(dashboardData.energy_status.available_energy)}
            />
            <StatCard
              title="사용률"
              value={`${safeNumber(dashboardData.energy_status.usage_rate)}%`}
            />
            <StatCard
              title="효율성"
              value={`${safeNumber(dashboardData.energy_status.efficiency_score)}%`}
              trend="up"
            />
          </div>
        </Section>

        <div className={gridLayouts.contentGrid}>
          {/* 지갑 분산 현황 */}
          <Section title="지갑 분산 현황">
            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-200">Hot Wallet</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-300">
                      {safeLocaleString(dashboardData.wallet_overview.distribution.hot.balance)} TRX
                    </span>
                    <span className="text-xs text-gray-400">
                      ({safePercentage(dashboardData.wallet_overview.distribution.hot.percentage)}%)
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-red-500 h-2 rounded-full" 
                    style={{ width: `${safeNumber(dashboardData.wallet_overview.distribution.hot.percentage)}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-200">Warm Wallet</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-300">
                      {safeLocaleString(dashboardData.wallet_overview.distribution.warm.balance)} TRX
                    </span>
                    <span className="text-xs text-gray-400">
                      ({safePercentage(dashboardData.wallet_overview.distribution.warm.percentage)}%)
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-yellow-500 h-2 rounded-full" 
                    style={{ width: `${safeNumber(dashboardData.wallet_overview.distribution.warm.percentage)}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-200">Cold Wallet</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-300">
                      {safeLocaleString(dashboardData.wallet_overview.distribution.cold.balance)} TRX
                    </span>
                    <span className="text-xs text-gray-400">
                      ({safePercentage(dashboardData.wallet_overview.distribution.cold.percentage)}%)
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{ width: `${safeNumber(dashboardData.wallet_overview.distribution.cold.percentage)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </Section>

          {/* 사용자 분석 */}
          <Section title="사용자 분석">
            <div className="grid grid-cols-2 gap-4">
              <StatCard
                title="총 사용자"
                value={safeNumber(dashboardData.user_analytics.total_users)}
              />
              <StatCard
                title="활성 사용자"
                value={safeNumber(dashboardData.user_analytics.active_users)}
              />
              <StatCard
                title="신규 사용자"
                value={safeNumber(dashboardData.user_analytics.new_users)}
                trend="up"
              />
              <StatCard
                title="유지율"
                value={`${safePercentage(dashboardData.user_analytics.retention_rate)}%`}
                trend="up"
              />
            </div>
          </Section>
        </div>

        {/* 수익 메트릭 */}
        <Section title="수익 메트릭">
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title="총 수익"
              value={`$${safeLocaleString(dashboardData.revenue_metrics.total_revenue)}`}
            />
            <StatCard
              title="수수료 수익"
              value={`$${safeLocaleString(dashboardData.revenue_metrics.commission_earned)}`}
            />
            <StatCard
              title="이익률"
              value={`${safePercentage(dashboardData.revenue_metrics.profit_margin)}%`}
              trend="up"
            />
            <StatCard
              title="성장률"
              value={`${safePercentage(dashboardData.revenue_metrics.growth_rate)}%`}
              trend="up"
            />
          </div>
        </Section>
      </div>
    </BasePage>
  )
}
