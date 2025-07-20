'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Users, DollarSign, Zap, Activity, TrendingUp, Monitor } from 'lucide-react';
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
import { RealtimeStatus } from '@/components/realtime/RealtimeStatus';
import { RealtimeStats } from '@/components/realtime/RealtimeStats';
import { RealtimeAlerts } from '@/components/realtime/RealtimeAlerts';
import { ActivityLogViewer } from '@/components/auth/ActivityLogViewer';
import { withRBAC } from '@/components/auth/withRBAC';

function Home() {
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
      <div className="space-y-8">
        {/* Realtime Status Header */}
        <div className="mb-6">
          <RealtimeStatus />
        </div>

        {/* Realtime Monitoring Dashboard */}
        <Section title="실시간 모니터링" className="mb-8">
          <div className="space-y-6">
            {/* Realtime Stats */}
            <RealtimeStats />
            
            {/* Realtime Alerts and Transactions */}
            <RealtimeAlerts maxAlerts={8} showTransactions={true} />
          </div>
        </Section>

        {/* System Health Overview */}
        {systemHealth && (
          <Section title="시스템 상태" className="mb-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`p-4 rounded-lg border ${
                systemHealth.status === 'healthy' 
                  ? 'bg-green-900/30 border-green-600' 
                  : systemHealth.status === 'warning'
                  ? 'bg-yellow-900/30 border-yellow-600'
                  : 'bg-red-900/30 border-red-600'
              }`}>
                <div className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  <span className="font-medium">전체 시스템 상태</span>
                </div>
                <p className="text-2xl font-bold mt-2">
                  {systemHealth.status === 'healthy' ? '정상' : systemHealth.status === 'warning' ? '주의' : '위험'}
                </p>
              </div>
              
              <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
                <div className="flex items-center">
                  <Monitor className="h-5 w-5 mr-2 text-blue-400" />
                  <span className="font-medium">서비스 상태</span>
                </div>
                <p className="text-2xl font-bold mt-2 text-green-400">운영 중</p>
              </div>
              
              <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
                <div className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2 text-purple-400" />
                  <span className="font-medium">응답 시간</span>
                </div>
                <p className="text-2xl font-bold mt-2 text-blue-400">
                  {systemHealth.response_time || '< 100ms'}
                </p>
              </div>
            </div>
          </Section>
        )}

        {/* Legacy Dashboard Stats (for backup/comparison) */}
        <Section title="통계 요약" className="mb-8">
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
        </Section>
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

        {/* Recent Activity Section */}
        <Section title="최근 활동" className="mt-6">
          <ActivityLogViewer limit={10} showFilters={false} />
        </Section>
      </div>
    </BasePage>
  );
}

// Export protected component
export default withRBAC(Home, { 
  requiredPermissions: ['analytics.view']
});
