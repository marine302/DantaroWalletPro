'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { EnergyStats as EnergyStatsComponent } from './EnergyStats'
import { EnergyPoolsTab } from './EnergyPoolsTab'
import { EnergyTransactionTable } from './EnergyTransactionTable'
import { EnergySettingsTab } from './EnergySettingsTab'
import { EnergyPoolInfo, EnergyStats, EnergyTransaction, EnergySettings } from '@/types'

interface EnergyManagementSectionProps {
  stats: EnergyStats
  pools: EnergyPoolInfo[]
  transactions: EnergyTransaction[]
  settings?: EnergySettings
  onSettingsSave?: (settings: EnergySettings) => void
  onRefresh?: () => void
  onAddPool?: () => void
}

export function EnergyManagementSection({
  stats,
  pools,
  transactions,
  settings,
  onSettingsSave,
  onRefresh,
  onAddPool
}: EnergyManagementSectionProps) {
  const [activeTab, setActiveTab] = useState<'pools' | 'transactions' | 'settings'>('pools')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  return (
    <div className="space-y-6">
      <PageHeader
        title="에너지 풀 관리"
        description="TRON 에너지 풀 현황 및 대여 관리"
        onRefresh={onRefresh}
      >
        <Button className="flex items-center gap-2" onClick={onAddPool}>
          <Plus className="w-4 h-4" />
          풀 추가
        </Button>
      </PageHeader>

      {/* 통계 카드 */}
      <EnergyStatsComponent stats={stats} />

      {/* 탭 네비게이션 */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('pools')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'pools' 
              ? 'bg-white text-blue-600 shadow-sm' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          에너지 풀
        </button>
        <button
          onClick={() => setActiveTab('transactions')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'transactions' 
              ? 'bg-white text-blue-600 shadow-sm' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          대여 내역
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'settings' 
              ? 'bg-white text-blue-600 shadow-sm' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          설정
        </button>
      </div>

      {/* 탭 컨텐츠 */}
      {activeTab === 'pools' && (
        <EnergyPoolsTab
          pools={pools}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
        />
      )}

      {activeTab === 'transactions' && (
        <EnergyTransactionTable transactions={transactions} />
      )}

      {activeTab === 'settings' && (
        <EnergySettingsTab 
          settings={settings}
          onSave={onSettingsSave}
        />
      )}
    </div>
  )
}
