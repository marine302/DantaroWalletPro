'use client';

import { Card } from '@/components/ui/Card';
import { realtimeManager } from '@/lib/realtime-manager';
import { Activity, Database, DollarSign, TrendingUp, Users, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';

interface RealtimeStatsProps {
  className?: string;
}

interface SystemStats {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  activeConnections: number;
}

interface DashboardStats {
  activeUsers: number;
  totalTransactions: number;
  energyTrading: number;
  revenue: number;
}

export function RealtimeStats({ className = '' }: RealtimeStatsProps) {
  const [systemStats, setSystemStats] = useState<SystemStats>({
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    activeConnections: 0
  });

  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    activeUsers: 0,
    totalTransactions: 0,
    energyTrading: 0,
    revenue: 0
  });

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Subscribe to realtime system stats
    const unsubscribeSystem = realtimeManager.subscribe('systemStats', (data: SystemStats) => {
      setSystemStats(data);
      setIsLoading(false);
    });

    // Subscribe to realtime dashboard stats
    const unsubscribeDashboard = realtimeManager.subscribe('dashboardStats', (data: DashboardStats) => {
      setDashboardStats(data);
      setIsLoading(false);
    });

    // Get initial data if available
    const initialSystemData = realtimeManager.getData('systemStats');
    if (initialSystemData) {
      setSystemStats(initialSystemData as SystemStats);
      setIsLoading(false);
    }

    const initialDashboardData = realtimeManager.getData('dashboardStats');
    if (initialDashboardData) {
      setDashboardStats(initialDashboardData as DashboardStats);
      setIsLoading(false);
    }

    return () => {
      unsubscribeSystem();
      unsubscribeDashboard();
    };
  }, []);

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatCurrency = (num: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-400';
    if (percentage >= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  if (isLoading) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-800 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-700 rounded mb-2"></div>
            <div className="h-8 bg-gray-700 rounded mb-2"></div>
            <div className="h-3 bg-gray-700 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* System Statistics */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">System Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">CPU Usage</p>
                <p className={`text-2xl font-bold ${getUsageColor(systemStats.cpuUsage)}`}>
                  {systemStats.cpuUsage.toFixed(1)}%
                </p>
              </div>
              <Activity className="w-8 h-8 text-blue-400" />
            </div>
          </Card>

          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Memory Usage</p>
                <p className={`text-2xl font-bold ${getUsageColor(systemStats.memoryUsage)}`}>
                  {systemStats.memoryUsage.toFixed(1)}%
                </p>
              </div>
              <Database className="w-8 h-8 text-green-400" />
            </div>
          </Card>

          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Disk Usage</p>
                <p className={`text-2xl font-bold ${getUsageColor(systemStats.diskUsage)}`}>
                  {systemStats.diskUsage.toFixed(1)}%
                </p>
              </div>
              <Database className="w-8 h-8 text-yellow-400" />
            </div>
          </Card>

          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active Connections</p>
                <p className="text-2xl font-bold text-blue-400">
                  {formatNumber(systemStats.activeConnections)}
                </p>
              </div>
              <Activity className="w-8 h-8 text-purple-400" />
            </div>
          </Card>
        </div>
      </div>

      {/* Business Statistics */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Business Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active Users</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatNumber(dashboardStats.activeUsers)}
                </p>
              </div>
              <Users className="w-8 h-8 text-green-400" />
            </div>
          </Card>

          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Transactions</p>
                <p className="text-2xl font-bold text-blue-400">
                  {formatNumber(dashboardStats.totalTransactions)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-400" />
            </div>
          </Card>

          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Energy Trading</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {formatNumber(dashboardStats.energyTrading)} kWh
                </p>
              </div>
              <Zap className="w-8 h-8 text-yellow-400" />
            </div>
          </Card>

          <Card className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Revenue</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatCurrency(dashboardStats.revenue)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-400" />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
