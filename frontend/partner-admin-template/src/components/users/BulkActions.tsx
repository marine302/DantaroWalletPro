'use client'

import React from 'react'
import { Button } from '@/components/ui/button'

interface BulkActionsProps {
  selectedCount: number
  onActivate: () => void
  onDeactivate: () => void
  onExport: () => void
}

export function BulkActions({
  selectedCount,
  onActivate,
  onDeactivate,
  onExport
}: BulkActionsProps) {
  if (selectedCount === 0) return null

  return (
    <div className="flex items-center gap-3 mb-4 p-3 bg-blue-50 rounded-lg">
      <span className="text-sm text-blue-700">
        {selectedCount}명 선택됨
      </span>
      <Button 
        size="sm" 
        variant="outline"
        onClick={onActivate}
      >
        활성화
      </Button>
      <Button 
        size="sm" 
        variant="outline"
        onClick={onDeactivate}
      >
        비활성화
      </Button>
      <Button 
        size="sm" 
        variant="outline"
        onClick={onExport}
      >
        내보내기
      </Button>
    </div>
  )
}
