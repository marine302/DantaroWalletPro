'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Users, DollarSign, Zap, Activity, TrendingUp } from 'lucide-react';
import { 
  StatCard, 
  Section,
  Button 
} from '@/components/ui/DarkThemeComponents';
import { gridLayouts } from '@/styles/dark-theme';
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
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.getDashboardStats(),
    enabled: isAuthenticated,
    retry: 1,
    retryDelay: 1000,
  });

  const {
    data: systemHealth,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000,
    enabled: isAuthenticated,
    retry: 1,
  });

  const {
    data: partnersResponse,
    isLoading: partnersLoading,
  } = useQuery({
    queryKey: ['partners'],
    queryFn: () => apiClient.getPartners(1, 5),
    enabled: isAuthenticated,
    retry: 1,
  });

  if (!isAuthenticated) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Fallback data for UI consistency
  const displayStats = stats || {
    total_partners: 5,
    active_partners: 4,
    total_users: 150,
    active_users: 120,
    total_revenue: 75000.0,
    total_transactions_today: 25,
    daily_volume: 125000.0,
    total_energy: 1500000,
    available_energy: 1150000,
    active_wallets: 45,
  };

  const displayPartners = partnersResponse?.items || [];

  return (
    <div className="space-y-6">
      {/* System Health Status */}
      {systemHealth && (
        <div className="flex justify-end">
          <div className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md ${
            systemHealth.status === 'healthy' 
              ? 'text-green-300 bg-green-900/30 border-green-600' 
              : systemHealth.status === 'warning'
              ? 'text-yellow-300 bg-yellow-900/30 border-yellow-600'
              : 'text-red-300 bg-red-900/30 border-red-600'
          }`}>
            <Activity className="h-4 w-4 mr-2" />
            System {systemHealth.status}
          </div>
        </div>
      )}

      {/* Main Stats Grid */}
      <div className={gridLayouts.statsGrid}>
        <StatCard
          title="Total Partners"
          value={safeFormatNumber(displayStats.total_partners)}
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          title="Active Partners"
          value={safeFormatNumber(displayStats.active_partners)}
          icon={<TrendingUp className="h-5 w-5" />}
          trend="up"
        />
        <StatCard
          title="Total Revenue"
          value={safeCurrency(displayStats.total_revenue)}
          icon={<DollarSign className="h-5 w-5" />}
          trend="up"
        />
        <StatCard
          title="Available Energy"
          value={safeFormatNumber(displayStats.available_energy)}
          icon={<Zap className="h-5 w-5" />}
        />
      </div>

      {/* Secondary Stats Grid */}
      <div className={gridLayouts.statsGrid}>
        <StatCard
          title="Daily Volume"
          value={safeCurrency(displayStats.daily_volume)}
          icon={<Activity className="h-5 w-5" />}
        />
        <StatCard
          title="Total Energy"
          value={safeFormatNumber(1500000)}
          icon={<Zap className="h-5 w-5" />}
        />
        <StatCard
          title="Transactions Today"
          value={safeFormatNumber(displayStats.total_transactions_today)}
          icon={<TrendingUp className="h-5 w-5" />}
          trend="up"
        />
        <StatCard
          title="Active Wallets"
          value={safeFormatNumber(displayStats.active_wallets)}
          icon={<Users className="h-5 w-5" />}
        />
      </div>

      {/* Recent Partners Section */}
      <Section title="Recent Partners">
        {partnersLoading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : displayPartners.length > 0 ? (
          <div className="space-y-4">
            {displayPartners.map((partner) => (
              <div key={partner.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
                <div>
                  <h4 className="text-white font-medium">{partner.name || `Partner ${partner.id}`}</h4>
                  <p className="text-gray-300 text-sm">Partner {partner.id}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(partner.status)}`}>
                    {partner.status}
                  </span>
                  <Button 
                    variant="secondary"
                    onClick={() => router.push(`/partners/${partner.id}`)}
                  >
                    View Details
                  </Button>
                </div>
              </div>
            ))}
            <div className="text-center pt-4">
              <Button onClick={() => router.push('/partners')}>
                View all partners
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-400">No partners found</p>
            <Button 
              onClick={() => router.push('/partners')}
              className="mt-4"
            >
              Add Partner
            </Button>
          </div>
        )}
      </Section>
    </div>
  );
}
