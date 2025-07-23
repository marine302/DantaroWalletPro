'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  X, 
  User as UserIcon, 
  Mail, 
  Phone, 
  Wallet, 
  Calendar,
  Shield,
  Clock,
  DollarSign,
  CreditCard
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { User } from '@/types'

interface UserDetailModalProps {
  user: User | null
  isOpen: boolean
  onClose: () => void
}

export function UserDetailModal({ user, isOpen, onClose }: UserDetailModalProps) {
  if (!isOpen || !user) return null

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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <UserIcon className="h-5 w-5" />
            사용자 상세 정보
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* 기본 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserIcon className="h-4 w-4" />
                기본 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">사용자명</label>
                <p className="text-lg font-medium">{user.username}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">사용자 ID</label>
                <p className="text-lg font-mono text-gray-600">{user.id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">상태</label>
                <div className="mt-1">
                  <Badge className={getStatusBadge(user.status)}>
                    {user.status === 'active' ? '활성' : 
                     user.status === 'inactive' ? '비활성' :
                     user.status === 'suspended' ? '정지' : '대기'}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">등급</label>
                <div className="mt-1">
                  <Badge className={getTierBadge(user.tier || 'basic')}>
                    {user.tier === 'basic' ? '베이직' :
                     user.tier === 'premium' ? '프리미엄' : 
                     user.tier === 'vip' ? 'VIP' : '베이직'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 연락처 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                연락처 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                  <Mail className="h-3 w-3" />
                  이메일
                </label>
                <p className="text-lg">{user.email}</p>
              </div>
              {user.phone && (
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    전화번호
                  </label>
                  <p className="text-lg">{user.phone}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 지갑 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                지갑 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">지갑 주소</label>
                <p className="text-lg font-mono bg-gray-50 p-2 rounded break-all">
                  {user.wallet_address || user.walletAddress}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    현재 잔액
                  </label>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(user.balance, 'USDT')}
                  </p>
                </div>
                {user.totalVolume && (
                  <div>
                    <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                      <CreditCard className="h-3 w-3" />
                      총 거래량
                    </label>
                    <p className="text-xl font-semibold">
                      {formatCurrency(user.totalVolume, 'USDT')}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* KYC 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                KYC 인증 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">KYC 상태</label>
                <div className="mt-1">
                  <Badge className={getKycBadge(user.kyc_status || user.kycStatus)}>
                    {(user.kyc_status || user.kycStatus) === 'approved' ? '승인' :
                     (user.kyc_status || user.kycStatus) === 'pending' ? '대기' :
                     (user.kyc_status || user.kycStatus) === 'rejected' ? '거부' : '미제출'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 계정 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                계정 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">가입일</label>
                <p className="text-lg">{formatDate(user.created_at || user.createdAt)}</p>
              </div>
              {(user.last_login || user.lastLogin) && (
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    최근 로그인
                  </label>
                  <p className="text-lg">{formatDate(user.last_login || user.lastLogin)}</p>
                </div>
              )}
              {user.totalTransactions && (
                <div>
                  <label className="text-sm font-medium text-gray-500">총 거래 수</label>
                  <p className="text-lg font-semibold">{user.totalTransactions.toLocaleString()}회</p>
                </div>
              )}
              {user.referral_code && (
                <div>
                  <label className="text-sm font-medium text-gray-500">추천 코드</label>
                  <p className="text-lg font-mono bg-gray-50 p-1 rounded">{user.referral_code}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex justify-end">
          <Button onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  )
}
