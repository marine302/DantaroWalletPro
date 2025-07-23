'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  X, 
  User as UserIcon, 
  Mail, 
  Phone, 
  Shield,
  Star,
  Save
} from 'lucide-react'

import type { User } from '@/types'

interface EditUserModalProps {
  user: User | null
  isOpen: boolean
  onClose: () => void
  onSave: (userData: Partial<User> & { id: string }) => Promise<void>
  isLoading?: boolean
}

export function EditUserModal({ user, isOpen, onClose, onSave, isLoading = false }: EditUserModalProps) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    status: 'active' as 'active' | 'inactive' | 'suspended' | 'pending',
    tier: 'basic' as 'basic' | 'premium' | 'vip',
    kyc_status: 'none' as 'none' | 'pending' | 'approved' | 'rejected'
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (user && isOpen) {
      // kyc_status 타입 매핑: not_started -> none
      const kycStatus = user.kyc_status || user.kycStatus || 'none'
      const mappedKycStatus = kycStatus === 'not_started' ? 'none' : kycStatus as 'pending' | 'approved' | 'rejected' | 'none'
      
      setFormData({
        username: user.username || '',
        email: user.email || '',
        phone: user.phone || '',
        status: user.status || 'active',
        tier: user.tier || 'basic',
        kyc_status: mappedKycStatus
      })
      setErrors({})
    }
  }, [user, isOpen])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.username.trim()) {
      newErrors.username = '사용자명을 입력해주세요'
    } else if (formData.username.length < 3) {
      newErrors.username = '사용자명은 3자 이상이어야 합니다'
    }

    if (!formData.email.trim()) {
      newErrors.email = '이메일을 입력해주세요'
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.email)) {
        newErrors.email = '올바른 이메일 형식을 입력해주세요'
      }
    }

    if (formData.phone && formData.phone.trim()) {
      const phoneRegex = /^[0-9-+\s()]+$/
      if (!phoneRegex.test(formData.phone)) {
        newErrors.phone = '올바른 전화번호 형식을 입력해주세요'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm() || !user) return

    try {
      await onSave({
        id: user.id,
        ...formData
      })
      onClose()
    } catch (error) {
      console.error('사용자 수정 실패:', error)
    }
  }

  const handleClose = () => {
    if (!isLoading) {
      setErrors({})
      onClose()
    }
  }

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
      <Card className="w-full max-w-2xl mx-auto bg-white max-h-[90vh] overflow-y-auto">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold flex items-center gap-2">
              <UserIcon className="h-5 w-5" />
              사용자 정보 수정
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClose}
              disabled={isLoading}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 기본 정보 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <UserIcon className="h-4 w-4" />
                기본 정보
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    사용자명
                  </label>
                  <Input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                    className={errors.username ? 'border-red-500' : ''}
                    disabled={isLoading}
                  />
                  {errors.username && (
                    <p className="text-sm text-red-600">{errors.username}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    이메일
                  </label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className={errors.email ? 'border-red-500' : ''}
                    disabled={isLoading}
                  />
                  {errors.email && (
                    <p className="text-sm text-red-600">{errors.email}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    전화번호 (선택)
                  </label>
                  <Input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    className={errors.phone ? 'border-red-500' : ''}
                    disabled={isLoading}
                    placeholder="전화번호를 입력하세요"
                  />
                  {errors.phone && (
                    <p className="text-sm text-red-600">{errors.phone}</p>
                  )}
                </div>
              </div>
            </div>

            {/* 상태 및 등급 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Shield className="h-4 w-4" />
                상태 및 등급
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    계정 상태
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as 'active' | 'inactive' | 'suspended' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                  >
                    <option value="active">활성</option>
                    <option value="inactive">비활성</option>
                    <option value="suspended">정지</option>
                    <option value="pending">대기</option>
                  </select>
                  <Badge className={getStatusBadge(formData.status)}>
                    {formData.status === 'active' ? '활성' : 
                     formData.status === 'inactive' ? '비활성' :
                     formData.status === 'suspended' ? '정지' : '대기'}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Star className="h-4 w-4" />
                    사용자 등급
                  </label>
                  <select
                    value={formData.tier}
                    onChange={(e) => setFormData(prev => ({ ...prev, tier: e.target.value as 'basic' | 'premium' | 'vip' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                  >
                    <option value="basic">Basic</option>
                    <option value="premium">Premium</option>
                    <option value="vip">VIP</option>
                  </select>
                  <Badge className={getTierBadge(formData.tier)}>
                    {formData.tier === 'basic' ? '베이직' :
                     formData.tier === 'premium' ? '프리미엄' : 'VIP'}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    KYC 상태
                  </label>
                  <select
                    value={formData.kyc_status}
                    onChange={(e) => setFormData(prev => ({ ...prev, kyc_status: e.target.value as 'none' | 'pending' | 'approved' | 'rejected' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                  >
                    <option value="none">미제출</option>
                    <option value="pending">대기</option>
                    <option value="approved">승인</option>
                    <option value="rejected">거부</option>
                  </select>
                  <Badge className={getKycBadge(formData.kyc_status)}>
                    {formData.kyc_status === 'approved' ? '승인' :
                     formData.kyc_status === 'pending' ? '대기' :
                     formData.kyc_status === 'rejected' ? '거부' : '미제출'}
                  </Badge>
                </div>
              </div>
            </div>

            {/* 버튼 영역 */}
            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1"
              >
                취소
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="flex-1"
              >
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? '저장 중...' : '저장'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
