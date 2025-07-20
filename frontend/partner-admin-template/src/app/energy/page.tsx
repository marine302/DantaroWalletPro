'use client'

import React from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Loader2, AlertTriangle } from 'lucide-react'
import { EnergyManagementSection } from '@/components/energy/EnergyManagementSection'
import { EnergyPoolInfo, EnergyStats, EnergyTransaction, EnergySettings } from '@/types'
// import { 
//   useEnergyDashboard, 
//   useEnergyPoolStatus
// } from '@/lib/hooks'

export default function EnergyPage() {
  // TODO: 실제 파트너 ID를 가져와야 함 (인증된 사용자의 파트너 ID)
  // const partnerId = 1; // 임시로 1 사용
  
  // 실제 API 훅 사용 (백엔드 연결 후 활성화)
  // const { 
  //   data: dashboardData, 
  //   isLoading: dashboardLoading, 
  //   isError: dashboardError 
  // } = useEnergyDashboard(partnerId);
  
  // const { 
  //   data: poolStatusData, 
  //   isLoading: poolStatusLoading, 
  //   isError: poolStatusError 
  // } = useEnergyPoolStatus(partnerId);
  
  // 나머지 API 훅들은 필요시 사용
  // const { data: monitoringData } = useEnergyMonitoring(partnerId);
  // const { data: transactionsData } = useEnergyTransactions(partnerId, 1, 20);
  // const stakeForEnergyMutation = useStakeForEnergy();
  
  // 현재는 로딩 없이 진행 (백엔드 연결 전)
  const isLoading = false;
  const hasError = false;

  // 폴백 데이터
  const fallbackPools: EnergyPoolInfo[] = [
    {
      id: '1',
      name: 'Prime Energy Pool A',
      total_capacity: 1000000,
      available_capacity: 650000,
      used_capacity: 350000,
      price_per_unit: 0.00035,
      status: 'active',
      created_at: '2024-01-15T09:00:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 127,
      revenue: 8456.75
    },
    {
      id: '2',
      name: 'Standard Energy Pool B',
      total_capacity: 750000,
      available_capacity: 450000,
      used_capacity: 300000,
      price_per_unit: 0.00040,
      status: 'active',
      created_at: '2024-02-01T10:30:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 89,
      revenue: 6234.50
    },
    {
      id: '3',
      name: 'Premium Energy Pool C',
      total_capacity: 500000,
      available_capacity: 100000,
      used_capacity: 400000,
      price_per_unit: 0.00030,
      status: 'active',
      created_at: '2024-03-10T14:15:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 234,
      revenue: 12890.25
    },
    {
      id: '4',
      name: 'Economy Energy Pool D',
      total_capacity: 300000,
      available_capacity: 0,
      used_capacity: 300000,
      price_per_unit: 0.00045,
      status: 'depleted',
      created_at: '2024-04-05T11:00:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 156,
      revenue: 4567.80
    },
    {
      id: '5',
      name: 'Backup Energy Pool E',
      total_capacity: 200000,
      available_capacity: 0,
      used_capacity: 0,
      price_per_unit: 0.00038,
      status: 'maintenance',
      created_at: '2024-05-20T16:30:00Z',
      last_updated: '2024-07-13T08:45:00Z',
      rental_count: 0,
      revenue: 0
    }
  ];

  const fallbackStats: EnergyStats = {
    total_pools: 5,
    total_capacity: 2750000,
    total_used: 1050000,
    total_available: 1200000,
    utilization_rate: 38.18,
    total_revenue: 32149.30,
    active_rentals: 606,
    avg_price_per_unit: 0.000376
  };

  const fallbackTransactions: EnergyTransaction[] = [
    {
      id: '1',
      user_id: 'user123',
      user_name: 'john_doe',
      pool_id: '1',
      pool_name: 'Prime Energy Pool A',
      amount: 1000,
      price: 0.00035,
      total_cost: 0.35,
      duration_hours: 24,
      status: 'active',
      created_at: '2024-07-13T06:00:00Z',
      expires_at: '2024-07-14T06:00:00Z'
    },
    {
      id: '2',
      user_id: 'user456',
      user_name: 'jane_smith',
      pool_id: '2',
      pool_name: 'Standard Energy Pool B',
      amount: 1500,
      price: 0.00040,
      total_cost: 0.60,
      duration_hours: 12,
      status: 'active',
      created_at: '2024-07-13T04:30:00Z',
      expires_at: '2024-07-13T16:30:00Z'
    },
    {
      id: '3',
      user_id: 'user789',
      user_name: 'bob_wilson',
      pool_id: '3',
      pool_name: 'Premium Energy Pool C',
      amount: 2000,
      price: 0.00030,
      total_cost: 0.60,
      duration_hours: 48,
      status: 'completed',
      created_at: '2024-07-11T10:00:00Z',
      expires_at: '2024-07-13T10:00:00Z'
    }
  ];

  // 실제 데이터 사용 (백엔드 연결 후 활성화)
  // const pools = poolStatusData?.pools || fallbackPools;
  // const stats = dashboardData?.stats || fallbackStats;
  
  // 현재는 fallback 데이터 사용 (백엔드 연결 전)
  const pools = fallbackPools;
  const stats = fallbackStats;
  const transactions = fallbackTransactions;

  const handleSettingsSave = (settings: EnergySettings) => {
    // TODO: 설정 저장 API 호출
    console.log('Saving settings:', settings);
  };

  const handleRefresh = () => {
    // TODO: 데이터 새로고침
    console.log('Refreshing data...');
  };

  const handleAddPool = () => {
    // TODO: 새 풀 추가 모달 또는 페이지로 이동
    console.log('Adding new pool...');
  };

  // 로딩 및 에러 처리
  if (isLoading) {
    return (
      <Sidebar>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">에너지 데이터를 불러오는 중...</span>
          </div>
        </div>
      </Sidebar>
    );
  }

  if (hasError) {
    return (
      <Sidebar>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <span className="ml-2 text-red-600">데이터를 불러오는 중 오류가 발생했습니다.</span>
          </div>
        </div>
      </Sidebar>
    );
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6">
        <EnergyManagementSection
          stats={stats}
          pools={pools}
          transactions={transactions}
          onSettingsSave={handleSettingsSave}
          onRefresh={handleRefresh}
          onAddPool={handleAddPool}
        />
      </div>
    </Sidebar>
  )
}
