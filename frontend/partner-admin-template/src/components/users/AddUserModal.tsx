'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { X, User, Mail, Shield } from 'lucide-react'

interface AddUserModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (userData: {
    username: string
    email: string
    tier: 'basic' | 'premium' | 'vip'
    send_welcome_email: boolean
  }) => Promise<void>
  isLoading?: boolean
}

export function AddUserModal({ isOpen, onClose, onSubmit, isLoading = false }: AddUserModalProps) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    tier: 'basic' as 'basic' | 'premium' | 'vip',
    send_welcome_email: true
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

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

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    try {
      await onSubmit(formData)
      // 성공 시 폼 리셋 및 모달 닫기
      setFormData({
        username: '',
        email: '',
        tier: 'basic',
        send_welcome_email: true
      })
      setErrors({})
      onClose()
    } catch (error) {
      console.error('사용자 추가 실패:', error)
    }
  }

  const handleClose = () => {
    if (!isLoading) {
      setFormData({
        username: '',
        email: '',
        tier: 'basic',
        send_welcome_email: true
      })
      setErrors({})
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md mx-auto bg-white">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold flex items-center gap-2">
              <User className="h-5 w-5" />
              새 사용자 추가
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
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 사용자명 입력 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <User className="h-4 w-4" />
                사용자명
              </label>
              <Input
                type="text"
                placeholder="사용자명을 입력하세요"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                className={errors.username ? 'border-red-500' : ''}
                disabled={isLoading}
              />
              {errors.username && (
                <p className="text-sm text-red-600">{errors.username}</p>
              )}
            </div>

            {/* 이메일 입력 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Mail className="h-4 w-4" />
                이메일
              </label>
              <Input
                type="email"
                placeholder="이메일을 입력하세요"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                className={errors.email ? 'border-red-500' : ''}
                disabled={isLoading}
              />
              {errors.email && (
                <p className="text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* 사용자 등급 선택 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                사용자 등급
              </label>
              <select
                value={formData.tier}
                onChange={(e) => setFormData(prev => ({ ...prev, tier: e.target.value as 'basic' | 'premium' | 'vip' }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              >
                <option value="basic">Basic</option>
                <option value="premium">Premium</option>
                <option value="vip">VIP</option>
              </select>
            </div>

            {/* 환영 이메일 발송 옵션 */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="welcome-email"
                checked={formData.send_welcome_email}
                onChange={(e) => setFormData(prev => ({ ...prev, send_welcome_email: e.target.checked }))}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                disabled={isLoading}
              />
              <label htmlFor="welcome-email" className="text-sm font-medium text-gray-700">
                환영 이메일 발송
              </label>
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
                {isLoading ? '추가 중...' : '사용자 추가'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
