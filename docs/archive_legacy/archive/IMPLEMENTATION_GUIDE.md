# 🔧 Super Admin Dashboard 구현 가이드

**참조 문서**: DEVELOPMENT_ROADMAP.md  
**목적**: 실제 개발 시 참고할 상세 구현 가이드

## 🎯 **Phase 1: 트랜잭션 감사 시스템 구현**

### **1.1 실시간 트랜잭션 모니터링 (3일)**

#### **Step 1: 컴포넌트 구조 설계**
```typescript
// src/app/audit-compliance/components/RealtimeTransactionMonitor.tsx
'use client';

import { useState, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { TransactionAlert, Transaction } from '@/types/audit.types';

interface RealtimeTransactionMonitorProps {
  partnerId?: string;
  alertThreshold?: number;
}

export function RealtimeTransactionMonitor({ 
  partnerId, 
  alertThreshold = 5 
}: RealtimeTransactionMonitorProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [alerts, setAlerts] = useState<TransactionAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  // WebSocket 연결
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(
    process.env.NEXT_PUBLIC_WS_URL + '/audit'
  );

  // 실시간 데이터 처리
  useEffect(() => {
    if (lastMessage !== null) {
      const data = JSON.parse(lastMessage.data);
      
      switch (data.type) {
        case 'transaction':
          setTransactions(prev => [data.payload, ...prev.slice(0, 99)]);
          break;
        case 'suspicious_activity':
          setAlerts(prev => [data.payload, ...prev.slice(0, 19)]);
          // 긴급 알림 표시
          showUrgentAlert(data.payload);
          break;
      }
    }
  }, [lastMessage]);

  const showUrgentAlert = (alert: TransactionAlert) => {
    // 브라우저 알림 또는 모달 표시
    if (alert.severity === 'critical') {
      new Notification(`긴급: ${alert.message}`, {
        icon: '/alert-icon.png',
        tag: 'critical-alert'
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* 연결 상태 표시 */}
      <ConnectionStatus isConnected={connectionStatus === 'Open'} />
      
      {/* 실시간 트랜잭션 스트림 */}
      <TransactionStream transactions={transactions} />
      
      {/* 의심거래 알림 */}
      <SuspiciousActivityAlerts alerts={alerts} />
      
      {/* 긴급 차단 기능 */}
      <EmergencyBlockingPanel />
    </div>
  );
}
```

#### **Step 2: 타입 정의**
```typescript
// src/types/audit/index.ts
export interface Transaction {
  id: string;
  timestamp: Date;
  from_address: string;
  to_address: string;
  amount: number;
  currency: string;
  transaction_hash: string;
  partner_id: string;
  status: 'pending' | 'completed' | 'failed' | 'blocked';
  risk_score: number;
  aml_flags: string[];
}

export interface TransactionAlert {
  id: string;
  transaction_id: string;
  type: 'suspicious_pattern' | 'aml_violation' | 'high_amount' | 'velocity_check';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  auto_blocked: boolean;
  requires_manual_review: boolean;
  timestamp: Date;
}

export interface AuditLog {
  id: string;
  timestamp: Date;
  event_type: string;
  entity_type: string;
  entity_id: string;
  user_id?: string;
  partner_id?: string;
  event_data: Record<string, any>;
  ip_address?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}
```

#### **Step 3: API 서비스**
```typescript
// src/services/audit/auditAPI.ts
import { apiClient } from '@/lib/api';
import { AuditLog, TransactionAlert } from '@/types/audit';

export class AuditAPI {
  // 감사 로그 조회
  static async getAuditLogs(params: {
    startDate?: Date;
    endDate?: Date;
    eventType?: string;
    partnerId?: string;
    severity?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await apiClient.get('/audit/logs', { params });
    return response.data;
  }

  // 의심거래 조회
  static async getSuspiciousTransactions(params: {
    startDate?: Date;
    endDate?: Date;
    severity?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await apiClient.get('/audit/transactions/suspicious', { params });
    return response.data;
  }

  // 거래 차단
  static async blockTransaction(transactionId: string, reason: string) {
    const response = await apiClient.post(`/audit/transactions/${transactionId}/block`, {
      reason,
      blocked_by: 'super_admin', // 현재 사용자 정보
      timestamp: new Date().toISOString()
    });
    return response.data;
  }

  // 컴플라이언스 보고서 생성
  static async generateComplianceReport(params: {
    type: 'sar' | 'ctr' | 'daily' | 'weekly' | 'monthly';
    startDate: Date;
    endDate: Date;
    partnerId?: string;
  }) {
    const response = await apiClient.post('/audit/reports/generate', params);
    return response.data;
  }
}
```

#### **Step 4: 커스텀 훅**
```typescript
// src/hooks/audit/useTransactionMonitor.ts
import { useState, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AuditAPI } from '@/services/audit/auditAPI';
import { Transaction, TransactionAlert } from '@/types/audit';

export function useTransactionMonitor(partnerId?: string) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [alerts, setAlerts] = useState<TransactionAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // WebSocket 연결
  const { lastMessage, connectionStatus } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL}/audit`
  );

  // 초기 데이터 로드
  useEffect(() => {
    loadInitialData();
  }, [partnerId]);

  // 실시간 업데이트
  useEffect(() => {
    if (lastMessage) {
      handleRealtimeUpdate(JSON.parse(lastMessage.data));
    }
  }, [lastMessage]);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [transactionData, alertData] = await Promise.all([
        AuditAPI.getSuspiciousTransactions({ partnerId, limit: 50 }),
        AuditAPI.getSuspiciousTransactions({ partnerId, limit: 20 })
      ]);
      
      setTransactions(transactionData.transactions);
      setAlerts(alertData.alerts);
    } catch (error) {
      console.error('Failed to load audit data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRealtimeUpdate = (data: any) => {
    switch (data.type) {
      case 'new_transaction':
        setTransactions(prev => [data.payload, ...prev.slice(0, 49)]);
        break;
      case 'suspicious_activity':
        setAlerts(prev => [data.payload, ...prev.slice(0, 19)]);
        break;
      case 'transaction_blocked':
        setTransactions(prev => 
          prev.map(tx => 
            tx.id === data.payload.transaction_id 
              ? { ...tx, status: 'blocked' }
              : tx
          )
        );
        break;
    }
  };

  const blockTransaction = async (transactionId: string, reason: string) => {
    try {
      await AuditAPI.blockTransaction(transactionId, reason);
      // UI 즉시 업데이트
      setTransactions(prev =>
        prev.map(tx =>
          tx.id === transactionId ? { ...tx, status: 'blocked' } : tx
        )
      );
      return { success: true };
    } catch (error) {
      console.error('Failed to block transaction:', error);
      return { success: false, error };
    }
  };

  return {
    transactions,
    alerts,
    isLoading,
    isConnected: connectionStatus === 'Open',
    blockTransaction,
    refreshData: loadInitialData
  };
}
```

### **1.2 감사 로그 검색 시스템 (2일)**

#### **고급 필터링 컴포넌트**
```typescript
// src/app/audit-compliance/components/AuditLogSearch.tsx
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AuditAPI } from '@/services/audit/auditAPI';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import { MultiSelect } from '@/components/ui/MultiSelect';

interface AuditLogSearchProps {
  onResultsChange?: (results: any[]) => void;
}

export function AuditLogSearch({ onResultsChange }: AuditLogSearchProps) {
  const [filters, setFilters] = useState({
    startDate: null,
    endDate: null,
    eventTypes: [],
    partnerIds: [],
    severity: [],
    searchKeyword: ''
  });

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;

  // 감사 로그 조회
  const { data, isLoading, error } = useQuery({
    queryKey: ['auditLogs', filters, currentPage],
    queryFn: () => AuditAPI.getAuditLogs({
      ...filters,
      page: currentPage,
      limit: pageSize
    }),
    enabled: Boolean(filters.startDate && filters.endDate)
  });

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // 필터 변경 시 첫 페이지로
  };

  const exportResults = async () => {
    try {
      const allResults = await AuditAPI.getAuditLogs({
        ...filters,
        page: 1,
        limit: 10000 // 전체 데이터
      });
      
      // CSV 다운로드 로직
      downloadCSV(allResults.logs, 'audit_logs.csv');
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* 필터 패널 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">검색 필터</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* 날짜 범위 */}
          <DateRangePicker
            startDate={filters.startDate}
            endDate={filters.endDate}
            onChange={(start, end) => {
              handleFilterChange('startDate', start);
              handleFilterChange('endDate', end);
            }}
          />
          
          {/* 이벤트 타입 */}
          <MultiSelect
            label="이벤트 타입"
            options={eventTypeOptions}
            value={filters.eventTypes}
            onChange={(value) => handleFilterChange('eventTypes', value)}
          />
          
          {/* 심각도 */}
          <MultiSelect
            label="심각도"
            options={severityOptions}
            value={filters.severity}
            onChange={(value) => handleFilterChange('severity', value)}
          />
          
          {/* 키워드 검색 */}
          <input
            type="text"
            placeholder="키워드 검색..."
            value={filters.searchKeyword}
            onChange={(e) => handleFilterChange('searchKeyword', e.target.value)}
            className="px-3 py-2 border rounded-md"
          />
        </div>
        
        <div className="flex justify-between mt-4">
          <button
            onClick={() => setFilters(initialFilters)}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            필터 초기화
          </button>
          
          <button
            onClick={exportResults}
            disabled={!data?.logs?.length}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            결과 내보내기
          </button>
        </div>
      </div>
      
      {/* 결과 테이블 */}
      <AuditLogTable
        logs={data?.logs || []}
        isLoading={isLoading}
        totalCount={data?.total || 0}
        currentPage={currentPage}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
      />
    </div>
  );
}

const eventTypeOptions = [
  { value: 'transaction_created', label: '거래 생성' },
  { value: 'transaction_completed', label: '거래 완료' },
  { value: 'wallet_created', label: '지갑 생성' },
  { value: 'withdrawal_requested', label: '출금 요청' },
  { value: 'suspicious_activity', label: '의심 활동' },
  { value: 'compliance_check', label: '컴플라이언스 검사' }
];

const severityOptions = [
  { value: 'info', label: '정보' },
  { value: 'warning', label: '경고' },
  { value: 'error', label: '오류' },
  { value: 'critical', label: '심각' }
];
```

---

## 🎯 **Phase 2: 외부 에너지 공급자 연동**

### **2.1 외부 공급자 모니터링**
```typescript
// src/app/energy/external-market/components/ExternalSupplierMonitor.tsx
'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ExternalEnergyAPI } from '@/services/energy/externalEnergyAPI';

export function ExternalSupplierMonitor() {
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);

  // 공급자 목록 및 상태
  const { data: suppliers, isLoading } = useQuery({
    queryKey: ['externalSuppliers'],
    queryFn: ExternalEnergyAPI.getSuppliers,
    refetchInterval: 30000 // 30초마다 업데이트
  });

  // 실시간 가격 정보
  const { data: prices } = useQuery({
    queryKey: ['energyPrices'],
    queryFn: ExternalEnergyAPI.getCurrentPrices,
    refetchInterval: 10000 // 10초마다 업데이트
  });

  return (
    <div className="space-y-6">
      {/* 공급자 상태 개요 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {suppliers?.map(supplier => (
          <SupplierStatusCard
            key={supplier.id}
            supplier={supplier}
            currentPrice={prices?.[supplier.id]}
            onClick={() => setSelectedSupplier(supplier.id)}
          />
        ))}
      </div>
      
      {/* 가격 비교 차트 */}
      <PriceComparisonChart suppliers={suppliers} prices={prices} />
      
      {/* 상세 모니터링 */}
      {selectedSupplier && (
        <SupplierDetailMonitor supplierId={selectedSupplier} />
      )}
    </div>
  );
}
```

### **2.2 자동 구매 규칙 설정**
```typescript
// src/app/energy/external-market/components/AutoPurchaseRules.tsx
export function AutoPurchaseRules() {
  const [rules, setRules] = useState<AutoPurchaseRule[]>([]);
  const [isEditing, setIsEditing] = useState(false);

  const handleRuleUpdate = async (ruleId: string, updates: Partial<AutoPurchaseRule>) => {
    try {
      await ExternalEnergyAPI.updateAutoPurchaseRule(ruleId, updates);
      // 로컬 상태 업데이트
      setRules(prev => prev.map(rule => 
        rule.id === ruleId ? { ...rule, ...updates } : rule
      ));
    } catch (error) {
      console.error('Failed to update rule:', error);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">자동 구매 규칙</h3>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md"
        >
          {isEditing ? '저장' : '편집'}
        </button>
      </div>
      
      <div className="space-y-4">
        {rules.map(rule => (
          <AutoPurchaseRuleCard
            key={rule.id}
            rule={rule}
            isEditing={isEditing}
            onUpdate={(updates) => handleRuleUpdate(rule.id, updates)}
          />
        ))}
      </div>
      
      {isEditing && (
        <button
          onClick={() => setRules(prev => [...prev, createNewRule()])}
          className="mt-4 px-4 py-2 border-2 border-dashed border-gray-300 rounded-md w-full"
        >
          + 새 규칙 추가
        </button>
      )}
    </div>
  );
}
```

---

## 📊 **개발 체크리스트**

### **Phase 1 체크리스트**
- [ ] 실시간 트랜잭션 모니터링 컴포넌트
- [ ] WebSocket 연결 및 데이터 스트림
- [ ] 의심거래 자동 탐지 알림
- [ ] 긴급 차단 기능
- [ ] 감사 로그 검색 인터페이스
- [ ] 고급 필터링 시스템
- [ ] 데이터 내보내기 기능
- [ ] 컴플라이언스 보고서 생성

### **Phase 2 체크리스트**
- [ ] 외부 공급자 API 연동
- [ ] 실시간 가격 모니터링
- [ ] 가격 비교 대시보드
- [ ] 자동 구매 규칙 설정
- [ ] 구매 이력 추적
- [ ] 수익성 분석

### **테스트 체크리스트**
- [ ] 컴포넌트 단위 테스트
- [ ] API 연동 테스트
- [ ] WebSocket 연결 테스트
- [ ] 에러 처리 테스트
- [ ] 성능 테스트
- [ ] 사용자 시나리오 테스트

---

**📝 이 문서는 실제 개발 진행에 따라 지속적으로 업데이트됩니다.**
