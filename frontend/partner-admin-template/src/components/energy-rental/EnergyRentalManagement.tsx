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
  RotateCcw,
  Plus,
  Search
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

interface EnergyRentalPool {
  id: string
  name: string
  total_energy: number
  available_energy: number
  rented_energy: number
  rental_rate: number
  utilization_rate: number
  status: 'active' | 'maintenance' | 'full'
  created_at: string
  last_updated: string
}

interface RentalTransaction {
  id: string
  user_id: string
  user_name: string
  pool_id: string
  pool_name: string
  energy_amount: number
  rental_fee: number
  duration_hours: number
  status: 'active' | 'completed' | 'cancelled'
  started_at: string
  expires_at: string
}

interface EnergyRentalStats {
  totalPools: number
  totalCapacity: number
  totalRented: number
  totalRevenue: number
  activeRentals: number
  utilizationRate: number
  dailyGrowth: number
}

interface EnergyRentalManagementProps {
  stats: EnergyRentalStats
  pools: EnergyRentalPool[]
  transactions: RentalTransaction[]
  onRefresh: () => void
  onCreatePool: () => void
  onManagePool: (poolId: string) => void
}

export function EnergyRentalManagement({
  stats,
  pools,
  transactions,
  onRefresh,
  onCreatePool,
  onManagePool
}: EnergyRentalManagementProps) {
  const [activeTab, setActiveTab] = useState('pools')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const getStatusColor = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      maintenance: 'bg-yellow-100 text-yellow-800',
      full: 'bg-red-100 text-red-800',
      completed: 'bg-blue-100 text-blue-800',
      cancelled: 'bg-gray-100 text-gray-800'
    }
    return colors[status as keyof typeof colors] || colors.active
  }

  const getUtilizationColor = (rate: number) => {
    if (rate >= 90) return 'text-red-600'
    if (rate >= 70) return 'text-yellow-600'
    return 'text-green-600'
  }

  const filteredPools = pools.filter(pool => {
    const matchesSearch = pool.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = !statusFilter || pool.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const filteredTransactions = transactions.filter(tx => {
    const matchesSearch = tx.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tx.pool_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = !statusFilter || tx.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="에너지 대여 관리"
        description="TRON 에너지 풀 대여 서비스 관리"
        onRefresh={onRefresh}
      >
        <Button onClick={onCreatePool}>
          <Plus className="h-4 w-4 mr-2" />
          풀 생성
        </Button>
      </PageHeader>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 풀 수</p>
                <p className="text-2xl font-bold text-blue-600">{stats.totalPools}</p>
                <p className="text-xs text-gray-500">개</p>
              </div>
              <Zap className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 용량</p>
                <p className="text-2xl font-bold text-green-600">{stats.totalCapacity.toLocaleString()}</p>
                <p className="text-xs text-gray-500">에너지</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">대여 중</p>
                <p className="text-2xl font-bold text-orange-600">{stats.totalRented.toLocaleString()}</p>
                <p className="text-xs text-gray-500">에너지</p>
              </div>
              <Users className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 수익</p>
                <p className="text-2xl font-bold text-purple-600">{formatCurrency(stats.totalRevenue)}</p>
                <p className="text-xs text-gray-500">TRX</p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 필터 및 검색 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="풀명, 사용자명으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 상태</option>
              <option value="active">활성</option>
              <option value="maintenance">유지보수</option>
              <option value="full">포화</option>
              <option value="completed">완료</option>
              <option value="cancelled">취소</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* 탭 콘텐츠 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="pools">에너지 풀</TabsTrigger>
          <TabsTrigger value="rentals">대여 현황</TabsTrigger>
          <TabsTrigger value="analytics">분석</TabsTrigger>
        </TabsList>

        <TabsContent value="pools" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPools.map((pool) => (
              <Card key={pool.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{pool.name}</CardTitle>
                    <Badge className={getStatusColor(pool.status)}>
                      {pool.status.toUpperCase()}
                    </Badge>
                  </div>
                  <CardDescription>
                    생성일: {formatDate(pool.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* 용량 정보 */}
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>사용률</span>
                        <span className={getUtilizationColor(pool.utilization_rate)}>
                          {pool.utilization_rate.toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={pool.utilization_rate} className="h-2" />
                    </div>

                    {/* 통계 */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">총 용량</p>
                        <p className="font-semibold">{pool.total_energy.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">사용 가능</p>
                        <p className="font-semibold text-green-600">{pool.available_energy.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">대여 중</p>
                        <p className="font-semibold text-orange-600">{pool.rented_energy.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">대여료</p>
                        <p className="font-semibold">{pool.rental_rate} TRX/h</p>
                      </div>
                    </div>

                    {/* 액션 버튼 */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => onManagePool(pool.id)}
                      >
                        <Settings className="h-4 w-4 mr-2" />
                        관리
                      </Button>
                      <Button
                        variant={pool.status === 'active' ? 'outline' : 'default'}
                        size="sm"
                        className="flex-1"
                      >
                        {pool.status === 'active' ? (
                          <>
                            <Pause className="h-4 w-4 mr-2" />
                            일시정지
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-2" />
                            시작
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="rentals" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>활성 대여 현황</CardTitle>
              <CardDescription>현재 진행 중인 에너지 대여 목록</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredTransactions.map((transaction) => (
                  <div key={transaction.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getStatusColor(transaction.status)}>
                            {transaction.status.toUpperCase()}
                          </Badge>
                          <span className="font-medium">{transaction.user_name}</span>
                          <span className="text-sm text-gray-500">→ {transaction.pool_name}</span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">에너지량</p>
                            <p className="font-semibold">{transaction.energy_amount.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">대여료</p>
                            <p className="font-semibold">{formatCurrency(transaction.rental_fee)} TRX</p>
                          </div>
                          <div>
                            <p className="text-gray-600">기간</p>
                            <p className="font-semibold">{transaction.duration_hours}시간</p>
                          </div>
                          <div>
                            <p className="text-gray-600">만료일</p>
                            <p className="font-semibold">{formatDate(transaction.expires_at)}</p>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          상세
                        </Button>
                        {transaction.status === 'active' && (
                          <Button variant="outline" size="sm">
                            <RotateCcw className="h-4 w-4 mr-2" />
                            연장
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>수익 분석</CardTitle>
                <CardDescription>에너지 대여 수익 현황</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>일간 수익</span>
                    <span className="font-bold text-green-600">+12.5%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>주간 수익</span>
                    <span className="font-bold text-green-600">+8.2%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>월간 수익</span>
                    <span className="font-bold text-green-600">+15.7%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>이용률 분석</CardTitle>
                <CardDescription>에너지 풀 사용 현황</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>평균 이용률</span>
                    <span className="font-bold">{stats.utilizationRate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>피크 시간대</span>
                    <span className="font-bold">14:00 - 18:00</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>최적 가격</span>
                    <span className="font-bold">조정 필요</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
