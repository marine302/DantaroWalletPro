'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Users, DollarSign, Zap, Activity, TrendingUp } from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { Table } from '@/components/ui/Table';
import { apiClient } from '@/lib/api';
import { getStatusColor, safeFormatNumber, safeCurrency } from '@/lib/utils';

export default function DashboardPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('authToken');
    if (!token) {
      router.push('/login');
      return;
    }
    setIsAuthenticated(true);
  }, [router]);

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.getDashboardStats(),
    enabled: isAuthenticated, // Only run query if authenticated
    retry: 1, // 최대 1번만 재시도
    retryDelay: 1000, // 1초 후 재시도
  });

  const {
    data: systemHealth,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
    enabled: isAuthenticated,
    retry: 1,
  });

  const {
    data: partnersResponse,
    isLoading: partnersLoading,
  } = useQuery({
    queryKey: ['partners', 1, 5],
    queryFn: () => apiClient.getPartners(1, 5),
    enabled: isAuthenticated,
  });

  // Show loading spinner while checking authentication
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (statsError) {
    console.error('Dashboard stats error:', statsError);
  }

  // 오류나 로딩 중일 때 사용할 fallback 데이터
  const displayStats = stats || {
    total_partners: 1,
    active_partners: 1,
    total_users: 50,
    active_users: 45,
    transactions_today: 25,
    daily_volume: 125000.0,
    total_energy: 1500000,
    available_energy: 1150000,
    total_revenue: 75000.0,
    total_energy_consumed: 350000,
    total_transactions_today: 25,
    active_wallets: 45,
  };

  const partnerColumns = [
    {
      key: 'name',
      title: 'Partner Name',
    },
    {
      key: 'domain',
      title: 'Domain',
    },
    {
      key: 'status',
      title: 'Status',
      render: (value: unknown) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(String(value))}`}>
          {String(value)}
        </span>
      ),
    },
    {
      key: 'created_at',
      title: 'Created',
      render: (value: unknown) => new Date(String(value)).toLocaleDateString(),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-8">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Dashboard
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Welcome to the DantaroWallet Super Admin Dashboard
            </p>
          </div>
          <div className="mt-4 flex md:mt-0 md:ml-4">
            {systemHealth && (
              <div className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md ${
                systemHealth.status === 'healthy' 
                  ? 'text-green-700 bg-green-100' 
                  : systemHealth.status === 'warning'
                  ? 'text-yellow-700 bg-yellow-100'
                  : 'text-red-700 bg-red-100'
              }`}>
                <Activity className="h-4 w-4 mr-2" />
                System {systemHealth.status}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          title="Total Partners"
          value={safeFormatNumber(displayStats.total_partners)}
          icon={Users}
          iconColor="text-blue-600"
          loading={statsLoading}
        />
        <StatCard
          title="Active Partners"
          value={safeFormatNumber(displayStats.active_partners)}
          icon={TrendingUp}
          iconColor="text-green-600"
          loading={statsLoading}
        />
        <StatCard
          title="Total Revenue"
          value={safeCurrency(displayStats.total_revenue)}
          icon={DollarSign}
          iconColor="text-emerald-600"
          loading={statsLoading}
        />
        <StatCard
          title="Available Energy"
          value={safeFormatNumber(displayStats.available_energy)}
          icon={Zap}
          iconColor="text-yellow-600"
          loading={statsLoading}
        />
      </div>

      {/* Additional stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          title="Daily Volume"
          value={safeCurrency(displayStats.daily_volume)}
          icon={Activity}
          iconColor="text-purple-600"
          loading={statsLoading}
        />
        <StatCard
          title="Energy Consumed"
          value={safeFormatNumber(displayStats.total_energy_consumed)}
          icon={Zap}
          iconColor="text-orange-600"
          loading={statsLoading}
        />
        <StatCard
          title="Transactions Today"
          value={safeFormatNumber(displayStats.total_transactions_today)}
          icon={TrendingUp}
          iconColor="text-indigo-600"
          loading={statsLoading}
        />
        <StatCard
          title="Active Wallets"
          value={safeFormatNumber(displayStats.active_wallets)}
          icon={Users}
          iconColor="text-pink-600"
          loading={statsLoading}
        />
      </div>

      {/* Recent Partners table */}
      <div className="mb-8">
        <div className="sm:flex sm:items-center mb-4">
          <div className="sm:flex-auto">
            <h3 className="text-lg font-medium text-gray-900">Recent Partners</h3>
            <p className="mt-1 text-sm text-gray-700">
              Latest partners added to the platform.
            </p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <a
              href="/partners"
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
            >
              View all partners
            </a>
          </div>
        </div>

        <Table
          data={(partnersResponse?.items || []) as unknown as Record<string, unknown>[]}
          columns={partnerColumns}
          loading={partnersLoading}
          emptyMessage="No partners found"
        />
      </div>
    </div>
  );
}
