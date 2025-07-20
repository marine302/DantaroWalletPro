'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { EnergyRentalManagementSection } from '@/components/energy-rental/EnergyRentalManagementSection'

export default function EnergyRentalPage() {
  // 목업 데이터
  const [overview] = useState({
    total_energy_capacity: 50000000,
    average_utilization: 78.5,
    total_revenue_today: 1250,
    active_rentals: 145,
    total_revenue_month: 35000,
    profit_margin: 22.5,
    total_energy_rented: 39250000
  })

  const [pools] = useState([
    {
      id: 'pool_001',
      name: 'High-Yield Pool A',
      status: 'active',
      created_at: '2025-07-15T00:00:00Z',
      utilization_rate: 85.2,
      available_energy: 7500000,
      total_energy: 50000000,
      staked_trx: 150000,
      rental_rate: 0.02,
      daily_revenue: 3000,
      auto_rebalance: true
    },
    {
      id: 'pool_002',
      name: 'Stable Pool B',
      status: 'paused',
      created_at: '2025-07-10T00:00:00Z',
      utilization_rate: 45.8,
      available_energy: 27100000,
      total_energy: 50000000,
      staked_trx: 100000,
      rental_rate: 0.015,
      daily_revenue: 1500,
      auto_rebalance: false
    }
  ])

  const [transactions] = useState([
    {
      id: 'tx_001',
      customer_name: 'DeFi Protocol A',
      energy_amount: 5000000,
      duration_hours: 24,
      total_cost: 2400,
      start_time: '2025-07-20T08:00:00Z',
      end_time: '2025-07-21T08:00:00Z',
      status: 'active'
    },
    {
      id: 'tx_002',
      customer_name: 'Trading Bot B',
      energy_amount: 2000000,
      duration_hours: 12,
      total_cost: 600,
      start_time: '2025-07-20T10:00:00Z',
      end_time: '2025-07-20T22:00:00Z',
      status: 'completed'
    }
  ])

  const handleCreatePool = () => {
    console.log('새 에너지 풀 생성')
  }

  const handleTogglePool = (poolId: string, currentStatus: string) => {
    console.log('풀 상태 변경:', poolId, currentStatus)
  }

  const handleRefresh = () => {
    console.log('에너지 렌탈 데이터 새로고침')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <EnergyRentalManagementSection
          overview={overview}
          pools={pools}
          transactions={transactions}
          onCreatePool={handleCreatePool}
          onTogglePool={handleTogglePool}
          onRefresh={handleRefresh}
        />
      </div>
    </Sidebar>
  )
}