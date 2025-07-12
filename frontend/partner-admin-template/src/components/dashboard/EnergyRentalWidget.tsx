'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Zap, DollarSign, TrendingUp, Calendar, Settings } from 'lucide-react'
import { formatCurrency, formatNumber } from '@/lib/utils'

interface EnergyRentalData {
  plan_type: 'subscription' | 'pay_per_use' | 'hybrid'
  subscription_tier: string
  is_active: boolean
  monthly_energy_quota: number
  current_rate: number
  monthly_used: number
  estimated_monthly_cost: number
  daily_consumption: number
  efficiency_score: number
}

interface EnergyRentalWidgetProps {
  className?: string
}

export function EnergyRentalWidget({ className }: EnergyRentalWidgetProps) {
  const [rentalData] = useState<EnergyRentalData>({
    plan_type: 'subscription',
    subscription_tier: 'Standard',
    is_active: true,
    monthly_energy_quota: 1000000,
    current_rate: 0.000420,
    monthly_used: 650000,
    estimated_monthly_cost: 273.0,
    daily_consumption: 21500,
    efficiency_score: 85.5
  })

  const usagePercentage = (rentalData.monthly_used / rentalData.monthly_energy_quota) * 100
  const remainingEnergy = rentalData.monthly_energy_quota - rentalData.monthly_used
  const estimatedDaysRemaining = Math.floor(remainingEnergy / rentalData.daily_consumption)

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-500" />
          에너지 렌탈 현황
        </CardTitle>
        <Badge variant={rentalData.is_active ? 'default' : 'secondary'}>
          {rentalData.subscription_tier}
        </Badge>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 구독 플랜 정보 */}
        {rentalData.plan_type === 'subscription' && (
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">월 할당량</span>
              <span className="font-medium">
                {formatNumber(rentalData.monthly_energy_quota)} 에너지
              </span>
            </div>
            
            <div className="space-y-2">
              <Progress value={usagePercentage} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{formatNumber(rentalData.monthly_used)} 사용</span>
                <span>{usagePercentage.toFixed(1)}% 사용됨</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-1">
                <span className="text-muted-foreground">남은 에너지</span>
                <div className="font-medium text-green-600">
                  {formatNumber(remainingEnergy)}
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-muted-foreground">예상 소진일</span>
                <div className="font-medium text-blue-600">
                  {estimatedDaysRemaining}일 후
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* 실시간 효율성 */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">에너지 효율성</span>
            <div className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-green-500" />
              <span className="text-sm font-medium text-green-600">
                {rentalData.efficiency_score}%
              </span>
            </div>
          </div>
          <Progress value={rentalData.efficiency_score} className="h-1.5" />
        </div>
        
        {/* 비용 정보 */}
        <div className="border-t pt-4 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">현재 단가</span>
            <span className="font-medium">
              {rentalData.current_rate} TRX/에너지
            </span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">일일 평균 소비량</span>
            <span className="font-medium">
              {formatNumber(rentalData.daily_consumption)} 에너지
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">이번 달 예상 비용</span>
            <div className="text-right">
              <div className="font-semibold text-lg flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                {formatCurrency(rentalData.estimated_monthly_cost)}
              </div>
              <div className="text-xs text-muted-foreground">
                TRX 기준
              </div>
            </div>
          </div>
        </div>
        
        {/* 액션 버튼 */}
        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Calendar className="w-3 h-3 mr-1" />
            사용 내역
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <Settings className="w-3 h-3 mr-1" />
            플랜 변경
          </Button>
        </div>
        
        {/* 알림 메시지 */}
        {usagePercentage > 80 && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-yellow-800">
                에너지 사용량이 80%를 초과했습니다. 플랜 업그레이드를 고려해보세요.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default EnergyRentalWidget
