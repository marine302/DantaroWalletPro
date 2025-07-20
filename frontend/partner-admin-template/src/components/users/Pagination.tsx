'use client'

import React from 'react'
import { Button } from '@/components/ui/button'

interface PaginationProps {
  currentPage: number
  totalItems: number
  itemsPerPage: number
  displayedItems: number
  onPageChange: (page: number) => void
}

export function Pagination({
  currentPage,
  totalItems,
  itemsPerPage,
  displayedItems,
  onPageChange
}: PaginationProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  return (
    <div className="flex items-center justify-between mt-6">
      <div className="text-sm text-gray-700">
        전체 {totalItems.toLocaleString()}명 중 {startItem}-{Math.min(endItem, displayedItems)}명 표시
      </div>
      <div className="flex gap-2">
        <Button 
          variant="outline" 
          size="sm"
          disabled={currentPage === 1}
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        >
          이전
        </Button>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
        >
          다음
        </Button>
      </div>
    </div>
  )
}
