'use client'

import React from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { 
  Battery, 
  Zap, 
  TrendingUp, 
  Clock,
  AlertTriangle,
  ArrowRight,
  Info
} from 'lucide-react'
import Link from 'next/link'

export default function EnergyPage() {
  // TODO: 실제 파트너의 에너지 할당 및 사용 현황 데이터를 가져와야 함
  
  // Mock 데이터 - HQ 기반 에너지 할당 현황
  const energyAllocation = {
    partner_id: 'partner_001',
    allocated_amount: 50000, // 할당받은 총 에너지
    used_amount: 23500, // 사용한 에너지
    remaining_amount: 26500, // 남은 에너지
    rental_end_time: '2024-07-30T23:59:59Z',
    current_rate: 0.00035, // TRX per energy unit
    status: 'active' as const
  }

  const usagePercentage = (energyAllocation.used_amount / energyAllocation.allocated_amount) * 100
  const remainingHours = Math.floor((new Date(energyAllocation.rental_end_time).getTime() - new Date().getTime()) / (1000 * 60 * 60))

  return (
    <Sidebar>
      <div className="space-y-6">
        {/* 페이지 헤더 */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">에너지 풀 관리</h1>
          <p className="text-muted-foreground">
            현재 할당받은 에너지 풀의 사용 현황 및 상태를 모니터링합니다
          </p>
        </div>

        {/* HQ 렌탈 시스템 안내 */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>HQ 기반 에너지 렌탈 시스템</AlertTitle>
          <AlertDescription>
            본사(HQ)에서 렌탈한 에너지는 사용자 출금 시 자동으로 소모됩니다. 
            사용자는 출금 수수료를 USDT로 지불하며, 파트너사는 에너지 비용과 수수료 수입의 차익을 얻습니다.
            <Link href="/energy-rental" className="ml-1 text-blue-600 hover:underline">
              추가 에너지 렌탈
            </Link>
          </AlertDescription>
        </Alert>

        {/* 현재 에너지 할당 현황 */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">할당받은 에너지</CardTitle>
              <Battery className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{energyAllocation.allocated_amount.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">총 에너지 용량</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">사용한 에너지</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{energyAllocation.used_amount.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                사용률 {usagePercentage.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">남은 에너지</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{energyAllocation.remaining_amount.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                {(100 - usagePercentage).toFixed(1)}% 남음
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">렌탈 종료까지</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{remainingHours}시간</div>
              <p className="text-xs text-muted-foreground">
                {new Date(energyAllocation.rental_end_time).toLocaleDateString()}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 에너지 사용량 진행 상황 */}
        <Card>
          <CardHeader>
            <CardTitle>에너지 사용 현황</CardTitle>
            <CardDescription>
              사용자 출금 요청시 소모된 에너지 현황입니다. 각 출금마다 에너지가 소모되며, 사용자로부터 USDT 수수료를 받습니다.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">사용량</span>
                <span className="text-sm text-muted-foreground">
                  {energyAllocation.used_amount.toLocaleString()} / {energyAllocation.allocated_amount.toLocaleString()}
                </span>
              </div>
              <Progress value={usagePercentage} className="w-full" />
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <Badge variant={energyAllocation.status === 'active' ? 'default' : 'secondary'}>
                  {energyAllocation.status === 'active' ? '활성' : '비활성'}
                </Badge>
                <span className="text-muted-foreground">
                  요금: {energyAllocation.current_rate} TRX/단위
                </span>
              </div>
              
              {usagePercentage > 80 && (
                <div className="flex items-center space-x-1 text-orange-600">
                  <AlertTriangle className="h-4 w-4" />
                  <span>에너지 부족 주의</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 액션 버튼들 */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/energy-rental">
            <Button className="w-full sm:w-auto">
              추가 에너지 렌탈
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          
          <Link href="/withdrawals">
            <Button variant="outline" className="w-full sm:w-auto">
              출금 관리 보기
            </Button>
          </Link>
          
          <Link href="/analytics">
            <Button variant="outline" className="w-full sm:w-auto">
              상세 분석 보기
            </Button>
          </Link>
        </div>

        {/* 비즈니스 모델 설명 */}
        <Card>
          <CardHeader>
            <CardTitle>💰 수익 구조</CardTitle>
            <CardDescription>
              에너지 렌탈과 출금 수수료의 관계
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl mb-2">🏢</div>
                <div className="font-medium">HQ 에너지 렌탈</div>
                <div className="text-sm text-muted-foreground">비용: {energyAllocation.current_rate} TRX/단위</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl mb-2">👤</div>
                <div className="font-medium">사용자 출금 수수료</div>
                <div className="text-sm text-muted-foreground">USDT로 수취</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl mb-2">💎</div>
                <div className="font-medium">파트너 수익</div>
                <div className="text-sm text-muted-foreground">수수료 - 에너지 비용</div>
              </div>
            </div>
            <div className="text-sm text-center text-muted-foreground mt-4">
              사용자 출금 시 → 에너지 소모 → 수수료 수입 → 파트너 수익 창출
            </div>
          </CardContent>
        </Card>

        {/* 에너지 부족 경고 */}
        {usagePercentage > 90 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>에너지 부족 경고</AlertTitle>
            <AlertDescription>
              할당받은 에너지의 90% 이상을 사용했습니다. 
              서비스 중단을 방지하기 위해 추가 에너지 렌탈을 고려해주세요.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </Sidebar>
  )
}
