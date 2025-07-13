'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Users, 
  Activity,
  BarChart3,
  Download,
  RefreshCw,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { useComprehensiveAnalytics } from '@/lib/hooks'

interface AnalyticsData {
  revenue: {
    total: number
    growth: number
    breakdown: Array<{ name: string; value: number; percentage: number }>
  }
  costs: {
    total: number
    growth: number
    breakdown: Array<{ name: string; value: number; percentage: number }>
  }
  profit: {
    total: number
    margin: number
    growth: number
  }
  users: {
    total: number
    active: number
    growth: number
    retention: number
  }
  transactions: {
    total: number
    volume: number
    avgSize: number
    growth: number
  }
}

interface BreakdownItem {
  name: string;
  value: number;
  percentage: number;
}

// TODO: API 타입과 UI 타입을 일치시킨 후 사용
// interface ApiAnalyticsData {
//   revenue?: {
//     total: number;
//     daily: Array<{ date: string; amount: number }>;
//     growth: number;
//   };
//   costs?: {
//     total: number;
//     breakdown: Array<{ category: string; amount: number }>;
//   };
//   profit?: {
//     total: number;
//     margin: number;
//   };
//   users?: {
//     total: number;
//     active: number;
//     growth: number;
//   };
//   transactions?: {
//     total: number;
//     volume: number;
//     daily: Array<{ date: string; count: number; volume: number }>;
//   };
// }

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | '1y'>('30d')
  
  // 실제 API 데이터 사용 (현재는 타입 불일치로 fallback 사용)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { data: _analyticsData, loading, error } = useComprehensiveAnalytics(period);

  // 새로고침 함수
  const handleRefresh = () => {
    // 페이지 새로고침
    window.location.reload();
  };

  // 폴백 데이터 (API가 실패했을 때)
  const fallbackData: AnalyticsData = {
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

  // 데이터 매핑 함수 (현재는 API 타입 불일치로 인해 fallback 데이터 사용)
  const mapApiDataToAnalytics = (): AnalyticsData => {
    // TODO: API 타입이 일치하도록 수정한 후 실제 데이터 사용
    return fallbackData;
  };

  const currentData = mapApiDataToAnalytics();

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case '7d': return '최근 7일'
      case '30d': return '최근 30일'
      case '90d': return '최근 90일'
      case '1y': return '최근 1년'
      default: return '최근 30일'
    }
  };

  // 로딩 상태
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="text-lg">분석 데이터를 불러오는 중...</span>
        </div>
      </div>
    );
  }

  // 오류 상태
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-semibold text-red-600">데이터 로딩 오류</h2>
          <p className="text-gray-600">분석 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.</p>
          <p className="text-sm text-gray-500">오류: {error.message}</p>
          <Button onClick={() => window.location.reload()} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            다시 시도
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-foreground">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">분석 및 보고서</h1>
          <p className="text-gray-600 dark:text-gray-300">수익성과 운영 지표를 종합적으로 분석합니다</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as '7d' | '30d' | '90d' | '1y')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-foreground"
          >
            <option value="7d">최근 7일</option>
            <option value="30d">최근 30일</option>
            <option value="90d">최근 90일</option>
            <option value="1y">최근 1년</option>
          </select>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </Button>
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            보고서 다운로드
          </Button>
        </div>
      </div>

      {/* 핵심 지표 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">총 수익</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {formatCurrency(currentData.revenue.total)}
            </div>
            <div className="flex items-center text-xs">
              <TrendingUp className="w-3 h-3 text-green-500 mr-1" />
              <span className="text-green-600">+{currentData.revenue.growth}%</span>
              <span className="text-muted-foreground ml-1">{getPeriodLabel(period)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">총 비용</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {formatCurrency(currentData.costs.total)}
            </div>
            <div className="flex items-center text-xs">
              <TrendingUp className="w-3 h-3 text-red-500 mr-1" />
              <span className="text-red-600">+{currentData.costs.growth}%</span>
              <span className="text-muted-foreground ml-1">{getPeriodLabel(period)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">순이익</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {formatCurrency(currentData.profit.total)}
            </div>
            <div className="flex items-center text-xs">
              <TrendingUp className="w-3 h-3 text-green-500 mr-1" />
              <span className="text-green-600">+{currentData.profit.growth}%</span>
              <span className="text-muted-foreground ml-1">마진 {currentData.profit.margin}%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-foreground">거래량</CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {formatCurrency(currentData.transactions.volume)}
            </div>
            <div className="flex items-center text-xs">
              <TrendingUp className="w-3 h-3 text-green-500 mr-1" />
              <span className="text-green-600">+{currentData.transactions.growth}%</span>
              <span className="text-muted-foreground ml-1">{currentData.transactions.total}건</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 수익 분석 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">수익 구성</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {currentData.revenue.breakdown.map((item: BreakdownItem, index: number) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">{item.name}</span>
                    <div className="text-right">
                      <span className="font-medium text-foreground">{formatCurrency(item.value)}</span>
                      <span className="text-xs text-gray-500 ml-2">({item.percentage.toFixed(1)}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${item.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-green-800 dark:text-green-300">총 수익</span>
                <span className="text-lg font-bold text-green-900 dark:text-green-200">
                  {formatCurrency(currentData.revenue.total)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">비용 구성</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {currentData.costs.breakdown.map((item: BreakdownItem, index: number) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">{item.name}</span>
                    <div className="text-right">
                      <span className="font-medium text-foreground">{formatCurrency(item.value)}</span>
                      <span className="text-xs text-gray-500 ml-2">({item.percentage.toFixed(1)}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-red-600 h-2 rounded-full"
                      style={{ width: `${item.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-red-800 dark:text-red-300">총 비용</span>
                <span className="text-lg font-bold text-red-900 dark:text-red-200">
                  {formatCurrency(currentData.costs.total)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 사용자 및 거래 통계 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">사용자 통계</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-300">총 사용자</p>
                  <p className="text-2xl font-bold text-foreground">{currentData.users.total.toLocaleString()}</p>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>

              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-300">활성 사용자</p>
                  <p className="text-2xl font-bold text-foreground">{currentData.users.active.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <Badge className="bg-green-100 text-green-800">
                    {((currentData.users.active / currentData.users.total) * 100).toFixed(1)}%
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-blue-600 dark:text-blue-300">성장률</p>
                  <p className="text-lg font-bold text-blue-900 dark:text-blue-200">
                    +{currentData.users.growth}%
                  </p>
                </div>
                <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <p className="text-sm text-purple-600 dark:text-purple-300">리텐션</p>
                  <p className="text-lg font-bold text-purple-900 dark:text-purple-200">
                    {currentData.users.retention}%
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">거래 통계</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-300">총 거래 수</p>
                  <p className="text-2xl font-bold text-foreground">{currentData.transactions.total.toLocaleString()}</p>
                </div>
                <Activity className="w-8 h-8 text-green-500" />
              </div>

              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-300">총 거래량</p>
                  <p className="text-2xl font-bold text-foreground">
                    {formatCurrency(currentData.transactions.volume)}
                  </p>
                </div>
                <div className="text-right">
                  <Badge className="bg-blue-100 text-blue-800">
                    +{currentData.transactions.growth}%
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-sm text-green-600 dark:text-green-300">평균 거래액</p>
                  <p className="text-lg font-bold text-green-900 dark:text-green-200">
                    {formatCurrency(currentData.transactions.avgSize)}
                  </p>
                </div>
                <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                  <p className="text-sm text-orange-600 dark:text-orange-300">일평균 거래</p>
                  <p className="text-lg font-bold text-orange-900 dark:text-orange-200">
                    {Math.round(currentData.transactions.total / 30)}건
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 시계열 데이터 요약 (차트는 나중에 추가) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground">일별 트렌드 ({getPeriodLabel(period)})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">차트 컴포넌트가 구현될 예정입니다</p>
            <p className="text-sm">수익, 비용, 사용자, 거래량의 시계열 차트가 표시됩니다</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
