'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  X, 
  AlertTriangle,
  Trash2
} from 'lucide-react'

import type { User } from '@/types'

interface DeleteUserModalProps {
  user: User | null
  isOpen: boolean
  onClose: () => void
  onConfirm: (userId: string) => Promise<void>
  isLoading?: boolean
}

export function DeleteUserModal({ user, isOpen, onClose, onConfirm, isLoading = false }: DeleteUserModalProps) {
  const handleConfirm = async () => {
    if (user) {
      await onConfirm(user.id)
      onClose()
    }
  }

  const handleClose = () => {
    if (!isLoading) {
      onClose()
    }
  }

  if (!isOpen || !user) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md mx-auto bg-white">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              사용자 삭제 확인
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
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-medium text-red-800">주의: 이 작업은 되돌릴 수 없습니다</h3>
                  <p className="text-sm text-red-700 mt-1">
                    사용자를 삭제하면 모든 관련 데이터가 영구적으로 삭제됩니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">삭제될 사용자 정보:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <p><span className="font-medium">사용자명:</span> {user.username}</p>
                <p><span className="font-medium">이메일:</span> {user.email}</p>
                <p><span className="font-medium">지갑 주소:</span> {user.wallet_address || user.walletAddress}</p>
                <p><span className="font-medium">잔액:</span> {user.balance} USDT</p>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium">삭제 전 확인사항:</p>
                  <ul className="mt-1 list-disc list-inside space-y-1">
                    <li>사용자의 잔액이 0인지 확인하세요</li>
                    <li>진행 중인 거래가 없는지 확인하세요</li>
                    <li>필요한 데이터를 백업했는지 확인하세요</li>
                  </ul>
                </div>
              </div>
            </div>

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
                type="button"
                variant="destructive"
                onClick={handleConfirm}
                disabled={isLoading}
                className="flex-1"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                {isLoading ? '삭제 중...' : '삭제 확인'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
