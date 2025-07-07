# Copilot 문서 #27: 에너지 관련 프론트엔드 구현

## 목표
TRON 에너지 풀 관리, 에너지 부족 대응, 동적 수수료 표시 등 에너지 관련 기능을 프론트엔드에서 효과적으로 구현합니다.

## 상세 지시사항

### 1. 프로젝트 구조 및 타입 정의

#### 1.1 에너지 관련 타입 정의
```typescript
// src/types/energy.ts
export interface EnergyPoolStatus {
  poolId: number;
  status: 'active' | 'low' | 'critical' | 'depleted' | 'maintenance';
  totalEnergy: number;
  availableEnergy: number;
  usedEnergy: number;
  usagePercentage: number;
  frozenTrx: number;
  autoRefill: boolean;
  lastChecked: string;
}

export interface EnergyUsageStats {
  period: {
    start: string;
    end: string;
  };
  dailyUsage: Array<{
    date: string;
    totalEnergy: number;
    totalCost: number;
    transactionCount: number;
  }>;
  byType: Array<{
    type: string;
    totalEnergy: number;
    count: number;
  }>;
  hourlyPattern: Array<{
    hour: number;
    avgEnergy: number;
  }>;
  summary: {
    totalEnergyConsumed: number;
    totalCost: number;
    totalTransactions: number;
    avgEnergyPerTransaction: number;
  };
}

export interface WithdrawalOption {
  method: 'standard' | 'trx_payment' | 'queue_wait' | 'external_pool';
  description: string;
  cost?: number;
  costUsd?: number;
  immediate: boolean;
  estimatedWaitMinutes?: number;
}

export interface FeeEstimate {
  withdrawalAmount: number;
  feeAmount: number;
  feePercentage: number;
  netAmount: number;
  breakdown: {
    baseFee: number;
    adjustments: Array<{
      type: string;
      adjustment: number;
      reason: string;
    }>;
    finalFee: number;
  };
  energyInfo: {
    included: boolean;
    message: string;
  };
}
```

### 2. API 서비스 레이어

#### 2.1 에너지 API 서비스
```typescript
// src/services/energyService.ts
import { apiClient } from '@/lib/apiClient';
import type { 
  EnergyPoolStatus, 
  EnergyUsageStats, 
  WithdrawalOption,
  FeeEstimate 
} from '@/types/energy';

export const energyService = {
  // 에너지 풀 상태 조회
  async getPoolStatus(poolId: number = 1): Promise<EnergyPoolStatus> {
    const response = await apiClient.get(`/admin/energy/status?pool_id=${poolId}`);
    return response.data;
  },

  // 에너지 사용 통계
  async getUsageStats(
    poolId: number,
    startDate?: string,
    endDate?: string
  ): Promise<EnergyUsageStats> {
    const params = new URLSearchParams({ pool_id: poolId.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await apiClient.get(`/admin/energy/usage-stats?${params}`);
    return response.data;
  },

  // 출금 옵션 확인
  async checkWithdrawalOptions(withdrawalId: number): Promise<{
    canProcessImmediately: boolean;
    reason: string;
    options: WithdrawalOption[];
  }> {
    const response = await apiClient.post(
      `/withdrawals/${withdrawalId}/check-options`
    );
    return response.data;
  },

  // 수수료 견적
  async estimateFee(amount: number): Promise<FeeEstimate> {
    const response = await apiClient.get(`/fees/estimate?amount=${amount}`);
    return response.data;
  },

  // 선택한 옵션으로 출금 처리
  async processWithOption(
    withdrawalId: number,
    option: string,
    additionalParams?: Record<string, any>
  ) {
    const response = await apiClient.post(
      `/withdrawals/${withdrawalId}/process-with-option`,
      {
        method: option,
        ...additionalParams
      }
    );
    return response.data;
  }
};
```

### 3. 관리자 에너지 대시보드

#### 3.1 에너지 풀 모니터링 컴포넌트
```typescript
// src/components/admin/energy/EnergyPoolDashboard.tsx
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { energyService } from '@/services/energyService';
import { 
  Battery, 
  AlertTriangle, 
  TrendingUp, 
  DollarSign,
  Zap 
} from 'lucide-react';
import { Line, Doughnut } from 'react-chartjs-2';

const EnergyPoolDashboard: React.FC = () => {
  const { data: poolStatus, isLoading } = useQuery({
    queryKey: ['energy-pool-status'],
    queryFn: () => energyService.getPoolStatus(),
    refetchInterval: 30000, // 30초마다 업데이트
  });

  const { data: usageStats } = useQuery({
    queryKey: ['energy-usage-stats'],
    queryFn: () => energyService.getUsageStats(1),
    refetchInterval: 60000, // 1분마다 업데이트
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600';
      case 'low': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      case 'depleted': return 'text-gray-600';
      default: return 'text-blue-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'critical':
      case 'depleted':
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <Battery className="h-5 w-5" />;
    }
  };

  if (isLoading) {
    return <div className="animate-pulse">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* 에너지 풀 상태 헤더 */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              에너지 풀 현황
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              마지막 업데이트: {new Date(poolStatus?.lastChecked || '').toLocaleString()}
            </p>
          </div>
          <div className={`flex items-center space-x-2 ${getStatusColor(poolStatus?.status || '')}`}>
            {getStatusIcon(poolStatus?.status || '')}
            <span className="text-lg font-semibold uppercase">
              {poolStatus?.status}
            </span>
          </div>
        </div>

        {/* 긴급 알림 */}
        {poolStatus?.status === 'critical' && (
          <div className="mt-4 bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            <strong className="font-bold">긴급!</strong>
            <span className="block sm:inline">
              에너지가 임계 수준에 도달했습니다. 즉시 조치가 필요합니다.
            </span>
            <div className="mt-2 space-x-2">
              <button className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
                TRX 동결하기
              </button>
              <button className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700">
                외부 에너지 구매
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="가용 에너지"
          value={poolStatus?.availableEnergy.toLocaleString() || '0'}
          subtitle={`${(100 - (poolStatus?.usagePercentage || 0)).toFixed(1)}% 남음`}
          icon={<Zap className="h-8 w-8 text-yellow-500" />}
          trend={poolStatus?.usagePercentage < 50 ? 'up' : 'down'}
        />
        <StatCard
          title="동결된 TRX"
          value={poolStatus?.frozenTrx.toLocaleString() || '0'}
          subtitle="TRX"
          icon={<DollarSign className="h-8 w-8 text-blue-500" />}
        />
        <StatCard
          title="일일 소비량"
          value={usageStats?.summary.avgEnergyPerTransaction.toLocaleString() || '0'}
          subtitle="평균/거래"
          icon={<TrendingUp className="h-8 w-8 text-green-500" />}
        />
        <StatCard
          title="예상 소진 시간"
          value={calculateDepletionTime(poolStatus)}
          subtitle="남은 시간"
          icon={<Battery className="h-8 w-8 text-red-500" />}
          urgent={poolStatus?.usagePercentage > 80}
        />
      </div>

      {/* 에너지 사용량 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">일별 에너지 사용량</h3>
          <EnergyUsageChart data={usageStats?.dailyUsage || []} />
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">거래 유형별 사용량</h3>
          <EnergyByTypeChart data={usageStats?.byType || []} />
        </div>
      </div>

      {/* 빠른 액션 패널 */}
      <QuickActionsPanel poolStatus={poolStatus} />
    </div>
  );
};

// 통계 카드 컴포넌트
const StatCard: React.FC<{
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down';
  urgent?: boolean;
}> = ({ title, value, subtitle, icon, trend, urgent }) => {
  return (
    <div className={`bg-white shadow rounded-lg p-6 ${urgent ? 'border-2 border-red-500' : ''}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{subtitle}</p>
        </div>
        <div className="flex flex-col items-center">
          {icon}
          {trend && (
            <span className={`text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
              {trend === 'up' ? '↑' : '↓'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// 빠른 액션 패널
const QuickActionsPanel: React.FC<{ poolStatus: EnergyPoolStatus | undefined }> = ({ poolStatus }) => {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">빠른 작업</h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <button className="bg-blue-600 text-white px-4 py-3 rounded hover:bg-blue-700">
          <Zap className="h-5 w-5 inline mr-2" />
          TRX 추가 동결
        </button>
        <button className="bg-green-600 text-white px-4 py-3 rounded hover:bg-green-700">
          에너지 가격 확인
        </button>
        <button className="bg-orange-600 text-white px-4 py-3 rounded hover:bg-orange-700">
          자동 관리 설정
        </button>
        <button className="bg-purple-600 text-white px-4 py-3 rounded hover:bg-purple-700">
          상세 리포트 보기
        </button>
      </div>
    </div>
  );
};

export default EnergyPoolDashboard;
```

### 4. 사용자 출금 인터페이스

#### 4.1 에너지 부족 시 대안 선택 모달
```typescript
// src/components/user/withdrawal/EnergyAlternativeModal.tsx
import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { energyService } from '@/services/energyService';
import { 
  AlertCircle, 
  DollarSign, 
  Clock, 
  ExternalLink 
} from 'lucide-react';
import type { WithdrawalOption } from '@/types/energy';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  withdrawalId: number;
  options: WithdrawalOption[];
  onSuccess: () => void;
}

const EnergyAlternativeModal: React.FC<Props> = ({
  isOpen,
  onClose,
  withdrawalId,
  options,
  onSuccess
}) => {
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);

  const processMutation = useMutation({
    mutationFn: (option: string) => 
      energyService.processWithOption(withdrawalId, option),
    onSuccess: () => {
      onSuccess();
      onClose();
    },
    onError: (error) => {
      console.error('처리 실패:', error);
      setIsProcessing(false);
    }
  });

  const handleProcess = () => {
    if (!selectedOption) return;
    setIsProcessing(true);
    processMutation.mutate(selectedOption);
  };

  const getOptionIcon = (method: string) => {
    switch (method) {
      case 'trx_payment':
        return <DollarSign className="h-6 w-6" />;
      case 'queue_wait':
        return <Clock className="h-6 w-6" />;
      case 'external_pool':
        return <ExternalLink className="h-6 w-6" />;
      default:
        return <AlertCircle className="h-6 w-6" />;
    }
  };

  const getOptionColor = (method: string) => {
    switch (method) {
      case 'trx_payment':
        return 'border-blue-500 bg-blue-50';
      case 'queue_wait':
        return 'border-yellow-500 bg-yellow-50';
      case 'external_pool':
        return 'border-green-500 bg-green-50';
      default:
        return 'border-gray-500 bg-gray-50';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center space-x-3 mb-4">
            <AlertCircle className="h-8 w-8 text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900">
              에너지 부족으로 대체 방법이 필요합니다
            </h3>
          </div>

          <p className="text-gray-600 mb-6">
            현재 TRON 네트워크 에너지가 부족하여 일반적인 방법으로 출금을 처리할 수 없습니다.
            아래 옵션 중 하나를 선택해주세요:
          </p>

          <div className="space-y-4">
            {options.map((option) => (
              <div
                key={option.method}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  selectedOption === option.method
                    ? getOptionColor(option.method)
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedOption(option.method)}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getOptionIcon(option.method)}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">
                      {option.description}
                    </h4>
                    
                    {option.cost !== undefined && (
                      <p className="text-sm text-gray-600 mt-1">
                        추가 비용: {option.cost} TRX 
                        {option.costUsd && ` (≈ $${option.costUsd.toFixed(2)})`}
                      </p>
                    )}
                    
                    {option.estimatedWaitMinutes && (
                      <p className="text-sm text-gray-600 mt-1">
                        예상 대기 시간: 약 {option.estimatedWaitMinutes}분
                      </p>
                    )}
                    
                    <div className="mt-2">
                      {option.immediate ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          즉시 처리
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          대기 필요
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              disabled={isProcessing}
            >
              취소
            </button>
            <button
              onClick={handleProcess}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
              disabled={!selectedOption || isProcessing}
            >
              {isProcessing ? '처리 중...' : '선택한 방법으로 진행'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnergyAlternativeModal;
```

### 5. 수수료 표시 컴포넌트

#### 5.1 동적 수수료 계산기
```typescript
// src/components/user/withdrawal/FeeCalculator.tsx
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { energyService } from '@/services/energyService';
import { Info, TrendingUp, TrendingDown } from 'lucide-react';
import type { FeeEstimate } from '@/types/energy';

interface Props {
  amount: number;
  onFeeCalculated?: (fee: FeeEstimate) => void;
}

const FeeCalculator: React.FC<Props> = ({ amount, onFeeCalculated }) => {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const { data: feeEstimate, isLoading } = useQuery({
    queryKey: ['fee-estimate', amount],
    queryFn: () => energyService.estimateFee(amount),
    enabled: amount > 0,
    staleTime: 30000, // 30초간 캐시
  });

  useEffect(() => {
    if (feeEstimate && onFeeCalculated) {
      onFeeCalculated(feeEstimate);
    }
  }, [feeEstimate, onFeeCalculated]);

  if (!amount || amount <= 0) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-lg p-4">
        <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-300 rounded w-1/2"></div>
      </div>
    );
  }

  if (!feeEstimate) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-gray-900">수수료 계산</h4>
        <button
          onClick={() => setShowBreakdown(!showBreakdown)}
          className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
        >
          <Info className="h-4 w-4 mr-1" />
          {showBreakdown ? '간단히' : '자세히'}
        </button>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-600">출금 금액:</span>
          <span className="font-medium">{amount.toFixed(2)} USDT</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">플랫폼 수수료:</span>
          <span className="font-medium text-red-600">
            -{feeEstimate.feeAmount.toFixed(2)} USDT ({feeEstimate.feePercentage.toFixed(2)}%)
          </span>
        </div>

        {showBreakdown && feeEstimate.breakdown.adjustments.length > 0 && (
          <div className="mt-3 pt-3 border-t border-blue-200">
            <p className="text-sm font-medium text-gray-700 mb-2">수수료 조정 내역:</p>
            {feeEstimate.breakdown.adjustments.map((adj, index) => (
              <div key={index} className="flex justify-between text-sm">
                <span className="text-gray-600">{adj.reason}:</span>
                <span className={adj.adjustment > 0 ? 'text-red-600' : 'text-green-600'}>
                  {adj.adjustment > 0 ? '+' : ''}{adj.adjustment.toFixed(2)} USDT
                  {adj.adjustment > 0 ? (
                    <TrendingUp className="h-3 w-3 inline ml-1" />
                  ) : (
                    <TrendingDown className="h-3 w-3 inline ml-1" />
                  )}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="pt-3 mt-3 border-t border-blue-200">
          <div className="flex justify-between font-semibold">
            <span className="text-gray-900">실제 출금액:</span>
            <span className="text-green-600">{feeEstimate.netAmount.toFixed(2)} USDT</span>
          </div>
        </div>

        {feeEstimate.energyInfo.included && (
          <div className="mt-3 bg-green-100 border border-green-200 rounded p-2">
            <p className="text-sm text-green-800 flex items-center">
              <Info className="h-4 w-4 mr-1" />
              {feeEstimate.energyInfo.message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeeCalculator;
```

### 6. 실시간 에너지 상태 표시

#### 6.1 에너지 상태 인디케이터
```typescript
// src/components/common/EnergyStatusIndicator.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { energyService } from '@/services/energyService';
import { Battery, Zap } from 'lucide-react';

const EnergyStatusIndicator: React.FC = () => {
  const { data: energyStatus } = useQuery({
    queryKey: ['energy-status'],
    queryFn: () => energyService.getPoolStatus(),
    refetchInterval: 60000, // 1분마다 업데이트
  });

  if (!energyStatus) return null;

  const getStatusColor = () => {
    if (energyStatus.usagePercentage < 70) return 'text-green-500';
    if (energyStatus.usagePercentage < 85) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getStatusText = () => {
    if (energyStatus.usagePercentage < 70) return '정상';
    if (energyStatus.usagePercentage < 85) return '주의';
    return '부족';
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`flex items-center ${getStatusColor()}`}>
        <Battery className="h-5 w-5 mr-1" />
        <span className="text-sm font-medium">{getStatusText()}</span>
      </div>
      <div className="text-xs text-gray-500">
        에너지 {(100 - energyStatus.usagePercentage).toFixed(0)}%
      </div>
    </div>
  );
};

export default EnergyStatusIndicator;
```

### 7. WebSocket 실시간 업데이트

#### 7.1 에너지 상태 WebSocket Hook
```typescript
// src/hooks/useEnergyWebSocket.ts
import { useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface EnergyUpdate {
  type: 'energy_update';
  data: {
    serviceAvailable: boolean;
    alternativeRequired: boolean;
    message: string;
  };
}

export const useEnergyWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<EnergyUpdate | null>(null);
  const queryClient = useQueryClient();
  
  const connect = useCallback(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/energy');
    
    ws.onopen = () => {
      console.log('에너지 WebSocket 연결됨');
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      try {
        const update: EnergyUpdate = JSON.parse(event.data);
        setLastUpdate(update);
        
        // React Query 캐시 업데이트
        if (update.type === 'energy_update') {
          queryClient.invalidateQueries({ queryKey: ['energy-status'] });
          
          // 긴급 상황인 경우 알림
          if (update.data.alternativeRequired) {
            showNotification({
              title: '에너지 부족 경고',
              message: update.data.message,
              type: 'warning'
            });
          }
        }
      } catch (error) {
        console.error('WebSocket 메시지 파싱 오류:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      console.log('WebSocket 연결 종료');
      setIsConnected(false);
      
      // 5초 후 재연결 시도
      setTimeout(() => {
        connect();
      }, 5000);
    };
    
    return ws;
  }, [queryClient]);
  
  useEffect(() => {
    const ws = connect();
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [connect]);
  
  return {
    isConnected,
    lastUpdate
  };
};
```

### 8. 파트너사 수수료 관리 UI

#### 8.1 파트너 수수료 설정 패널
```typescript
// src/components/admin/partners/PartnerFeeSettings.tsx
import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { feeService } from '@/services/feeService';
import { Save, Plus, Trash2 } from 'lucide-react';

interface Props {
  partnerId: number;
  currentConfig: any; // 타입 정의 필요
}

const PartnerFeeSettings: React.FC<Props> = ({ partnerId, currentConfig }) => {
  const [feeConfig, setFeeConfig] = useState(currentConfig);
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (data: any) => 
      feeService.updatePartnerFees(partnerId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partner-fees', partnerId] });
      showNotification({
        title: '성공',
        message: '수수료 설정이 업데이트되었습니다',
        type: 'success'
      });
    }
  });

  const handleSave = () => {
    updateMutation.mutate(feeConfig);
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">파트너 수수료 설정</h3>
        <button
          onClick={handleSave}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          disabled={updateMutation.isLoading}
        >
          <Save className="h-4 w-4 mr-2" />
          {updateMutation.isLoading ? '저장 중...' : '저장'}
        </button>
      </div>

      {/* 기본 수수료 설정 */}
      <div className="space-y-4">
        <div>
          <h4 className="font-medium text-gray-900 mb-3">기본 수수료</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                출금 수수료 (%)
              </label>
              <input
                type="number"
                value={feeConfig.withdrawal?.percentage || 0}
                onChange={(e) => setFeeConfig({
                  ...feeConfig,
                  withdrawal: {
                    ...feeConfig.withdrawal,
                    percentage: parseFloat(e.target.value)
                  }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                step="0.01"
                min="0"
                max="100"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">
                최소 수수료 (USDT)
              </label>
              <input
                type="number"
                value={feeConfig.withdrawal?.minFee || 0}
                onChange={(e) => setFeeConfig({
                  ...feeConfig,
                  withdrawal: {
                    ...feeConfig.withdrawal,
                    minFee: parseFloat(e.target.value)
                  }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                step="0.01"
                min="0"
              />
            </div>
          </div>
        </div>

        {/* 등급별 수수료 */}
        <div className="mt-6">
          <h4 className="font-medium text-gray-900 mb-3">등급별 할인</h4>
          <div className="space-y-3">
            {['bronze', 'silver', 'gold'].map((tier) => (
              <div key={tier} className="flex items-center space-x-4">
                <span className="w-20 text-sm font-medium capitalize">
                  {tier}
                </span>
                <input
                  type="number"
                  value={feeConfig.tierDiscounts?.[tier] || 0}
                  onChange={(e) => setFeeConfig({
                    ...feeConfig,
                    tierDiscounts: {
                      ...feeConfig.tierDiscounts,
                      [tier]: parseFloat(e.target.value)
                    }
                  })}
                  className="flex-1 rounded-md border-gray-300 shadow-sm"
                  placeholder="할인율 %"
                  step="1"
                  min="0"
                  max="100"
                />
              </div>
            ))}
          </div>
        </div>

        {/* 수익 분배 */}
        <div className="mt-6">
          <h4 className="font-medium text-gray-900 mb-3">수익 분배</h4>
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">
              파트너 수익률 (%)
            </label>
            <input
              type="number"
              value={feeConfig.revenueShare || 0}
              onChange={(e) => setFeeConfig({
                ...feeConfig,
                revenueShare: parseFloat(e.target.value)
              })}
              className="w-32 rounded-md border-gray-300 shadow-sm"
              step="1"
              min="0"
              max="100"
            />
            <span className="text-sm text-gray-500">
              플랫폼: {100 - (feeConfig.revenueShare || 0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PartnerFeeSettings;
```

### 9. 모바일 반응형 에너지 상태

#### 9.1 모바일 에너지 대시보드
```typescript
// src/components/mobile/MobileEnergyDashboard.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { energyService } from '@/services/energyService';
import { Battery, AlertTriangle } from 'lucide-react';

const MobileEnergyDashboard: React.FC = () => {
  const { data: energyStatus } = useQuery({
    queryKey: ['energy-status-mobile'],
    queryFn: () => energyService.getPoolStatus(),
    refetchInterval: 60000,
  });

  const getBatteryLevel = () => {
    if (!energyStatus) return 0;
    return 100 - energyStatus.usagePercentage;
  };

  const getBatteryColor = () => {
    const level = getBatteryLevel();
    if (level > 30) return 'bg-green-500';
    if (level > 15) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">에너지 상태</h3>
        {energyStatus?.status === 'critical' && (
          <AlertTriangle className="h-5 w-5 text-red-500 animate-pulse" />
        )}
      </div>

      {/* 배터리 시각화 */}
      <div className="relative h-32 bg-gray-200 rounded-lg overflow-hidden">
        <div 
          className={`absolute bottom-0 left-0 right-0 ${getBatteryColor()} transition-all duration-500`}
          style={{ height: `${getBatteryLevel()}%` }}
        >
          <div className="absolute inset-0 bg-white opacity-20 animate-pulse"></div>
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <Battery className="h-12 w-12 text-gray-700 mb-2" />
            <p className="text-2xl font-bold text-gray-900">
              {getBatteryLevel().toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      {/* 상태 정보 */}
      <div className="mt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">가용 에너지</span>
          <span className="font-medium">
            {energyStatus?.availableEnergy.toLocaleString() || '0'}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">서비스 상태</span>
          <span className={`font-medium ${
            energyStatus?.status === 'active' ? 'text-green-600' : 'text-red-600'
          }`}>
            {energyStatus?.status === 'active' ? '정상' : '제한됨'}
          </span>
        </div>
      </div>

      {energyStatus?.status !== 'active' && (
        <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded p-3">
          <p className="text-sm text-yellow-800">
            에너지 부족으로 출금 시 추가 옵션이 필요할 수 있습니다.
          </p>
        </div>
      )}
    </div>
  );
};

export default MobileEnergyDashboard;
```

## 검증 포인트

- [ ] 에너지 풀 상태가 실시간으로 표시되는가?
- [ ] 에너지 부족 시 대안이 제시되는가?
- [ ] 수수료가 동적으로 계산되는가?
- [ ] WebSocket 연결이 안정적인가?
- [ ] 관리자가 에너지를 효과적으로 관리할 수 있는가?
- [ ] 파트너별 수수료 설정이 가능한가?
- [ ] 모바일에서도 잘 작동하는가?
- [ ] 사용자가 수수료를 쉽게 이해할 수 있는가?

이로써 TRON 에너지 관련 모든 기능이 프론트엔드에서 구현되어, 사용자와 관리자 모두 효과적으로 에너지 시스템을 활용할 수 있습니다.