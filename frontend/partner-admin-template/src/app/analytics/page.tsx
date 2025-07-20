'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
// import { useComprehensiveAnalytics } from '@/lib/hooks'

// 모듈화된 컴포넌트들 import
import { AnalyticsHeader } from '@/components/common/PageHeader'
import { AnalyticsStats } from '@/components/common/StatsCards'
import { BreakdownSection, UserTransactionStats } from '@/components/analytics/AnalyticsSections'
import { TrendChartsSection } from '@/components/analytics/TrendChartsSection'

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | '1y'>('30d')
  // const partnerId = 1; // TODO: 실제 파트너 ID 가져오기
  
  // 새로고침 함수
  const handleRefresh = () => {
    window.location.reload();
  };

  // 폴백 데이터 (API가 실패했을 때)
  const fallbackData = {
    revenue: {
      total: 125800.50,
      growth: 15.2,
      breakdown: [
        { name: '거래 수수료', value: 85600.30, percentage: 68.1 },
        { name: '출금 수수료', value: 25400.15, percentage: 20.2 },
        { name: '환전 수수료', value: 14800.05, percentage: 11.7 }
      ]
    },
    costs: {
      total: 68200.25,
      growth: 8.4,
      breakdown: [
        { name: '에너지 비용', value: 35400.10, percentage: 51.9 },
        { name: '운영 비용', value: 18500.08, percentage: 27.1 },
        { name: '인프라 비용', value: 14300.07, percentage: 21.0 }
      ]
    },
    profit: {
      total: 57600.25,
      margin: 45.8,
      growth: 22.1
    },
    users: {
      total: 1250,
      active: 980,
      growth: 12.5,
      retention: 85.6
    },
    transactions: {
      total: 8420,
      volume: 2450000.75,
      avgSize: 291.05,
      growth: 18.7
    }
  };

  return (
    <Sidebar>
      <div className="space-y-6">
        {/* 헤더 */}
        <AnalyticsHeader
          period={period}
          onPeriodChange={setPeriod}
          onRefresh={handleRefresh}
        />

        {/* 핵심 지표 */}
        <AnalyticsStats data={fallbackData} period={period} />

        {/* 수익/비용 분석 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <BreakdownSection
            title="수익 구성"
            data={fallbackData.revenue.breakdown}
            total={fallbackData.revenue.total}
            color="green"
          />
          <BreakdownSection
            title="비용 구성"
            data={fallbackData.costs.breakdown}
            total={fallbackData.costs.total}
            color="red"
          />
        </div>

        {/* 사용자 및 거래 통계 */}
        <UserTransactionStats
          userStats={fallbackData.users}
          transactionStats={fallbackData.transactions}
        />

        {/* 트렌드 차트 */}
        <TrendChartsSection period={period} />
      </div>
    </Sidebar>
  )
}
