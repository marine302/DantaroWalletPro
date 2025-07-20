'use client';

import { realtimeManager } from '@/lib/realtime-manager';
import { AlertCircle, Clock, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';

interface RealtimeStatusProps {
  className?: string;
}

export function RealtimeStatus({ className = '' }: RealtimeStatusProps) {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [dataCount, setDataCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Subscribe to all realtime data types
    const unsubscribers = [
      realtimeManager.subscribe('systemStats', () => {
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
        setIsConnected(true);
        setError(null);
      }),
      realtimeManager.subscribe('dashboardStats', () => {
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
        setIsConnected(true);
        setError(null);
      }),
      realtimeManager.subscribe('alerts', () => {
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
        setIsConnected(true);
        setError(null);
      }),
      realtimeManager.subscribe('energyMarket', () => {
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
        setIsConnected(true);
        setError(null);
      }),
      realtimeManager.subscribe('transactions', (data) => {
        // Handle single transaction - add to existing transactions array
        const currentTransactions = realtimeManager.getData('transactions');
        const transactionsArray = Array.isArray(currentTransactions) ? currentTransactions : [];
        const newTransactions = [data, ...transactionsArray.slice(0, 19)]; // Keep last 20 transactions
        realtimeManager.updateData('transactions', newTransactions);
        setLastUpdate(new Date());
        setDataCount(prev => prev + 1);
        setIsConnected(true);
        setError(null);
      })
    ];

    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  }, []); // dependency 제거

  const getStatusColor = () => {
    if (isConnected) return 'text-green-400';
    if (error) return 'text-red-400';
    return 'text-gray-400';
  };

  const getStatusText = () => {
    if (isConnected) return 'Connected';
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

      {error && (
        <span className="text-xs text-red-400">
          {error}
        </span>
      )}
    </div>
  );
}
