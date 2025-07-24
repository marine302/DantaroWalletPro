'use client';

import { useI18n } from '@/contexts/I18nContext';
import React, { useState, useEffect, useCallback } from 'react'
import BasePage from "@/components/ui/BasePage"
import {
  StatCard,
  Section,
  FormField,
  Button
} from '@/components/ui/DarkThemeComponents'
import { gridLayouts } from '@/styles/dark-theme'
import { withRBAC } from '@/components/auth/withRBAC'
import {
  TransactionTrendChart,
  VolumeAreaChart,
  WalletDistributionChart,
  RevenueBarChart,
  generateTransactionTrendData,
  generateWalletDistributionData
} from '@/components/charts/DashboardCharts'

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

function IntegratedDashboard() {
  const { t } = useI18n()
  const [partnerId, setPartnerId] = useState<number>(1)
  const [partners, setPartners] = useState<{id: number, name: string}[]>([])
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // 파트너 목록 가져오기 (슈퍼 어드민용)
  const _fetchPartners = useCallback(async () => {
    try {
      // TODO: 실제 API 연동
      // const _response = await fetch('/api/partners/list', {
      //   headers: { 'Authorization': `Bearer ${token}` }
      // })
      // const _partners = await response.json()

      // 임시 목 데이터 (파트너 어드민 시스템과 연동 예정)
      const _mockPartners = [
        { id: 1, name: "DantaroExchange" },
        { id: 2, name: "CryptoLink Korea" },
        { id: 3, name: "BlockChain Ventures" },
        { id: 4, name: "FinTech Solutions" }
      ]
      setPartners(mockPartners)
    } catch (error) {
      console.error('파트너 목록 가져오기 실패:', error)
    }
  }, [])

  useEffect(() => {
    fetchPartners()
  }, [fetchPartners])

  // 안전한 숫자 처리 유틸리티
  const _safeNumber = (value: number | undefined | null): number => {
    return typeof value === 'number' && !isNaN(value) ? value : 0
  }

  const _safeLocaleString = (value: number | undefined | null): string => {
    return safeNumber(value).toLocaleString()
  }

  const _safePercentage = (value: number | undefined | null): string => {
    return safeNumber(value).toFixed(1)
  }

  const _fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // 실제 API 호출 시도
      const _apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      let response: Response

      try {
        response = await fetch(`${apiUrl}/api/v1/integrated-dashboard/dashboard/${partnerId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const _data = await response.json()
          setDashboardData(data)
          return
        }
      } catch (apiError) {
        console.log('API 호출 실패, fallback 데이터 사용:', apiError)
      }

      // Fallback: mock 서버 또는 정적 데이터
      try {
        response = await fetch(`http://localhost:3001/api/integrated-dashboard/${partnerId}`)
        if (response.ok) {
          const _data = await response.json()
          setDashboardData(data)
          return
        }
      } catch (mockError) {
        console.log('Mock 서버 호출 실패, 정적 데이터 사용:', mockError)
      }

      // 최종 fallback 데이터
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

    } catch (err) {
      console.error('Dashboard data fetch error:', err)
      setError(t.integratedDashboard.fetchError)
    } finally {
      setLoading(false)
    }
  }, [partnerId, t.integratedDashboard.fetchError])

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
        <div className="text-gray-300 text-lg">{t.integratedDashboard.noData}</div>
      </div>
    )
  }

  const _handlePartnerChange = (newPartnerId: number) => {
    setPartnerId(newPartnerId)
    // 파트너 변경 시 자동으로 데이터 새로고침
    fetchDashboardData()
  }

  const _headerActions = (
    <div className="flex items-center gap-4">
      {/* 파트너 선택 드롭다운 */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-300">파트너 선택:</label>
        <select
          value={partnerId}
          onChange={(e) => handlePartnerChange(Number(e.target.value))}
          className="px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {partners.map(partner => (
            <option key={partner.id} value={partner.id}>
              {partner.name}
            </option>
          ))}
        </select>
      </div>
      <Button onClick={fetchDashboardData}>
        새로고침
      </Button>
    </div>
  )

  return (
    <BasePage
      title={t.integratedDashboard.title}
      description={`${partners.find(p => p.id === partnerId)?.name || `파트너 ${partnerId}`}의 상세 분석 대시보드`}
      headerActions={headerActions}
    >
      <div className="space-y-6">

        {/* 지갑 현황 */}
        <Section title={t.integratedDashboard.sections.walletOverview}>
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title={t.integratedDashboard.walletOverview.totalBalance}
              value={`${safeLocaleString(dashboardData.wallet_overview.total_balance)} TRX`}
            />
            <StatCard
              title={t.integratedDashboard.walletOverview.walletCount}
              value={safeNumber(dashboardData.wallet_overview.wallet_count)}
            />
            <StatCard
              title={t.integratedDashboard.walletOverview.securityScore}
              value={`${safeNumber(dashboardData.wallet_overview.security_score)}%`}
              trend="up"
            />
            <StatCard
              title={t.integratedDashboard.walletOverview.diversificationIndex}
              value={safePercentage(dashboardData.wallet_overview.diversification_index)}
              trend="neutral"
            />
          </div>
        </Section>

        {/* 거래 흐름 */}
        <Section title={t.integratedDashboard.sections.transactionFlow}>
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title={t.integratedDashboard.transactionFlow.dailyTransactions}
              value={safeNumber(dashboardData.transaction_flow.total_count)}
            />
            <StatCard
              title={t.integratedDashboard.transactionFlow.totalVolume}
              value={`${safeLocaleString(dashboardData.transaction_flow.total_volume)} TRX`}
            />
            <StatCard
              title={t.integratedDashboard.transactionFlow.avgAmount}
              value={`${safeLocaleString(dashboardData.transaction_flow.avg_amount)} TRX`}
            />
            <StatCard
              title={t.integratedDashboard.transactionFlow.trend}
              value={dashboardData.transaction_flow.trend}
              trend="up"
            />
          </div>
        </Section>

        {/* 에너지 상태 */}
        <Section title={t.integratedDashboard.sections.energyStatus}>
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title={t.integratedDashboard.energyStatus.totalEnergy}
              value={safeLocaleString(dashboardData.energy_status.total_energy)}
            />
            <StatCard
              title={t.integratedDashboard.energyStatus.availableEnergy}
              value={safeLocaleString(dashboardData.energy_status.available_energy)}
            />
            <StatCard
              title={t.integratedDashboard.energyStatus.usageRate}
              value={`${safeNumber(dashboardData.energy_status.usage_rate)}%`}
            />
            <StatCard
              title={t.integratedDashboard.energyStatus.efficiency}
              value={`${safeNumber(dashboardData.energy_status.efficiency_score)}%`}
              trend="up"
            />
          </div>
        </Section>

        <div className={gridLayouts.contentGrid}>
          {/* 지갑 분산 현황 */}
          <Section title={t.integratedDashboard.sections.walletDistribution}>
            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-200">{t.integratedDashboard.walletDistribution.hotWallet}</span>
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
                  <span className="text-sm font-medium text-gray-200">{t.integratedDashboard.walletDistribution.warmWallet}</span>
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
                  <span className="text-sm font-medium text-gray-200">{t.integratedDashboard.walletDistribution.coldWallet}</span>
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
          <Section title={t.integratedDashboard.sections.userAnalytics}>
            <div className="grid grid-cols-2 gap-4">
              <StatCard
                title={t.integratedDashboard.userAnalytics.totalUsers}
                value={safeNumber(dashboardData.user_analytics.total_users)}
              />
              <StatCard
                title={t.integratedDashboard.userAnalytics.activeUsers}
                value={safeNumber(dashboardData.user_analytics.active_users)}
              />
              <StatCard
                title={t.integratedDashboard.userAnalytics.newUsers}
                value={safeNumber(dashboardData.user_analytics.new_users)}
                trend="up"
              />
              <StatCard
                title={t.integratedDashboard.userAnalytics.retentionRate}
                value={`${safePercentage(dashboardData.user_analytics.retention_rate)}%`}
                trend="up"
              />
            </div>
          </Section>
        </div>

        {/* 수익 메트릭 */}
        <Section title={t.integratedDashboard.sections.revenueMetrics}>
          <div className={gridLayouts.statsGrid}>
            <StatCard
              title={t.integratedDashboard.revenueMetrics.totalRevenue}
              value={`$${safeLocaleString(dashboardData.revenue_metrics.total_revenue)}`}
            />
            <StatCard
              title={t.integratedDashboard.revenueMetrics.commissionEarned}
              value={`$${safeLocaleString(dashboardData.revenue_metrics.commission_earned)}`}
            />
            <StatCard
              title={t.integratedDashboard.revenueMetrics.profitMargin}
              value={`${safePercentage(dashboardData.revenue_metrics.profit_margin)}%`}
              trend="up"
            />
            <StatCard
              title={t.integratedDashboard.revenueMetrics.growthRate}
              value={`${safePercentage(dashboardData.revenue_metrics.growth_rate)}%`}
              trend="up"
            />
          </div>
        </Section>

        {/* 차트 섹션 예시 */}
        {/* 차트 분석 섹션 */}
        <Section title="상세 분석 차트">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-800 p-4 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">거래량 추세</h3>
              <TransactionTrendChart
                data={generateTransactionTrendData()}
              />
            </div>
            <div className="bg-gray-800 p-4 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">거래 볼륨</h3>
              <VolumeAreaChart
                data={generateTransactionTrendData()}
              />
            </div>
            <div className="bg-gray-800 p-4 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">지갑 분산도</h3>
              <WalletDistributionChart
                data={generateWalletDistributionData()}
              />
            </div>
            <div className="bg-gray-800 p-4 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">수익 추세</h3>
              <RevenueBarChart
                data={generateTransactionTrendData()}
              />
            </div>
          </div>
        </Section>
      </div>
    </BasePage>
  )
}

// Export protected component with RBAC
export default withRBAC(IntegratedDashboard, {
  requiredPermissions: ['partners.view', 'analytics.view']
})
