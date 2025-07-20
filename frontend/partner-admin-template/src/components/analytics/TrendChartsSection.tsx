'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  RevenueTrendChart, 
  UserGrowthChart, 
  TransactionVolumeChart,
  generateSampleTrendData
} from '@/components/charts/TrendCharts'

interface TrendChartsSectionProps {
  period: '7d' | '30d' | '90d' | '1y'
}

export const TrendChartsSection: React.FC<TrendChartsSectionProps> = ({ period }) => {
  const getPeriodLabel = (period: string) => {
    switch (period) {
      case '7d': return '최근 7일'
      case '30d': return '최근 30일'
      case '90d': return '최근 90일'
      case '1y': return '최근 1년'
      default: return '최근 30일'
    }
  }

  // 차트용 트렌드 데이터 생성
  const trendData = generateSampleTrendData(period)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-gray-900 dark:text-gray-100">
          트렌드 분석 ({getPeriodLabel(period)})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="revenue" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="revenue">수익/비용 트렌드</TabsTrigger>
            <TabsTrigger value="users">사용자 증가</TabsTrigger>
            <TabsTrigger value="transactions">거래량</TabsTrigger>
          </TabsList>
          
          <TabsContent value="revenue" className="mt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  수익 및 비용 트렌드
                </h3>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded"></div>
                    <span className="text-gray-600 dark:text-gray-300">수익</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded"></div>
                    <span className="text-gray-600 dark:text-gray-300">비용</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded"></div>
                    <span className="text-gray-600 dark:text-gray-300">순이익</span>
                  </div>
                </div>
              </div>
              <RevenueTrendChart data={trendData} period={period} />
            </div>
          </TabsContent>
          
          <TabsContent value="users" className="mt-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                사용자 증가 추이
              </h3>
              <UserGrowthChart data={trendData} period={period} />
            </div>
          </TabsContent>
          
          <TabsContent value="transactions" className="mt-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                거래량 추이
              </h3>
              <TransactionVolumeChart data={trendData} period={period} />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
