'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Zap, 
  TrendingUp, 
  Users, 
  DollarSign,
  Loader2,
  AlertTriangle
} from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { useRentEnergy, useExtendRental, useCancelRental } from '@/lib/hooks/useEnergyRentalHooks'
import type { 
  EnergyRentalPlan, 
  EnergyRental, 
  EnergyUsageStats, 
  EnergySupplyStatus
} from '@/types'

interface EnergyRentalManagementSectionProps {
  plans?: EnergyRentalPlan[]
  usage?: EnergyUsageStats
  allocation?: EnergyRental | null
  pools?: EnergySupplyStatus
  system?: {
    status: 'healthy' | 'degraded' | 'outage'
    last_update: string
    issues?: string[]
  }
  isBackendConnected: boolean
}

export function EnergyRentalManagementSection({
  plans = [],
  usage,
  allocation,
  pools,
  system,
  isBackendConnected
}: EnergyRentalManagementSectionProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedPlan, setSelectedPlan] = useState<EnergyRentalPlan | null>(null)
  const [rentalForm, setRentalForm] = useState({
    duration_hours: 24,
    energy_amount: 1000000
  })

  // 뮤테이션 훅들
  const rentEnergyMutation = useRentEnergy()
  const extendRentalMutation = useExtendRental()
  const cancelRentalMutation = useCancelRental()

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge variant="default">활성</Badge>
      case 'expired': return <Badge variant="secondary">만료</Badge>
      case 'cancelled': return <Badge variant="destructive">취소</Badge>
      case 'pending': return <Badge variant="outline">대기</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  const getSystemStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy': return <Badge className="bg-green-100 text-green-800">정상</Badge>
      case 'degraded': return <Badge className="bg-yellow-100 text-yellow-800">성능 저하</Badge>
      case 'outage': return <Badge className="bg-red-100 text-red-800">장애</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  const handleRentEnergy = async () => {
    if (!selectedPlan) return
    
    try {
      await rentEnergyMutation.mutateAsync({
        plan_id: selectedPlan.id,
        duration_hours: rentalForm.duration_hours,
        energy_amount: rentalForm.energy_amount
      })
      setSelectedPlan(null)
      setRentalForm({ duration_hours: 24, energy_amount: 1000000 })
    } catch (error) {
      console.error('Failed to rent energy:', error)
    }
  }

  const handleExtendRental = async (rentalId: string, hours: number) => {
    try {
      await extendRentalMutation.mutateAsync({ rentalId, additionalHours: hours })
    } catch (error) {
      console.error('Failed to extend rental:', error)
    }
  }

  const handleCancelRental = async (rentalId: string) => {
    try {
      await cancelRentalMutation.mutateAsync(rentalId)
    } catch (error) {
      console.error('Failed to cancel rental:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* 백엔드 연결 상태 및 시스템 상태 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">에너지 렌탈 대시보드</h2>
          <p className="text-gray-600">Super Admin에서 에너지를 렌탈하여 사용자에게 제공</p>
        </div>
        
        {system && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">시스템 상태:</span>
            {getSystemStatusBadge(system.status)}
          </div>
        )}
      </div>

      {/* 현재 렌탈 정보 (있는 경우) */}
      {allocation && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-600" />
              현재 에너지 렌탈
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">렌탈 ID</p>
                <p className="font-semibold">{allocation.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">에너지 양</p>
                <p className="font-semibold">{allocation.energy_amount.toLocaleString()} Energy</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">남은 시간</p>
                <p className="font-semibold">{allocation.remaining_hours}시간</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">상태</p>
                {getStatusBadge(allocation.status)}
              </div>
            </div>
            
            <div className="mt-4 flex gap-2">
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleExtendRental(allocation.id, 24)}
                disabled={extendRentalMutation.isPending}
              >
                {extendRentalMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                24시간 연장
              </Button>
              <Button 
                size="sm" 
                variant="destructive"
                onClick={() => handleCancelRental(allocation.id)}
                disabled={cancelRentalMutation.isPending}
              >
                {cancelRentalMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                렌탈 취소
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 에너지 사용 통계 */}
      {usage && (
        <div className="grid gap-6 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Zap className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{usage.total_energy_used.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">총 사용량</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{usage.daily_usage.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">일일 사용량</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <DollarSign className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{formatCurrency(usage.cost_today)}</div>
                  <div className="text-sm text-muted-foreground">오늘 비용</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{usage.efficiency_score}%</div>
                  <div className="text-sm text-muted-foreground">효율성 점수</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="plans">렌탈 플랜</TabsTrigger>
          <TabsTrigger value="pools">에너지 풀 상태</TabsTrigger>
          {!isBackendConnected && <TabsTrigger value="mock">목 데이터</TabsTrigger>}
        </TabsList>

        {/* 개요 탭 */}
        <TabsContent value="overview" className="space-y-4">
          {usage ? (
            <Card>
              <CardHeader>
                <CardTitle>에너지 사용 현황</CardTitle>
                <CardDescription>실시간 에너지 사용량 및 비용 분석</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>일일 사용량</span>
                      <span>{usage.daily_usage.toLocaleString()} / {usage.daily_limit.toLocaleString()}</span>
                    </div>
                    <Progress value={(usage.daily_usage / usage.daily_limit) * 100} />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>월간 사용량</span>
                      <span>{usage.monthly_usage.toLocaleString()} / {usage.monthly_limit.toLocaleString()}</span>
                    </div>
                    <Progress value={(usage.monthly_usage / usage.monthly_limit) * 100} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                사용량 데이터를 불러올 수 없습니다.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* 렌탈 플랜 탭 */}
        <TabsContent value="plans" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {plans.map((plan) => (
              <Card key={plan.id} className={`cursor-pointer transition-colors ${
                selectedPlan?.id === plan.id ? 'ring-2 ring-blue-500' : ''
              }`} onClick={() => setSelectedPlan(plan)}>
                <CardHeader>
                  <CardTitle className="flex justify-between items-center">
                    {plan.name}
                    <Badge variant="outline">{plan.type}</Badge>
                  </CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>에너지량:</span>
                      <span className="font-semibold">{plan.energy_amount.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>기간:</span>
                      <span className="font-semibold">{plan.duration_hours}시간</span>
                    </div>
                    <div className="flex justify-between">
                      <span>비용:</span>
                      <span className="font-semibold">{formatCurrency(plan.cost_per_hour)}/시간</span>
                    </div>
                    {plan.availability && (
                      <div className="flex justify-between">
                        <span>가용성:</span>
                        <Badge variant={plan.availability.is_available ? "default" : "destructive"}>
                          {plan.availability.is_available ? "사용 가능" : "품절"}
                        </Badge>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 에너지 렌탈 폼 */}
          {selectedPlan && (
            <Card>
              <CardHeader>
                <CardTitle>에너지 렌탈 요청</CardTitle>
                <CardDescription>선택한 플랜: {selectedPlan.name}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-medium">대여 기간 (시간)</label>
                    <Input
                      type="number"
                      value={rentalForm.duration_hours}
                      onChange={(e) => setRentalForm(prev => ({
                        ...prev,
                        duration_hours: parseInt(e.target.value) || 24
                      }))}
                      min="1"
                      max="168"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">에너지 양</label>
                    <Input
                      type="number"
                      value={rentalForm.energy_amount}
                      onChange={(e) => setRentalForm(prev => ({
                        ...prev,
                        energy_amount: parseInt(e.target.value) || 1000000
                      }))}
                      min="100000"
                      step="100000"
                    />
                  </div>
                </div>
                
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-2">예상 비용</h4>
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(selectedPlan.cost_per_hour * rentalForm.duration_hours)}
                  </div>
                  <p className="text-sm text-gray-600">
                    {rentalForm.duration_hours}시간 × {formatCurrency(selectedPlan.cost_per_hour)}/시간
                  </p>
                </div>

                <div className="mt-4 flex gap-2">
                  <Button 
                    onClick={handleRentEnergy}
                    disabled={rentEnergyMutation.isPending}
                    className="flex-1"
                  >
                    {rentEnergyMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : null}
                    에너지 렌탈하기
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => setSelectedPlan(null)}
                  >
                    취소
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 에너지 풀 상태 탭 */}
        <TabsContent value="pools" className="space-y-4">
          {pools ? (
            <Card>
              <CardHeader>
                <CardTitle>HQ 에너지 풀 상태</CardTitle>
                <CardDescription>Super Admin이 관리하는 에너지 풀 현황</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-semibold mb-2">전체 용량</h4>
                    <div className="text-2xl font-bold">{pools.total_capacity.toLocaleString()}</div>
                    <Progress value={(pools.available_capacity / pools.total_capacity) * 100} className="mt-2" />
                    <p className="text-sm text-gray-600 mt-1">
                      사용 가능: {pools.available_capacity.toLocaleString()} / {pools.total_capacity.toLocaleString()}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">현재 가격</h4>
                    <div className="text-2xl font-bold text-green-600">{formatCurrency(pools.current_price)}</div>
                    <p className="text-sm text-gray-600">에너지당 시간당 비용</p>
                    {pools.price_trend && (
                      <div className="flex items-center mt-1">
                        <TrendingUp className={`w-4 h-4 mr-1 ${
                          pools.price_trend > 0 ? 'text-red-500' : 'text-green-500'
                        }`} />
                        <span className={`text-sm ${
                          pools.price_trend > 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {pools.price_trend > 0 ? '+' : ''}{pools.price_trend.toFixed(2)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                에너지 풀 상태를 불러올 수 없습니다.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* 목 데이터 탭 (백엔드 연결되지 않았을 때만 표시) */}
        {!isBackendConnected && (
          <TabsContent value="mock" className="space-y-4">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                현재 백엔드에 연결되지 않아 목 데이터를 사용하고 있습니다.
                백엔드 서버가 준비되면 실제 데이터로 자동 전환됩니다.
              </AlertDescription>
            </Alert>
            
            <Card>
              <CardHeader>
                <CardTitle>개발 중 - 목 데이터</CardTitle>
                <CardDescription>백엔드 준비 중이므로 임시 데이터로 UI를 확인할 수 있습니다.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <p>• 렌탈 플랜: {plans.length}개 사용 가능</p>
                  <p>• 현재 할당: {allocation ? '1개 활성' : '없음'}</p>
                  <p>• 에너지 풀 상태: {pools ? '연결됨' : '연결 안됨'}</p>
                  <p>• 시스템 상태: {system?.status || '알 수 없음'}</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}
