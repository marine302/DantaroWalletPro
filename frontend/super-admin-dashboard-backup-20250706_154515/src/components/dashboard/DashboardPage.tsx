'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Users, DollarSign, Zap, Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { Table } from '@/components/ui/Table';
import { apiClient } from '@/lib/api';
import { formatCurrency, formatNumber, getStatusColor } from '@/lib/utils';
import { Partner } from '@/types';

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
  });

  const {
    data: systemHealth,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
    enabled: isAuthenticated,
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
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
              <p className="mt-1 text-sm text-red-700">
                Unable to load dashboard data. Please try refreshing the page.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
          value={stats ? formatNumber(stats.total_partners) : '—'}
          icon={Users}
          iconColor="text-blue-600"
          loading={statsLoading}
        />
        <StatCard
          title="Active Partners"
          value={stats ? formatNumber(stats.active_partners) : '—'}
          icon={TrendingUp}
          iconColor="text-green-600"
          loading={statsLoading}
        />
        <StatCard
          title="Total Revenue"
          value={stats ? formatCurrency(stats.total_revenue) : '—'}
          icon={DollarSign}
          iconColor="text-emerald-600"
          loading={statsLoading}
        />
        <StatCard
          title="Available Energy"
          value={stats ? formatNumber(stats.available_energy) : '—'}
          icon={Zap}
          iconColor="text-yellow-600"
          loading={statsLoading}
        />
      </div>

      {/* Additional stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          title="Daily Volume"
          value={stats ? formatCurrency(stats.daily_volume) : '—'}
          icon={Activity}
          iconColor="text-purple-600"
          loading={statsLoading}
        />
        <StatCard
          title="Energy Consumed"
          value={stats ? formatNumber(stats.total_energy_consumed) : '—'}
          icon={Zap}
          iconColor="text-orange-600"
          loading={statsLoading}
        />
        <StatCard
          title="Transactions Today"
          value={stats ? formatNumber(stats.total_transactions_today) : '—'}
          icon={TrendingUp}
          iconColor="text-indigo-600"
          loading={statsLoading}
        />
        <StatCard
          title="Active Wallets"
          value={stats ? formatNumber(stats.active_wallets) : '—'}
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
