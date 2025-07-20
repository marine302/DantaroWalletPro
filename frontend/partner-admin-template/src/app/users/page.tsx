'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { 
  Users, 
  Search, 
  Download, 
  Plus,
  Edit,
  Trash2,
  Mail,
  Phone,
  Activity,
  DollarSign,
  Eye,
  Loader2
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useUsers, useUserStats } from '@/lib/hooks'

interface User {
  id: string
  username: string
  email: string
  phone?: string
  wallet_address: string
  balance: number
  status: 'active' | 'inactive' | 'suspended' | 'pending'
  created_at: string
  last_login?: string
  kyc_status: 'none' | 'pending' | 'approved' | 'rejected'
  tier: 'basic' | 'premium' | 'vip'
  referral_code?: string
  referred_by?: string
}

interface UserStats {
  total_users: number
  active_users: number
  new_users_today: number
  total_balance: number
  average_balance: number
  kyc_approved: number
  kyc_pending: number
}

// 백엔드 응답 타입 (실제 API 응답 구조)
interface UserStatsResponse {
  total_users: number
  active_users: number
  new_users: number
  new_users_today: number
  total_balance: number
  average_balance: number
  kyc_approved: number
  kyc_pending: number
  daily_growth: number
  weekly_growth: number
  activity_rate: number
}

export default function UsersPage() {
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [kycFilter, setKycFilter] = useState<string>('')
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])

  // 실제 API 데이터 사용
  const { data: usersData, isLoading: usersLoading, isError: usersError } = useUsers(currentPage, 20);
  const { data: statsData, isLoading: statsLoading, isError: statsError } = useUserStats();

  // 폴백 데이터
  const fallbackUsers: User[] = [
    {
      id: '1',
      username: 'john_doe',
      email: 'john@example.com',
      phone: '+82-10-1234-5678',
      wallet_address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
      balance: 15000.50,
      status: 'active',
      created_at: '2024-01-15T09:30:00Z',
      last_login: '2024-07-13T08:45:00Z',
      kyc_status: 'approved',
      tier: 'premium',
      referral_code: 'JOHN2024',
      referred_by: undefined
    },
    {
      id: '2',
      username: 'jane_smith',
      email: 'jane@example.com',
      phone: '+82-10-9876-5432',
      wallet_address: 'TMuA6YqfCeX8EhbfYEg5y7S4DqzSJireY9',
      balance: 8750.25,
      status: 'active',
      created_at: '2024-02-20T14:15:00Z',
      last_login: '2024-07-12T19:30:00Z',
      kyc_status: 'approved',
      tier: 'basic',
      referral_code: 'JANE2024'
    },
    {
      id: '3',
      username: 'bob_wilson',
      email: 'bob@example.com',
      wallet_address: 'TLPpXqUYssrZPCWwP1MUK8yqeZsKAFa2Z8',
      balance: 2340.00,
      status: 'inactive',
      created_at: '2024-03-10T11:00:00Z',
      last_login: '2024-07-01T16:20:00Z',
      kyc_status: 'pending',
      tier: 'basic'
    },
    {
      id: '4',
      username: 'alice_johnson',
      email: 'alice@example.com',
      phone: '+82-10-5555-1234',
      wallet_address: 'TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs',
      balance: 45600.75,
      status: 'active',
      created_at: '2024-01-05T10:30:00Z',
      last_login: '2024-07-13T07:15:00Z',
      kyc_status: 'approved',
      tier: 'vip',
      referral_code: 'ALICE2024'
    },
    {
      id: '5',
      username: 'charlie_brown',
      email: 'charlie@example.com',
      wallet_address: 'TSSMHYeV2uE9qYH14Hvcs6HjRNjPYWMGpT',
      balance: 0.00,
      status: 'suspended',
      created_at: '2024-06-15T16:45:00Z',
      kyc_status: 'rejected',
      tier: 'basic'
    }
  ];

  const fallbackStats: UserStats = {
    total_users: 1247,
    active_users: 892,
    new_users_today: 23,
    total_balance: 2847352.75,
    average_balance: 2284.12,
    kyc_approved: 756,
    kyc_pending: 89
  };

  // 데이터 매핑
  const users = (usersData as { users?: User[] })?.users || fallbackUsers;
  
  // 백엔드 응답을 프론트엔드 UserStats 형식으로 변환
  const statsResponse = statsData as UserStatsResponse | null;
  const stats: UserStats = statsResponse ? {
    total_users: statsResponse.total_users || 0,
    active_users: statsResponse.active_users || 0,
    new_users_today: statsResponse.new_users_today || 0,
    total_balance: statsResponse.total_balance || 0,
    average_balance: statsResponse.average_balance || 0,
    kyc_approved: statsResponse.kyc_approved || 0,
    kyc_pending: statsResponse.kyc_pending || 0
  } : fallbackStats;

  const getStatusBadge = (status: string) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800'
    }
    return variants[status as keyof typeof variants] || variants.pending
  }

  const getKycBadge = (status: string) => {
    const variants = {
      approved: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      rejected: 'bg-red-100 text-red-800',
      none: 'bg-gray-100 text-gray-800'
    }
    return variants[status as keyof typeof variants] || variants.none
  }

  const getTierBadge = (tier: string) => {
    const variants = {
      basic: 'bg-blue-100 text-blue-800',
      premium: 'bg-purple-100 text-purple-800',
      vip: 'bg-yellow-100 text-yellow-800'
    }
    return variants[tier as keyof typeof variants] || variants.basic
  }

  const handleUserSelect = (userId: string) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const handleBulkAction = (action: string) => {
    console.log(`Bulk action: ${action} for users:`, selectedUsers)
    // TODO: 실제 벌크 액션 구현
  }

  const loading = usersLoading || statsLoading
  const error = usersError || statsError

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">사용자 관리</h1>
          <p className="text-gray-600 mt-1">플랫폼 사용자 현황 및 관리</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="w-4 h-4" />
            내보내기
          </Button>
          <Button className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            사용자 추가
          </Button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 사용자</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : stats.total_users.toLocaleString()}
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">활성 사용자</p>
                <p className="text-2xl font-bold text-green-600">
                  {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : stats.active_users.toLocaleString()}
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">신규 사용자 (오늘)</p>
                <p className="text-2xl font-bold text-blue-600">
                  {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : `+${stats.new_users_today}`}
                </p>
              </div>
              <Plus className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 잔액</p>
                <p className="text-2xl font-bold text-purple-600">
                  {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : formatCurrency(stats.total_balance, 'USDT')}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 필터 및 검색 */}
      <Card>
        <CardHeader>
          <CardTitle>사용자 목록</CardTitle>
          <CardDescription>사용자 검색 및 필터링</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="사용자명, 이메일, 지갑 주소로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">모든 상태</option>
              <option value="active">활성</option>
              <option value="inactive">비활성</option>
              <option value="suspended">정지</option>
              <option value="pending">대기</option>
            </select>
            <select
              value={kycFilter}
              onChange={(e) => setKycFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">모든 KYC</option>
              <option value="approved">승인</option>
              <option value="pending">대기</option>
              <option value="rejected">거부</option>
              <option value="none">미제출</option>
            </select>
          </div>

          {/* 벌크 액션 */}
          {selectedUsers.length > 0 && (
            <div className="flex items-center gap-3 mb-4 p-3 bg-blue-50 rounded-lg">
              <span className="text-sm text-blue-700">
                {selectedUsers.length}명 선택됨
              </span>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleBulkAction('activate')}
              >
                활성화
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleBulkAction('deactivate')}
              >
                비활성화
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleBulkAction('export')}
              >
                내보내기
              </Button>
            </div>
          )}

          {/* 사용자 테이블 */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedUsers.length === users.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedUsers(users.map((u: User) => u.id))
                        } else {
                          setSelectedUsers([])
                        }
                      }}
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    사용자
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    연락처
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    잔액
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    KYC
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    등급
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    가입일
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    액션
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                      <p className="text-gray-500 mt-2">사용자 목록을 불러오는 중...</p>
                    </td>
                  </tr>
                ) : error ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-red-600">
                      사용자 목록을 불러오는데 실패했습니다.
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                      등록된 사용자가 없습니다.
                    </td>
                  </tr>
                ) : (
                  users.map((user: User) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={selectedUsers.includes(user.id)}
                          onChange={() => handleUserSelect(user.id)}
                        />
                      </td>
                      <td className="px-4 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{user.username}</div>
                          <div className="text-sm text-gray-500 truncate max-w-xs" title={user.wallet_address}>
                            {user.wallet_address}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div>
                          <div className="text-sm text-gray-900 flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {user.email}
                          </div>
                          {user.phone && (
                            <div className="text-sm text-gray-500 flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {user.phone}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(user.balance, 'USDT')}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <Badge className={getStatusBadge(user.status)}>
                          {user.status === 'active' ? '활성' : 
                           user.status === 'inactive' ? '비활성' :
                           user.status === 'suspended' ? '정지' : '대기'}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <Badge className={getKycBadge(user.kyc_status)}>
                          {user.kyc_status === 'approved' ? '승인' :
                           user.kyc_status === 'pending' ? '대기' :
                           user.kyc_status === 'rejected' ? '거부' : '미제출'}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <Badge className={getTierBadge(user.tier)}>
                          {user.tier === 'basic' ? '베이직' :
                           user.tier === 'premium' ? '프리미엄' : 'VIP'}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {formatDate(user.created_at)}
                        </div>
                        {user.last_login && (
                          <div className="text-xs text-gray-500">
                            최근: {formatDate(user.last_login)}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <Button size="sm" variant="outline">
                            <Eye className="w-3 h-3" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700">
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* 페이지네이션 */}
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-700">
              전체 {stats.total_users.toLocaleString()}명 중 1-{Math.min(20, users.length)}명 표시
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              >
                이전
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                다음
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      </div>
    </Sidebar>
  )
}
