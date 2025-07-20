'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { realtimeManager } from '@/lib/realtime-manager';
import { AlertCircle, Clock, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';

interface RealtimeStatusProps {
  className?: string;
}

export function RealtimeStatus({ className = '' }: RealtimeStatusProps) {
  // Mock WebSocket URL을 개발 중에 사용
  const useMockData = process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true';
  const wsUrl = useMockData
    ? 'ws://localhost:3002'
    : process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

  const { isConnected, isConnecting, error, reconnectCount, subscribe } = useWebSocket(wsUrl);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [dataCount, setDataCount] = useState(0);

  useEffect(() => {
    // Subscribe to all realtime data types and forward to realtime manager
    const unsubscribers = [
      subscribe('systemStats', (data) => {
        realtimeManager.updateData('systemStats', data);
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
      }),
      subscribe('dashboardStats', (data) => {
        realtimeManager.updateData('dashboardStats', data);
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
      }),
      subscribe('alert', (data) => {
        // Handle single alert - add to existing alerts array
        const currentAlerts = realtimeManager.getData('alerts');
        const alertsArray = Array.isArray(currentAlerts) ? currentAlerts : [];
        const newAlerts = [data, ...alertsArray.slice(0, 9)]; // Keep last 10 alerts
        realtimeManager.updateData('alerts', newAlerts);
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
      }),
      subscribe('energyMarket', (data) => {
        realtimeManager.updateData('energyMarket', data);
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
      }),
      subscribe('transaction', (data) => {
        // Handle single transaction - add to existing transactions array
        const currentTransactions = realtimeManager.getData('transactions');
        const transactionsArray = Array.isArray(currentTransactions) ? currentTransactions : [];
        const newTransactions = [data, ...transactionsArray.slice(0, 19)]; // Keep last 20 transactions
        realtimeManager.updateData('transactions', newTransactions);
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
      })
    ];

    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  }, [subscribe]);

  const getStatusColor = () => {
    if (isConnected) return 'text-green-400';
    if (isConnecting) return 'text-yellow-400';
    if (error) return 'text-red-400';
    return 'text-gray-400';
  };

  const getStatusText = () => {
    if (isConnected) return 'Connected';
    if (isConnecting) return 'Connecting...';
    if (error) return 'Disconnected';
    return 'Offline';
  };

  const getStatusIcon = () => {
    if (isConnected) return <Wifi className="w-4 h-4" />;
    if (error) return <WifiOff className="w-4 h-4" />;
    return <AlertCircle className="w-4 h-4" />;
  };

  const formatLastUpdate = () => {
    if (!lastUpdate) return 'No data';
    const now = new Date();
    const diff = now.getTime() - lastUpdate.getTime();
    if (diff < 1000) return 'Just now';
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return lastUpdate.toLocaleTimeString();
  };

  return (
    <div className={`flex items-center space-x-4 p-3 bg-gray-800 rounded-lg border border-gray-700 ${className}`}>
      <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
        {getStatusIcon()}
        <span className="text-sm font-medium">{getStatusText()}</span>
      </div>

      {isConnected && (
        <div className="flex items-center space-x-4 text-xs text-gray-400">
          <div className="flex items-center space-x-1">
            <Clock className="w-3 h-3" />
            <span>{formatLastUpdate()}</span>
          </div>
          <div>
            <span>Updates: {dataCount}</span>
          </div>
        </div>
      )}

      {reconnectCount > 0 && (
        <span className="text-xs text-orange-400">
          Reconnects: {reconnectCount}
        </span>
      )}

      {error && (
        <span className="text-xs text-red-400">
          {error}
        </span>
      )}
    </div>
  );
}
