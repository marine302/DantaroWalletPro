'use client'

import { Input } from '@/components/ui/input'

interface EnergyFiltersProps {
  searchTerm: string
  onSearchChange: (value: string) => void
  statusFilter: string
  onStatusChange: (value: string) => void
}

export function EnergyFilters({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusChange
}: EnergyFiltersProps) {
  return (
    <div className="flex gap-4 mb-6">
      <Input
        placeholder="풀 이름으로 검색..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="flex-1"
      />
      <select
        value={statusFilter}
        onChange={(e) => onStatusChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        <option value="">모든 상태</option>
        <option value="active">활성</option>
        <option value="maintenance">점검중</option>
        <option value="depleted">고갈</option>
      </select>
    </div>
  )
}
