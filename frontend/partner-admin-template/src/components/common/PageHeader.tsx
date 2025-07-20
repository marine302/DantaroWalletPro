'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Download, RefreshCw } from 'lucide-react'

interface PageHeaderProps {
  title: string
  description: string
  children?: React.ReactNode
  onRefresh?: () => void
  showDownload?: boolean
  showRefresh?: boolean
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  children,
  onRefresh,
  showDownload = false,
  showRefresh = true
}) => {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{title}</h1>
        <p className="text-gray-600 dark:text-gray-300">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        {children}
        {showRefresh && (
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </Button>
        )}
        {showDownload && (
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            보고서 다운로드
          </Button>
        )}
      </div>
    </div>
  )
}

// 분석 페이지 전용 헤더 (기간 선택 포함)
interface AnalyticsHeaderProps {
  period: '7d' | '30d' | '90d' | '1y'
  onPeriodChange: (period: '7d' | '30d' | '90d' | '1y') => void
  onRefresh: () => void
}

export const AnalyticsHeader: React.FC<AnalyticsHeaderProps> = ({
  period,
  onPeriodChange,
  onRefresh
}) => {
  return (
    <PageHeader
      title="분석 및 보고서"
      description="수익성과 운영 지표를 종합적으로 분석합니다"
      onRefresh={onRefresh}
      showDownload={true}
    >
      <select
        value={period}
        onChange={(e) => onPeriodChange(e.target.value as '7d' | '30d' | '90d' | '1y')}
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-900 dark:text-gray-100"
      >
        <option value="7d">최근 7일</option>
        <option value="30d">최근 30일</option>
        <option value="90d">최근 90일</option>
        <option value="1y">최근 1년</option>
      </select>
    </PageHeader>
  )
}
