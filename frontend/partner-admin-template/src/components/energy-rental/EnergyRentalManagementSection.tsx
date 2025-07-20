'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/common/PageHeader'
import { 
  Zap, 
  TrendingUp, 
  Users, 
  DollarSign,
  Settings,
  Play,
  Pause,
  Plus
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

interface EnergyOverview {
  total_energy_capacity: number
  average_utilization: number
  total_revenue_today: number
  active_rentals: number
  total_revenue_month: number
  profit_margin: number
  total_energy_rented: number
}

interface EnergyPool {
  id: string
  name: string
  status: string
  created_at: string
  utilization_rate: number
  available_energy: number
  total_energy: number
  staked_trx: number
  rental_rate: number
  daily_revenue: number
  auto_rebalance: boolean
}

interface EnergyTransaction {
  id: string
  customer_name: string
  energy_amount: number
  duration_hours: number
  total_cost: number
  start_time: string
  end_time: string
  status: string
}

interface EnergyRentalManagementSectionProps {
  overview: EnergyOverview
  pools: EnergyPool[]
  transactions: EnergyTransaction[]
  onCreatePool: () => void
  onTogglePool: (poolId: string, currentStatus: string) => void
  onRefresh: () => void
}

export function EnergyRentalManagementSection({
  overview,
  pools,
  transactions,
  onCreatePool,
  onTogglePool,
  onRefresh
}: EnergyRentalManagementSectionProps) {
  const [activeTab, setActiveTab] = useState('pools')
  const [newPoolForm, setNewPoolForm] = useState({
    name: '',
    stake_amount: '',
    rental_rate: ''
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge variant="default">활성</Badge>
      case 'paused': return <Badge variant="secondary">일시정지</Badge>
      case 'stopped': return <Badge variant="destructive">중단</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  const getTransactionStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge variant="default">대여중</Badge>
      case 'completed': return <Badge variant="secondary">완료</Badge>
      case 'pending': return <Badge variant="outline">대기</Badge>
      case 'failed': return <Badge variant="destructive">실패</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  const handleCreatePool = () => {
    onCreatePool()
    setNewPoolForm({ name: '', stake_amount: '', rental_rate: '' })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="에너지 렌탈 서비스"
        description="TRX 스테이킹을 통한 에너지 생성 및 자동 렌탈 서비스 관리"
        onRefresh={onRefresh}
      >
        <Button onClick={onCreatePool}>
          <Plus className="w-4 h-4 mr-2" />
          새 풀 생성
        </Button>
      </PageHeader>

      {/* 개요 통계 */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Zap className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{overview.total_energy_capacity.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">총 에너지 용량</div>
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
                <div className="text-2xl font-bold">{overview.average_utilization.toFixed(1)}%</div>
                <div className="text-sm text-muted-foreground">평균 이용률</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{formatCurrency(overview.total_revenue_today, 'TRX')}</div>
                <div className="text-sm text-muted-foreground">오늘 수익</div>
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
                <div className="text-2xl font-bold">{overview.active_rentals}</div>
                <div className="text-sm text-muted-foreground">활성 렌탈</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 수익성 개요 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            수익성 분석
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{overview.profit_margin.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">수익률</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{formatCurrency(overview.total_revenue_month, 'TRX')}</div>
              <div className="text-sm text-muted-foreground">월간 수익</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{(overview.total_energy_rented / overview.total_energy_capacity * 100).toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">전체 이용률</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="pools">에너지 풀</TabsTrigger>
          <TabsTrigger value="rentals">렌탈 현황</TabsTrigger>
          <TabsTrigger value="analytics">분석</TabsTrigger>
        </TabsList>

        {/* 에너지 풀 탭 */}
        <TabsContent value="pools" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {pools.map((pool) => (
              <Card key={pool.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{pool.name}</CardTitle>
                    {getStatusBadge(pool.status)}
                  </div>
                  <CardDescription>
                    생성일: {formatDate(pool.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* 에너지 사용량 */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">에너지 사용률</span>
                      <span className="text-sm text-muted-foreground">
                        {pool.utilization_rate.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={pool.utilization_rate} className="w-full" />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>사용가능: {pool.available_energy.toLocaleString()}</span>
                      <span>총 용량: {pool.total_energy.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* 기본 정보 */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">스테이킹 TRX</div>
                      <div className="font-medium">{pool.staked_trx.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">렌탈 요금</div>
                      <div className="font-medium">{pool.rental_rate} TRX/hour</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">일일 수익</div>
                      <div className="font-medium text-green-600">{formatCurrency(pool.daily_revenue, 'TRX')}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">자동 리밸런싱</div>
                      <div className="text-xs">{pool.auto_rebalance ? '활성' : '비활성'}</div>
                    </div>
                  </div>

                  {/* 액션 버튼들 */}
                  <div className="flex space-x-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onTogglePool(pool.id, pool.status)}
                      className="flex-1"
                    >
                      {pool.status === 'active' ? (
                        <>
                          <Pause className="w-3 h-3 mr-1" />
                          일시정지
                        </>
                      ) : (
                        <>
                          <Play className="w-3 h-3 mr-1" />
                          활성화
                        </>
                      )}
                    </Button>
                    <Button variant="outline" size="sm">
                      <Settings className="w-3 h-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* 새 풀 생성 카드 */}
            <Card className="border-dashed">
              <CardContent className="p-6">
                <div className="text-center mb-4">
                  <Zap className="w-12 h-12 mx-auto mb-2 text-muted-foreground" />
                  <h3 className="font-medium">새 에너지 풀 생성</h3>
                  <p className="text-sm text-muted-foreground">TRX 스테이킹으로 에너지 풀을 생성하세요</p>
                </div>
                
                <div className="space-y-3">
                  <Input
                    placeholder="풀 이름"
                    value={newPoolForm.name}
                    onChange={(e) => setNewPoolForm({...newPoolForm, name: e.target.value})}
                  />
                  <Input
                    placeholder="스테이킹 TRX 수량"
                    type="number"
                    value={newPoolForm.stake_amount}
                    onChange={(e) => setNewPoolForm({...newPoolForm, stake_amount: e.target.value})}
                  />
                  <Input
                    placeholder="렌탈 요금 (TRX/hour)"
                    type="number"
                    step="0.01"
                    value={newPoolForm.rental_rate}
                    onChange={(e) => setNewPoolForm({...newPoolForm, rental_rate: e.target.value})}
                  />
                  <Button 
                    onClick={handleCreatePool}
                    disabled={!newPoolForm.name || !newPoolForm.stake_amount}
                    className="w-full"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    풀 생성
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 렌탈 현황 탭 */}
        <TabsContent value="rentals" className="space-y-6">
          <div className="space-y-4">
            {transactions.map((transaction) => (
              <Card key={transaction.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="font-medium">{transaction.customer_name}</h3>
                        {getTransactionStatusBadge(transaction.status)}
                      </div>
                      
                      <div className="grid gap-4 md:grid-cols-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">에너지 수량</div>
                          <div className="font-medium">{transaction.energy_amount.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">렌탈 기간</div>
                          <div className="font-medium">{transaction.duration_hours}시간</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">총 비용</div>
                          <div className="font-medium">{formatCurrency(transaction.total_cost, 'TRX')}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">시작 시간</div>
                          <div className="font-medium">{formatDate(transaction.start_time)}</div>
                        </div>
                      </div>

                      {transaction.status === 'active' && transaction.end_time && (
                        <div className="mt-3 p-2 bg-blue-50 rounded">
                          <div className="text-sm text-blue-800">
                            종료 예정: {formatDate(transaction.end_time)}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="ml-4">
                      <Button variant="outline" size="sm">
                        상세보기
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* 분석 탭 */}
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                성능 분석 및 최적화 제안
              </CardTitle>
              <CardDescription>
                AI 기반 분석을 통한 수익성 최적화 방안을 제공합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>상세 분석 차트가 여기에 표시됩니다</p>
                <p className="text-sm">(AI 분석 엔진 연동 후 활성화)</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
