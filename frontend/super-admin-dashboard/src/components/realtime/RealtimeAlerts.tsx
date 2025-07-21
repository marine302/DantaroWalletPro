'use client';

import { realtimeManager } from '@/lib/realtime-manager';
import { AlertCircle, AlertTriangle, Bell, Clock, Info, TrendingUp, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { createDarkClasses } from '@/styles/dark-theme';

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
}

interface Transaction {
  id: string;
  type: string;
  amount: number;
  status: 'pending' | 'completed' | 'failed';
  timestamp: string;
}

interface RealtimeAlertsProps {
  className?: string;
  maxAlerts?: number;
  showTransactions?: boolean;
}

export function RealtimeAlerts({
  className = '',
  maxAlerts = 10,
  showTransactions = true
}: RealtimeAlertsProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  // Type guard functions
  const isAlert = (item: unknown): item is Alert => {
    if (!item || typeof item !== 'object') return false;
    const obj = item as Record<string, unknown>;
    return typeof obj.message === 'string' &&
      typeof obj.type === 'string' &&
      ['error', 'warning', 'info'].includes(obj.type) &&
      typeof obj.id === 'string' &&
      typeof obj.timestamp === 'string';
  };

  const isTransaction = (item: unknown): item is Transaction => {
    if (!item || typeof item !== 'object') return false;
    const obj = item as Record<string, unknown>;
    return typeof obj.amount === 'number' &&
      typeof obj.status === 'string' &&
      ['pending', 'completed', 'failed'].includes(obj.status) &&
      typeof obj.id === 'string' &&
      typeof obj.timestamp === 'string' &&
      typeof obj.type === 'string';
  };

  useEffect(() => {
    // Subscribe to realtime alerts (both singular and plural forms)
    const unsubscribeAlerts = realtimeManager.subscribe('alerts', (data: Alert[]) => {
      if (Array.isArray(data)) {
        setAlerts(data.filter(alert => !dismissedAlerts.has(alert.id)).slice(0, maxAlerts));
      }
    });

    const unsubscribeAlert = realtimeManager.subscribe('alert', (data: Alert) => {
      if (data && typeof data === 'object' && isAlert(data)) {
        setAlerts(prev => {
          const filtered = prev.filter(alert => alert.id !== data.id && !dismissedAlerts.has(alert.id));
          return [data, ...filtered].slice(0, maxAlerts);
        });
      }
    });

    // Subscribe to realtime transactions (both singular and plural forms)
    const unsubscribeTransactions = realtimeManager.subscribe('transactions', (data: Transaction[]) => {
      if (Array.isArray(data)) {
        setTransactions(data.slice(0, maxAlerts));
      }
    });

    const unsubscribeTransaction = realtimeManager.subscribe('transaction', (data: Transaction) => {
      if (data && typeof data === 'object' && isTransaction(data)) {
        setTransactions(prev => {
          const filtered = prev.filter(tx => tx.id !== data.id);
          return [data, ...filtered].slice(0, maxAlerts);
        });
      }
    });

    // Get initial data if available
    const initialAlerts = realtimeManager.getData('alerts');
    if (initialAlerts && Array.isArray(initialAlerts)) {
      const validAlerts = initialAlerts.filter(isAlert);
      setAlerts(validAlerts.filter(alert => !dismissedAlerts.has(alert.id)).slice(0, maxAlerts));
    }

    const initialTransactions = realtimeManager.getData('transactions');
    if (initialTransactions && Array.isArray(initialTransactions)) {
      const validTransactions = initialTransactions.filter(isTransaction);
      setTransactions(validTransactions.slice(0, maxAlerts));
    }

    return () => {
      unsubscribeAlerts();
      unsubscribeAlert();
      unsubscribeTransactions();
      unsubscribeTransaction();
    };
  }, [dismissedAlerts, maxAlerts]);

  const dismissAlert = (alertId: string) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case 'info':
        return <Info className="w-4 h-4 text-blue-400" />;
      default:
        return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const getAlertStyles = (type: Alert['type']) => {
    switch (type) {
      case 'error':
        return 'bg-red-900/50 border-red-700 text-red-100';
      case 'warning':
        return 'bg-yellow-900/50 border-yellow-700 text-yellow-100';
      case 'info':
        return 'bg-blue-900/50 border-blue-700 text-blue-100';
      default:
        return 'bg-gray-900/50 border-gray-700 text-gray-100';
    }
  };

  const getTransactionStatusColor = (status: Transaction['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-400';
      case 'pending':
        return 'text-yellow-400';
      case 'failed':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 ${className}`}>
      {/* Alerts Section */}
      <div className={`${createDarkClasses.card()} p-6`}>
        <div className="flex items-center space-x-2 mb-4">
          <Bell className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">System Alerts</h3>
          {alerts.length > 0 && (
            <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
              {alerts.length}
            </span>
          )}
        </div>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {alerts.length === 0 ? (
            <p className="text-gray-200 text-center py-4">No alerts</p>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className={`flex items-start space-x-3 p-3 rounded-lg border ${getAlertStyles(alert.type)}`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getAlertIcon(alert.type)}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{alert.message}</p>
                  <div className="flex items-center space-x-1 mt-1">
                    <Clock className="w-3 h-3 text-gray-400" />
                    <p className="text-xs text-gray-400">
                      {formatTimestamp(alert.timestamp)}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => dismissAlert(alert.id)}
                  className="flex-shrink-0 text-gray-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent Transactions Section */}
      {showTransactions && (
        <div className={`${createDarkClasses.card()} p-6`}>
          <div className="flex items-center space-x-2 mb-4">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <h3 className="text-lg font-semibold text-white">Recent Transactions</h3>
            {transactions.length > 0 && (
              <span className="bg-green-600 text-white text-xs px-2 py-1 rounded-full">
                {transactions.length}
              </span>
            )}
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {transactions.length === 0 ? (
              <p className="text-gray-200 text-center py-4">No recent transactions</p>
            ) : (
              transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-white">
                        {transaction.type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className={`text-sm font-semibold ${getTransactionStatusColor(transaction.status)}`}>
                        {transaction.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-sm text-gray-300">
                        {formatCurrency(transaction.amount)}
                      </span>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {formatTimestamp(transaction.timestamp)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
