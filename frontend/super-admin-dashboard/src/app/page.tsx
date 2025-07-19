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
import { useI18n } from '@/contexts/I18nContext';
import { BasePage } from '@/components/ui/BasePage';

export default function Home() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const { t } = useI18n();

  useEffect(() => {
    // 개발 환경에서는 인증 우회
    if (process.env.NODE_ENV === 'development') {
      setIsAuthenticated(true);
      return;
    }
    
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
    error: statsError,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.getDashboardStats(),
    enabled: isAuthenticated,
    retry: 3,
    retryDelay: 1000,
  });

  const {
    data: systemHealth,
    error: healthError,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: process.env.NODE_ENV === 'development' ? 60000 : 30000, // 개발환경에서는 1분으로 연장
    enabled: isAuthenticated,
    retry: 3,
  });

  const {
    data: partnersResponse,
    isLoading: partnersLoading,
    error: partnersError,
  } = useQuery({
    queryKey: ['partners'],
    queryFn: () => apiClient.getPartners(1, 5),
    enabled: isAuthenticated,
    retry: 3,
    retryDelay: 1000,
  });

  // 개발 환경에서 API 오류 디버깅
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      if (statsError) {
        console.error('Dashboard Stats Error:', statsError);
      }
      if (healthError) {
        console.error('System Health Error:', healthError);
      }
      if (partnersError) {
        console.error('Partners Error:', partnersError);
      }
      if (stats) {
        console.log('Dashboard Stats:', stats);
      }
      if (systemHealth) {
        console.log('System Health:', systemHealth);
      }
      if (partnersResponse) {
        console.log('Partners:', partnersResponse);
      }
    }
  }, [statsError, healthError, partnersError, stats, systemHealth, partnersResponse]);

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
    <BasePage
      title={t.dashboard.title}
      description={t.dashboard.description}
    >
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
              {t.dashboard.systemHealth} {systemHealth.status === 'healthy' ? t.dashboard.healthy : t.dashboard.critical}
            </div>
          </div>
        )}

        {/* Main Stats Grid */}
        <div className={gridLayouts.statsGrid}>
          <StatCard
            title={t.dashboard.totalPartners}
            value={safeFormatNumber(displayStats.total_partners)}
            icon={<Users className="h-5 w-5" />}
          />
          <StatCard
            title={t.dashboard.activePartners}
            value={safeFormatNumber(displayStats.active_partners)}
            icon={<TrendingUp className="h-5 w-5" />}
            trend="up"
          />
          <StatCard
            title={t.dashboard.totalRevenue}
            value={safeCurrency(displayStats.total_revenue)}
            icon={<DollarSign className="h-5 w-5" />}
            trend="up"
          />
          <StatCard
            title={t.dashboard.availableEnergy}
            value={safeFormatNumber(displayStats.available_energy)}
            icon={<Zap className="h-5 w-5" />}
          />
        </div>

        {/* Secondary Stats Grid */}
        <div className={gridLayouts.statsGrid}>
          <StatCard
            title={t.dashboard.dailyVolume}
            value={safeCurrency(displayStats.daily_volume)}
            icon={<Activity className="h-5 w-5" />}
          />
          <StatCard
            title={t.dashboard.totalEnergy}
            value={safeFormatNumber(1500000)}
            icon={<Zap className="h-5 w-5" />}
          />
          <StatCard
            title={t.dashboard.transactionsToday}
            value={safeFormatNumber(displayStats.total_transactions_today)}
            icon={<TrendingUp className="h-5 w-5" />}
            trend="up"
          />
          <StatCard
            title={t.dashboard.activeWallets}
            value={safeFormatNumber(displayStats.active_wallets)}
            icon={<Users className="h-5 w-5" />}
          />
        </div>

        {/* Recent Partners Section */}
        <Section title={t.dashboard.recentPartners}>
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
                      {t.common.viewDetails}
                    </Button>
                  </div>
                </div>
              ))}
              <div className="text-center pt-4">
                <Button onClick={() => router.push('/partners')}>
                  {t.common.viewAll}
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-400">{t.dashboard.noPartnersFound}</p>
              <Button 
                onClick={() => router.push('/partners')}
                className="mt-4"
              >
                {t.dashboard.addPartner}
              </Button>
            </div>
          )}
        </Section>
      </div>
    </BasePage>
  );
}
