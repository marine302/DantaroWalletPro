'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Zap, 
  TrendingUp, 
  Users, 
  DollarSign,
  Settings,
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Calculator,
  PieChart,
  ArrowUpDown
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { 
  useEnergyRentalOverview, 
  useEnergyRentalPools, 
  useEnergyRentalTransactions,
  useCreateEnergyPool,
  useUpdateEnergyPool
} from '@/lib/hooks'

// 에너지 렌탈 타입 정의
interface EnergyPool {
  id: string
  name: string
  total_energy: number
  available_energy: number
  staked_trx: number
  rental_rate: number // TRX per energy per hour
  status: 'active' | 'paused' | 'maintenance'
  utilization_rate: number
  daily_revenue: number
  created_at: string
  auto_rebalance: boolean
}

interface RentalTransaction {
  id: string
  customer_id: string
  customer_name: string
  energy_amount: number
  duration_hours: number
  rental_rate: number
  total_cost: number
  status: 'pending' | 'active' | 'completed' | 'failed'
  start_time: string
  end_time?: string
  pool_id: string
}

interface RentalOverview {
  total_pools: number
  total_energy_capacity: number
  total_energy_rented: number
  total_revenue_today: number
  total_revenue_month: number
  active_rentals: number
  average_utilization: number
  profit_margin: number
}

export default function EnergyRentalPage() {
  const [newPoolForm, setNewPoolForm] = useState({
    name: '',
    stake_amount: '',
    rental_rate: ''
  })

  // API 훅 사용
  const { data: overviewData, isLoading: overviewLoading } = useEnergyRentalOverview()
  const { data: poolsData, isLoading: poolsLoading } = useEnergyRentalPools()
  const { data: transactionsData, isLoading: transactionsLoading } = useEnergyRentalTransactions()
  const createPoolMutation = useCreateEnergyPool()
  const updatePoolMutation = useUpdateEnergyPool()

  // 폴백 데이터
  const fallbackOverview: RentalOverview = {
    total_pools: 3,
    total_energy_capacity: 2500000,
    total_energy_rented: 1875000,
    total_revenue_today: 2840,
    total_revenue_month: 89250,
    active_rentals: 47,
    average_utilization: 75.2,
    profit_margin: 23.8
  }

  const fallbackPools: EnergyPool[] = [
    {
      id: 'pool_001',
      name: '메인 에너지 풀',
      total_energy: 1000000,
      available_energy: 250000,
      staked_trx: 50000,
      rental_rate: 0.15,
      status: 'active',
      utilization_rate: 75.0,
      daily_revenue: 1200,
      created_at: '2025-01-15T09:00:00Z',
      auto_rebalance: true
    },
    {
      id: 'pool_002',
      name: 'VIP 전용 풀',
      total_energy: 800000,
      available_energy: 320000,
      staked_trx: 40000,
      rental_rate: 0.12,
      status: 'active',
      utilization_rate: 60.0,
      daily_revenue: 960,
      created_at: '2025-02-01T14:00:00Z',
      auto_rebalance: true
    },
    {
      id: 'pool_003',
      name: '테스트 풀',
      total_energy: 700000,
      available_energy: 700000,
      staked_trx: 35000,
      rental_rate: 0.20,
      status: 'paused',
      utilization_rate: 0.0,
      daily_revenue: 0,
      created_at: '2025-07-10T10:00:00Z',
      auto_rebalance: false
    }
  ]

  const fallbackTransactions: RentalTransaction[] = [
    {
      id: 'rent_001',
      customer_id: 'customer_001',
      customer_name: 'DApp사업자A',
      energy_amount: 50000,
      duration_hours: 24,
      rental_rate: 0.15,
      total_cost: 180,
      status: 'active',
      start_time: '2025-07-20T09:00:00Z',
      end_time: '2025-07-21T09:00:00Z',
      pool_id: 'pool_001'
    },
    {
      id: 'rent_002',
      customer_id: 'customer_002',
      customer_name: 'DApp사업자B',
      energy_amount: 75000,
      duration_hours: 12,
      rental_rate: 0.12,
      total_cost: 108,
      status: 'completed',
      start_time: '2025-07-19T14:00:00Z',
      end_time: '2025-07-20T02:00:00Z',
      pool_id: 'pool_002'
    }
  ]

  // 실제 API 데이터와 폴백 데이터 병합
  const overview = (overviewData as RentalOverview | undefined) || fallbackOverview
  const pools = (poolsData as { pools?: EnergyPool[] })?.pools || fallbackPools
  const transactions = (transactionsData as { transactions?: RentalTransaction[] })?.transactions || fallbackTransactions

  const handleCreatePool = async () => {
    try {
      await createPoolMutation.mutateAsync({
        name: newPoolForm.name,
        stake_amount: parseFloat(newPoolForm.stake_amount),
        rental_rate: parseFloat(newPoolForm.rental_rate)
      })
      setNewPoolForm({ name: '', stake_amount: '', rental_rate: '' })
    } catch (error) {
      console.error('풀 생성 실패:', error)
    }
  }

  const handleTogglePool = async (poolId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active'
    try {
      await updatePoolMutation.mutateAsync({
        poolId,
        updates: { status: newStatus }
      })
    } catch (error) {
      console.error('풀 상태 변경 실패:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge variant="default">활성</Badge>
      case 'paused': return <Badge variant="secondary">일시정지</Badge>
      case 'maintenance': return <Badge variant="destructive">점검중</Badge>
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

  if (overviewLoading || poolsLoading || transactionsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <Zap className="h-6 w-6 animate-pulse text-yellow-500" />
          <span className="text-lg">에너지 렌탈 정보를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  return (
    <Sidebar>
      <div className="flex h-screen bg-background">      
        <main className="flex-1 p-8 overflow-auto">
          <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">에너지 렌탈 서비스</h1>
                <p className="text-muted-foreground">
                  Doc-31: TRX 스테이킹을 통한 에너지 생성 및 자동 렌탈 서비스 관리
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="outline" className="flex items-center space-x-2">
                  <Calculator className="w-4 h-4" />
                  <span>수익성 계산기</span>
                </Button>
                <Button className="flex items-center space-x-2">
                  <Zap className="w-4 h-4" />
                  <span>새 풀 생성</span>
                </Button>
              </div>
            </div>
          </div>

          {/* 개요 통계 */}
          <div className="grid gap-6 md:grid-cols-4 mb-8">
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
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5" />
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

          <Tabs defaultValue="pools" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="pools">에너지 풀</TabsTrigger>
              <TabsTrigger value="rentals">렌탈 현황</TabsTrigger>
              <TabsTrigger value="analytics">분석 & 최적화</TabsTrigger>
              <TabsTrigger value="settings">설정</TabsTrigger>
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
                          <div className="flex items-center space-x-1">
                            {pool.auto_rebalance ? (
                              <CheckCircle className="w-3 h-3 text-green-500" />
                            ) : (
                              <AlertTriangle className="w-3 h-3 text-orange-500" />
                            )}
                            <span className="text-xs">{pool.auto_rebalance ? '활성' : '비활성'}</span>
                          </div>
                        </div>
                      </div>

                      {/* 액션 버튼들 */}
                      <div className="flex space-x-2 pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleTogglePool(pool.id, pool.status)}
                          disabled={updatePoolMutation.isPending}
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
                        disabled={createPoolMutation.isPending || !newPoolForm.name || !newPoolForm.stake_amount}
                        className="w-full"
                      >
                        {createPoolMutation.isPending ? (
                          <RotateCcw className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Zap className="w-4 h-4 mr-2" />
                        )}
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
                            <ArrowUpDown className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* 분석 & 최적화 탭 */}
            <TabsContent value="analytics" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    성능 분석 및 최적화 제안
                  </CardTitle>
                  <CardDescription>
                    AI 기반 분석을 통한 수익성 최적화 방안을 제공합니다
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>상세 분석 차트가 여기에 표시됩니다</p>
                    <p className="text-sm">(AI 분석 엔진 연동 후 활성화)</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 설정 탭 */}
            <TabsContent value="settings" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    에너지 렌탈 글로벌 설정
                  </CardTitle>
                  <CardDescription>
                    전체 에너지 렌탈 서비스의 기본 설정을 관리합니다
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>글로벌 설정 패널이 여기에 표시됩니다</p>
                    <p className="text-sm">(설정 시스템 구현 후 활성화)</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
    </Sidebar>
  )
}
