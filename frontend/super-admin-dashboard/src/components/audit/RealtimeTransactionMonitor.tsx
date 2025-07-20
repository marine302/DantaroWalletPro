'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import { AuditEventType } from '@/types/audit';

interface RealtimeTransaction {
  id: string;
  timestamp: Date;
  type: AuditEventType;
  amount: number;
  currency: string;
  from_address: string;
  to_address: string;
  status: 'pending' | 'completed' | 'failed';
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  partner_id?: string;
  user_id?: string;
  flags: string[];
}

interface MonitoringMetrics {
  total_transactions_24h: number;
  suspicious_transactions: number;
  blocked_transactions: number;
  average_risk_score: number;
  high_risk_transactions: number;
}

export function RealtimeTransactionMonitor() {
  const [transactions, setTransactions] = useState<RealtimeTransaction[]>([]);
  const [metrics, setMetrics] = useState<MonitoringMetrics>({
    total_transactions_24h: 0,
    suspicious_transactions: 0,
    blocked_transactions: 0,
    average_risk_score: 0,
    high_risk_transactions: 0
  });
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [alertsEnabled, setAlertsEnabled] = useState(true);

  // WebSocket 연결 for 실시간 트랜잭션 데이터
  const [isConnected, setIsConnected] = useState(false);
  
  function sendMessage(data: any) {
    console.log('Mock sendMessage:', data);
  }

  function handleWebSocketMessage(data: any) {
    if (data.type === 'transaction_update') {
      const newTransaction: RealtimeTransaction = {
        ...data.transaction,
        timestamp: new Date(data.transaction.timestamp)
      };
      
      setTransactions(prev => [newTransaction, ...prev.slice(0, 49)]); // 최근 50개만 유지
      
      // 고위험 거래 알림
      if (newTransaction.risk_level === 'critical' && alertsEnabled) {
        showCriticalAlert(newTransaction);
      }
    } else if (data.type === 'metrics_update') {
      setMetrics(data.metrics);
    }
  }

  function showCriticalAlert(transaction: RealtimeTransaction) {
    // 브라우저 알림
    if (Notification.permission === 'granted') {
      new Notification('🚨 Critical Risk Transaction Detected', {
        body: `Transaction ${transaction.id}: ${transaction.amount} ${transaction.currency}`,
        icon: '/favicon.ico'
      });
    }
    
    // 사운드 알림 (옵션)
    const audio = new Audio('/sounds/alert.mp3');
    audio.play().catch(() => {
      console.log('Alert sound playback failed');
    });
  }

  function handleEmergencyBlock(transactionId: string) {
    if (confirm('⚠️ Emergency block this transaction? This action cannot be undone.')) {
      sendMessage({
        type: 'emergency_block',
        transaction_id: transactionId,
        timestamp: new Date().toISOString()
      });
    }
  }

  function getRiskBadgeColor(level: string) {
    switch (level) {
      case 'low': return 'bg-green-900/30 text-green-300';
      case 'medium': return 'bg-yellow-900/30 text-yellow-300';
      case 'high': return 'bg-orange-900/30 text-orange-300';
      case 'critical': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  }

  function getStatusBadgeColor(status: string) {
    switch (status) {
      case 'completed': return 'bg-green-900/30 text-green-300';
      case 'pending': return 'bg-blue-900/30 text-blue-300';
      case 'failed': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  }

  useEffect(() => {
    // 알림 권한 요청
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // 모니터링 시작
    if (isMonitoring && isConnected) {
      sendMessage({ type: 'subscribe_transactions' });
      sendMessage({ type: 'subscribe_metrics' });
    }

    return () => {
      if (isConnected) {
        sendMessage({ type: 'unsubscribe_transactions' });
        sendMessage({ type: 'unsubscribe_metrics' });
      }
    };
  }, [isMonitoring, isConnected, sendMessage]);

  return (
    <Section>
      <div className="space-y-6">
        {/* 헤더 및 컨트롤 */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-white">
              🔍 실시간 트랜잭션 모니터링
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              WebSocket Status: 
              <span className={`ml-2 ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
              </span>
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setAlertsEnabled(!alertsEnabled)}
              className={`${alertsEnabled ? 'bg-green-600' : 'bg-gray-600'}`}
            >
              {alertsEnabled ? '🔔 Alerts ON' : '🔕 Alerts OFF'}
            </Button>
            <Button
              onClick={() => setIsMonitoring(!isMonitoring)}
              className={`${isMonitoring ? 'bg-blue-600' : 'bg-gray-600'}`}
            >
              {isMonitoring ? '⏸️ Pause' : '▶️ Resume'}
            </Button>
          </div>
        </div>

        {/* 실시간 메트릭 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
            <p className="text-xs text-gray-400">24h Transactions</p>
            <p className="text-xl font-bold text-white">{metrics.total_transactions_24h.toLocaleString()}</p>
          </div>
          <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-lg p-3">
            <p className="text-xs text-yellow-400">Suspicious</p>
            <p className="text-xl font-bold text-yellow-300">{metrics.suspicious_transactions}</p>
          </div>
          <div className="bg-red-900/20 border border-red-700/30 rounded-lg p-3">
            <p className="text-xs text-red-400">Blocked</p>
            <p className="text-xl font-bold text-red-300">{metrics.blocked_transactions}</p>
          </div>
          <div className="bg-blue-900/20 border border-blue-700/30 rounded-lg p-3">
            <p className="text-xs text-blue-400">Avg Risk Score</p>
            <p className="text-xl font-bold text-blue-300">{metrics.average_risk_score.toFixed(1)}</p>
          </div>
          <div className="bg-orange-900/20 border border-orange-700/30 rounded-lg p-3">
            <p className="text-xs text-orange-400">High Risk</p>
            <p className="text-xl font-bold text-orange-300">{metrics.high_risk_transactions}</p>
          </div>
        </div>

        {/* 실시간 트랜잭션 스트림 */}
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-700">
            <h4 className="font-semibold text-white">🚨 Live Transaction Stream</h4>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {transactions.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                No transactions detected yet...
              </div>
            ) : (
              <div className="space-y-1">
                {transactions.map((tx) => (
                  <div
                    key={tx.id}
                    className={`p-3 border-l-4 ${
                      tx.risk_level === 'critical' ? 'border-red-500 bg-red-900/10' :
                      tx.risk_level === 'high' ? 'border-orange-500 bg-orange-900/10' :
                      tx.risk_level === 'medium' ? 'border-yellow-500 bg-yellow-900/10' :
                      'border-green-500 bg-green-900/10'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={getRiskBadgeColor(tx.risk_level)}>
                            {tx.risk_level.toUpperCase()}
                          </Badge>
                          <Badge className={getStatusBadgeColor(tx.status)}>
                            {tx.status.toUpperCase()}
                          </Badge>
                          <span className="text-xs text-gray-400">
                            {tx.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm text-white font-mono">
                          {tx.amount} {tx.currency} | {tx.from_address.slice(0, 8)}...→{tx.to_address.slice(0, 8)}...
                        </p>
                        <p className="text-xs text-gray-400">
                          Risk Score: {tx.risk_score} | Type: {tx.type}
                        </p>
                        {tx.flags.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {tx.flags.map((flag, idx) => (
                              <Badge key={idx} className="bg-red-900/30 text-red-300 text-xs">
                                {flag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      {tx.risk_level === 'critical' && tx.status === 'pending' && (
                        <Button
                          onClick={() => handleEmergencyBlock(tx.id)}
                          className="bg-red-600 hover:bg-red-700 text-xs px-2 py-1"
                        >
                          🚫 BLOCK
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}
