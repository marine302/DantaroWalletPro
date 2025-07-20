'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { 
  Zap, 
  Settings,
  Plus,
  RefreshCw,
  Activity,
  Timer,
  DollarSign,
  Users,
  Loader2,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
// import { 
//   useEnergyDashboard, 
//   useEnergyPoolStatus
// } from '@/lib/hooks'

interface EnergyPool {
  id: string
  name: string
  total_capacity: number
  available_capacity: number
  used_capacity: number
  price_per_unit: number
  status: 'active' | 'maintenance' | 'depleted'
  created_at: string
  last_updated: string
  rental_count: number
  revenue: number
}

interface EnergyStats {
  total_pools: number
  total_capacity: number
  total_used: number
  total_available: number
  utilization_rate: number
  total_revenue: number
  active_rentals: number
  avg_price_per_unit: number
}

interface EnergyTransaction {
  id: string
  user_id: string
  user_name: string
  pool_id: string
  pool_name: string
  amount: number
  price: number
  total_cost: number
  duration_hours: number
  status: 'active' | 'completed' | 'expired'
  created_at: string
  expires_at: string
}

export default function EnergyPage() {
  const [activeTab, setActiveTab] = useState<'pools' | 'transactions' | 'settings'>('pools')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  
  // TODO: 실제 파트너 ID를 가져와야 함 (인증된 사용자의 파트너 ID)
  // const partnerId = 1; // 임시로 1 사용
  
  // 실제 API 훅 사용 (백엔드 연결 후 활성화)
  // const { 
  //   data: dashboardData, 
  //   isLoading: dashboardLoading, 
  //   isError: dashboardError 
  // } = useEnergyDashboard(partnerId);
  
  // const { 
  //   data: poolStatusData, 
  //   isLoading: poolStatusLoading, 
  //   isError: poolStatusError 
  // } = useEnergyPoolStatus(partnerId);
  
  // 나머지 API 훅들은 필요시 사용
  // const { data: monitoringData } = useEnergyMonitoring(partnerId);
  // const { data: transactionsData } = useEnergyTransactions(partnerId, 1, 20);
  // const stakeForEnergyMutation = useStakeForEnergy();
  
  // 현재는 로딩 없이 진행 (백엔드 연결 전)
  const isLoading = false;
  const hasError = false;

  // 폴백 데이터
  const fallbackPools: EnergyPool[] = [
    {
      id: '1',
      name: 'Prime Energy Pool A',
      total_capacity: 1000000,
      available_capacity: 650000,
      used_capacity: 350000,
      price_per_unit: 0.00035,
      status: 'active',
      created_at: '2024-01-15T09:00:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 127,
      revenue: 8456.75
    },
    {
      id: '2',
      name: 'Standard Energy Pool B',
      total_capacity: 750000,
      available_capacity: 450000,
      used_capacity: 300000,
      price_per_unit: 0.00040,
      status: 'active',
      created_at: '2024-02-01T10:30:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 89,
      revenue: 6234.50
    },
    {
      id: '3',
      name: 'Premium Energy Pool C',
      total_capacity: 500000,
      available_capacity: 100000,
      used_capacity: 400000,
      price_per_unit: 0.00030,
      status: 'active',
      created_at: '2024-03-10T14:15:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 234,
      revenue: 12890.25
    },
    {
      id: '4',
      name: 'Economy Energy Pool D',
      total_capacity: 300000,
      available_capacity: 0,
      used_capacity: 300000,
      price_per_unit: 0.00045,
      status: 'depleted',
      created_at: '2024-04-05T11:00:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 156,
      revenue: 4567.80
    },
    {
      id: '5',
      name: 'Backup Energy Pool E',
      total_capacity: 200000,
      available_capacity: 0,
      used_capacity: 0,
      price_per_unit: 0.00038,
      status: 'maintenance',
      created_at: '2024-05-20T16:30:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 0,
      revenue: 0
    }
  ];

  const fallbackStats: EnergyStats = {
    total_pools: 5,
    total_capacity: 2750000,
    total_used: 1050000,
    total_available: 1200000,
    utilization_rate: 38.18,
    total_revenue: 32149.30,
    active_rentals: 606,
    avg_price_per_unit: 0.000376
  };

  const fallbackTransactions: EnergyTransaction[] = [
    {
      id: '1',
      user_id: 'user123',
      user_name: 'john_doe',
      pool_id: '1',
      pool_name: 'Prime Energy Pool A',
      amount: 1000,
      price: 0.00035,
      total_cost: 0.35,
      duration_hours: 24,
      status: 'active',
      created_at: '2024-07-13T06:00:00Z',
      expires_at: '2024-07-14T06:00:00Z'
    },
    {
      id: '2',
      user_id: 'user456',
      user_name: 'jane_smith',
      pool_id: '2',
      pool_name: 'Standard Energy Pool B',
      amount: 1500,
      price: 0.00040,
      total_cost: 0.60,
      duration_hours: 12,
      status: 'active',
      created_at: '2024-07-13T04:30:00Z',
      expires_at: '2024-07-13T16:30:00Z'
    },
    {
      id: '3',
      user_id: 'user789',
      user_name: 'bob_wilson',
      pool_id: '3',
      pool_name: 'Premium Energy Pool C',
      amount: 2000,
      price: 0.00030,
      total_cost: 0.60,
      duration_hours: 48,
      status: 'completed',
      created_at: '2024-07-11T10:00:00Z',
      expires_at: '2024-07-13T10:00:00Z'
    }
  ];

  // 실제 데이터 사용 (백엔드 연결 후 활성화)
  // const pools = poolStatusData?.pools || fallbackPools;
  // const stats = dashboardData?.stats || fallbackStats;
  
  // 현재는 fallback 데이터 사용 (백엔드 연결 전)
  const pools = fallbackPools;
  const stats = fallbackStats;
  const transactions = fallbackTransactions;

  const getStatusBadge = (status: string) => {
    const variants = {
      active: { class: 'bg-green-100 text-green-800', icon: CheckCircle, text: '활성' },
      maintenance: { class: 'bg-yellow-100 text-yellow-800', icon: Timer, text: '점검중' },
      depleted: { class: 'bg-red-100 text-red-800', icon: AlertTriangle, text: '고갈' }
    }
    return variants[status as keyof typeof variants] || variants.active
  }

  const getRentalStatusBadge = (status: string) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      completed: 'bg-blue-100 text-blue-800',
      expired: 'bg-gray-100 text-gray-800'
    }
    return variants[status as keyof typeof variants] || variants.active
  }

  const filteredPools = pools.filter(pool => {
    const matchesSearch = pool.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === '' || pool.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 로딩 및 에러 처리
  if (isLoading) {
    return (
      <Sidebar>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">에너지 데이터를 불러오는 중...</span>
          </div>
        </div>
      </Sidebar>
    );
  }

  if (hasError) {
    return (
      <Sidebar>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <span className="ml-2 text-red-600">데이터를 불러오는 중 오류가 발생했습니다.</span>
          </div>
        </div>
      </Sidebar>
    );
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">에너지 풀 관리</h1>
          <p className="text-gray-600 mt-1">TRON 에너지 풀 현황 및 대여 관리</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            새로고침
          </Button>
          <Button className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            풀 추가
          </Button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 에너지 용량</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.total_capacity.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">Energy Units</p>
              </div>
              <Zap className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">이용률</p>
                <p className="text-2xl font-bold text-purple-600">
                  {`${stats.utilization_rate.toFixed(1)}%`}
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${stats.utilization_rate}%` }}
                  />
                </div>
              </div>
              <Activity className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">활성 대여</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.active_rentals.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <Users className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 수익</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatCurrency(stats.total_revenue, 'TRX')}
                </p>
                <p className="text-xs text-gray-500">평균 {stats.avg_price_per_unit.toFixed(6)} TRX/Unit</p>
              </div>
              <DollarSign className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 탭 네비게이션 */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('pools')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'pools' 
              ? 'bg-white text-blue-600 shadow-sm' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          에너지 풀
        </button>
        <button
          onClick={() => setActiveTab('transactions')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'transactions' 
              ? 'bg-white text-blue-600 shadow-sm' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          대여 내역
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'settings' 
              ? 'bg-white text-blue-600 shadow-sm' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          설정
        </button>
      </div>

      {/* 에너지 풀 탭 */}
      {activeTab === 'pools' && (
        <Card>
          <CardHeader>
            <CardTitle>에너지 풀 목록</CardTitle>
            <CardDescription>등록된 에너지 풀 현황 및 관리</CardDescription>
          </CardHeader>
          <CardContent>
            {/* 필터 */}
            <div className="flex gap-4 mb-6">
              <Input
                placeholder="풀 이름으로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">모든 상태</option>
                <option value="active">활성</option>
                <option value="maintenance">점검중</option>
                <option value="depleted">고갈</option>
              </select>
            </div>

            {/* 풀 그리드 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPools.length === 0 ? (
                <div className="col-span-full text-center py-8 text-gray-500">
                  조건에 맞는 에너지 풀이 없습니다.
                </div>
              ) : (
                filteredPools.map((pool) => {
                  const status = getStatusBadge(pool.status);
                  const StatusIcon = status.icon;
                  const utilizationRate = (pool.used_capacity / pool.total_capacity) * 100;
                  
                  return (
                    <Card key={pool.id} className="hover:shadow-lg transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h3 className="font-semibold text-lg text-gray-900">{pool.name}</h3>
                            <p className="text-sm text-gray-500">ID: {pool.id}</p>
                          </div>
                          <Badge className={status.class}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {status.text}
                          </Badge>
                        </div>

                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">이용률</span>
                              <span className="font-medium">{utilizationRate.toFixed(1)}%</span>
                            </div>
                            <Progress value={utilizationRate} className="h-2" />
                          </div>

                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <p className="text-gray-600">총 용량</p>
                              <p className="font-medium">{pool.total_capacity.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">사용 중</p>
                              <p className="font-medium text-red-600">{pool.used_capacity.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">사용 가능</p>
                              <p className="font-medium text-green-600">{pool.available_capacity.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">단가</p>
                              <p className="font-medium">{pool.price_per_unit.toFixed(6)} TRX</p>
                            </div>
                          </div>

                          <div className="border-t pt-3">
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-gray-600">대여 건수: {pool.rental_count}건</span>
                              <span className="font-medium text-blue-600">
                                수익: {formatCurrency(pool.revenue, 'TRX')}
                              </span>
                            </div>
                          </div>

                          <div className="flex gap-2 pt-2">
                            <Button size="sm" variant="outline" className="flex-1">
                              <Settings className="w-3 h-3 mr-1" />
                              설정
                            </Button>
                            <Button size="sm" className="flex-1">
                              상세보기
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 대여 내역 탭 */}
      {activeTab === 'transactions' && (
        <Card>
          <CardHeader>
            <CardTitle>에너지 대여 내역</CardTitle>
            <CardDescription>사용자별 에너지 대여 및 사용 내역</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      사용자
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      에너지 풀
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      수량
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      비용
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      기간
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      시작일
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">{transaction.user_name}</div>
                        <div className="text-sm text-gray-500">{transaction.user_id}</div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">{transaction.pool_name}</div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {transaction.amount.toLocaleString()} Energy
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(transaction.total_cost, 'TRX')}
                        </div>
                        <div className="text-sm text-gray-500">
                          @{transaction.price.toFixed(6)} TRX/Unit
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">{transaction.duration_hours}시간</div>
                      </td>
                      <td className="px-4 py-4">
                        <Badge className={getRentalStatusBadge(transaction.status)}>
                          {transaction.status === 'active' ? '활성' :
                           transaction.status === 'completed' ? '완료' : '만료'}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {formatDate(transaction.created_at)}
                        </div>
                        <div className="text-sm text-gray-500">
                          만료: {formatDate(transaction.expires_at)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 설정 탭 */}
      {activeTab === 'settings' && (
        <Card>
          <CardHeader>
            <CardTitle>에너지 풀 설정</CardTitle>
            <CardDescription>에너지 풀 운영 및 가격 정책 설정</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">기본 설정</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      기본 에너지 단가 (TRX)
                    </label>
                    <Input 
                      type="number" 
                      step="0.000001"
                      placeholder="0.000350"
                      defaultValue="0.000350"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      최대 대여 기간 (시간)
                    </label>
                    <Input 
                      type="number"
                      placeholder="72"
                      defaultValue="72"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">자동 관리</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">자동 풀 보충</p>
                      <p className="text-sm text-gray-500">에너지 용량이 20% 이하로 떨어지면 자동 보충</p>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">동적 가격 조정</p>
                      <p className="text-sm text-gray-500">수요에 따라 에너지 단가 자동 조정</p>
                    </div>
                    <input type="checkbox" className="rounded" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">점검 모드 자동 전환</p>
                      <p className="text-sm text-gray-500">문제 감지시 자동으로 점검 모드로 전환</p>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button variant="outline">취소</Button>
                <Button>설정 저장</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      </div>
    </Sidebar>
  )
}
