'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Edit,
  Trash2,
  Mail,
  Phone,
  Eye,
  Loader2
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { User } from '@/types'

interface UserTableProps {
  users: User[]
  loading: boolean
  error: boolean
  selectedUsers: string[]
  onUserSelect: (userId: string) => void
  onSelectAll: (checked: boolean) => void
  onViewUser?: (user: User) => void
  onEditUser?: (user: User) => void
  onDeleteUser?: (user: User) => void
}

export function UserTable({
  users,
  loading,
  error,
  selectedUsers,
  onUserSelect,
  onSelectAll,
  onViewUser,
  onEditUser,
  onDeleteUser
}: UserTableProps) {
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

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left">
              <input
                type="checkbox"
                checked={selectedUsers.length === users.length && users.length > 0}
                onChange={(e) => onSelectAll(e.target.checked)}
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
                    onChange={() => onUserSelect(user.id)}
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
                  <Badge className={getKycBadge((user.kycStatus || user.kyc_status) || 'none')}>
                    {(user.kycStatus || user.kyc_status) === 'approved' ? '승인' :
                     (user.kycStatus || user.kyc_status) === 'pending' ? '대기' :
                     (user.kycStatus || user.kyc_status) === 'rejected' ? '거부' : '미제출'}
                  </Badge>
                </td>
                <td className="px-4 py-4">
                  <Badge className={getTierBadge(user.tier || 'basic')}>
                    {user.tier === 'basic' ? '베이직' :
                     user.tier === 'premium' ? '프리미엄' : 
                     user.tier === 'vip' ? 'VIP' : '베이직'}
                  </Badge>
                </td>
                <td className="px-4 py-4">
                  <div className="text-sm text-gray-900">
                    {formatDate(user.createdAt || user.created_at || '')}
                  </div>
                  {user.last_login && (
                    <div className="text-xs text-gray-500">
                      최근: {formatDate(user.last_login)}
                    </div>
                  )}
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => onViewUser?.(user)}
                      title="사용자 상세보기"
                    >
                      <Eye className="w-3 h-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => onEditUser?.(user)}
                      title="사용자 정보 수정"
                    >
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="text-red-600 hover:text-red-700 hover:border-red-300"
                      onClick={() => onDeleteUser?.(user)}
                      title="사용자 삭제"
                    >
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
  )
}
