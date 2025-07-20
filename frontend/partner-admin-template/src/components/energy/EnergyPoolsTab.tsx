'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { EnergyFilters } from './EnergyFilters'
import { EnergyPoolCard } from './EnergyPoolCard'
import { EnergyPoolInfo } from '@/types'

interface EnergyPoolsTabProps {
  pools: EnergyPoolInfo[]
  searchTerm: string
  onSearchChange: (value: string) => void
  statusFilter: string
  onStatusChange: (value: string) => void
}

export function EnergyPoolsTab({
  pools,
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusChange
}: EnergyPoolsTabProps) {
  const filteredPools = pools.filter(pool => {
    const matchesSearch = pool.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === '' || pool.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>에너지 풀 목록</CardTitle>
        <CardDescription>등록된 에너지 풀 현황 및 관리</CardDescription>
      </CardHeader>
      <CardContent>
        <EnergyFilters
          searchTerm={searchTerm}
          onSearchChange={onSearchChange}
          statusFilter={statusFilter}
          onStatusChange={onStatusChange}
        />

        {/* 풀 그리드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPools.length === 0 ? (
            <div className="col-span-full text-center py-8 text-gray-500">
              조건에 맞는 에너지 풀이 없습니다.
            </div>
          ) : (
            filteredPools.map((pool) => (
              <EnergyPoolCard key={pool.id} pool={pool} />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
