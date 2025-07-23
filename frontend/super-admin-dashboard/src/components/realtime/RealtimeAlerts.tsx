'use client';

import { realtimeManager } from '@/lib/realtime-manager';
import { AlertCircle, AlertTriangle, Bell, Clock, Info, TrendingUp, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { createDarkClasses } from '@/styles/dark-theme';
import { AlertPriority, TransactionStatus, TransactionType, WithTimestamp, SafeRecord } from '@/types/common';

// Local types for RealtimeAlerts
interface Alert extends WithTimestamp {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  priority?: AlertPriority;
}

interface Transaction extends WithTimestamp {
  id: string;
  type: TransactionType;
  status: TransactionStatus;
  amount: number;
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

  // 데이터 검증 함수들
  const _isAlert = (data: unknown): data is Alert => {
    if (!data || typeof data !== 'object') return false;
    const _obj = data as Record<string, unknown>;
    return (
      typeof obj.id === 'string' &&
      typeof obj.message === 'string' &&
      typeof obj.type === 'string' &&
      ['success', 'warning', 'error', 'info'].includes(obj.type as string) &&
      typeof obj.timestamp === 'string'
    );
  };

  const _isTransaction = (data: unknown): data is Transaction => {
    if (!data || typeof data !== 'object') return false;
    const _obj = data as Record<string, unknown>;
    return (
      typeof obj.id === 'string' &&
      typeof obj.type === 'string' &&
      typeof obj.status === 'string' &&
      ['pending', 'completed', 'failed', 'cancelled'].includes(obj.status as string) &&
      typeof obj.amount === 'number' &&
      typeof obj.timestamp === 'string'
    );
  };

  useEffect(() => {
    // Subscribe to realtime data
    const _unsubscribeAlerts = realtimeManager.subscribe('alerts', (data: unknown) => {
      try {
        if (Array.isArray(data)) {
          const _validAlerts = data.filter(isAlert);
          setAlerts(validAlerts.filter(alert => !dismissedAlerts.has(alert.id)).slice(0, maxAlerts));
        }
      } catch (error) {
        console.error('Error processing alerts:', error);
      }
    });

    const _unsubscribeTransactions = realtimeManager.subscribe('transactions', (data: unknown) => {
      try {
        if (Array.isArray(data)) {
          const _validTransactions = data.filter(isTransaction);
          setTransactions(validTransactions.slice(0, 10)); // 최대 10개
        }
      } catch (error) {
        console.error('Error processing transactions:', error);
      }
    });

    return () => {
      unsubscribeAlerts();
      unsubscribeTransactions();
    };
  }, [maxAlerts, dismissedAlerts]);

  const _dismissAlert = (alertId: string) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const _getAlertIcon = (type: Alert['type']) => {
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

  const _getAlertStyles = (type: Alert['type']) => {
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

  const _getTransactionStatusColor = (status: Transaction['status']) => {
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

  const _formatTimestamp = (timestamp: string) => {
    const _date = new Date(timestamp);
    const _now = new Date();
    const _diff = now.getTime() - date.getTime();

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleString();
  };

  const _formatCurrency = (amount: number) => {
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
        </div>
      )}
    </div>
  );
}
