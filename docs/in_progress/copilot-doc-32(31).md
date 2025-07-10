# Copilot 문서 #31: 파트너 관리자 템플릿 (TronLink 통합)

## 목표
TronLink 연동이 통합된 파트너 관리자 대시보드를 구축합니다. TronLink 지갑 연동 UI, 실시간 자산 현황 대시보드, 에너지 풀 모니터링 위젯, 출금 승인 및 배치 실행 UI, 사용자 관리 및 KYC 인터페이스, 수익/비용 분석 대시보드를 포함한 완성형 템플릿을 제공합니다.

## 전제 조건
- Copilot 문서 #24-30이 완료되어 있어야 합니다
- TronLink 연동 시스템이 구현되어 있어야 합니다
- 모든 백엔드 API가 작동 중이어야 합니다
- React/Next.js 환경이 준비되어 있어야 합니다

## 🎯 파트너 관리자 템플릿 구조

### 📊 대시보드 레이아웃
```
파트너 관리자 대시보드
├── 🏠 메인 대시보드
│   ├── 실시간 통계 카드
│   ├── 자산 현황 차트
│   ├── 에너지 풀 상태
│   ├── 최근 거래 목록
│   └── 알림 센터
├── 💼 TronLink 지갑 관리
│   ├── 지갑 연결 상태
│   ├── 다중 지갑 관리
│   ├── 잔액 및 자산 현황
│   └── 트랜잭션 서명 UI
├── ⚡ 에너지 풀 모니터링
│   ├── 실시간 에너지 상태
│   ├── TRX 스테이킹 현황
│   ├── 에너지 사용 통계
│   └── 임계값 알림 설정
├── 💸 출금 관리
│   ├── 출금 요청 대기열
│   ├── 실시간/일괄 출금 설정
│   ├── 배치 생성 및 서명
│   └── 출금 이력 조회
├── 👥 사용자 관리
│   ├── 사용자 목록 및 검색
│   ├── KYC 상태 관리
│   ├── 사용자별 거래 이력
│   └── 계정 동결/해제
├── 📊 분석 및 보고서
│   ├── 수익/비용 분석
│   ├── 거래량 통계
│   ├── 사용자 행동 분석
│   └── 맞춤형 리포트
└── ⚙️ 설정
    ├── 파트너 정보
    ├── API 키 관리
    ├── 브랜딩 설정
    └── 알림 설정
```

## 🛠️ 구현 단계

### Phase 1: 프로젝트 기본 구조 (1일)

#### 1.1 Next.js 프로젝트 생성
```bash
# 파트너 관리자 템플릿 생성
npx create-next-app@latest partner-admin-template --typescript --tailwind --app
cd partner-admin-template

# 필요한 패키지 설치
npm install @reduxjs/toolkit react-redux
npm install @tanstack/react-query
npm install @headlessui/react @heroicons/react
npm install recharts date-fns
npm install react-hook-form @hookform/resolvers zod
npm install @tronweb3/tronwallet-adapter-react-hooks
npm install @tronweb3/tronwallet-adapter-tronlink
npm install tronweb
npm install axios
npm install react-hot-toast
npm install framer-motion
```

#### 1.2 프로젝트 구조 설정
```typescript
// src/lib/project-structure.ts
export const projectStructure = `
src/
├── app/                      # Next.js 13+ App Router
│   ├── (auth)/              # 인증 관련 라우트
│   │   ├── login/
│   │   └── layout.tsx
│   ├── (dashboard)/         # 대시보드 라우트
│   │   ├── page.tsx         # 메인 대시보드
│   │   ├── wallet/          # 지갑 관리
│   │   ├── energy/          # 에너지 풀
│   │   ├── withdrawals/     # 출금 관리
│   │   ├── users/           # 사용자 관리
│   │   ├── analytics/       # 분석
│   │   ├── settings/        # 설정
│   │   └── layout.tsx
│   └── api/                 # API 라우트
├── components/
│   ├── common/              # 공통 컴포넌트
│   │   ├── Button/
│   │   ├── Card/
│   │   ├── Modal/
│   │   └── Table/
│   ├── dashboard/           # 대시보드 컴포넌트
│   │   ├── StatsCard/
│   │   ├── AssetChart/
│   │   └── RecentTransactions/
│   ├── wallet/              # 지갑 컴포넌트
│   │   ├── TronLinkConnect/
│   │   ├── WalletStatus/
│   │   └── TransactionSigner/
│   ├── energy/              # 에너지 컴포넌트
│   │   ├── EnergyGauge/
│   │   ├── StakingInfo/
│   │   └── UsageChart/
│   └── layout/              # 레이아웃 컴포넌트
│       ├── Sidebar/
│       ├── Header/
│       └── Footer/
├── hooks/                   # 커스텀 훅
│   ├── useTronLink.ts
│   ├── useEnergyPool.ts
│   └── useWithdrawals.ts
├── lib/                     # 유틸리티
│   ├── api/                 # API 클라이언트
│   ├── tron/                # Tron 관련
│   └── utils/               # 일반 유틸리티
├── store/                   # Redux 스토어
│   ├── slices/
│   └── store.ts
└── types/                   # TypeScript 타입
    ├── api.ts
    ├── wallet.ts
    └── user.ts
`;
```

### Phase 2: TronLink 지갑 연동 구현 (2일)

#### 2.1 TronLink 연동 Provider
```typescript
// src/providers/TronLinkProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { 
  WalletProvider,
  useWallet,
  WalletError
} from '@tronweb3/tronwallet-adapter-react-hooks';
import { 
  TronLinkAdapter,
  WalletReadyState 
} from '@tronweb3/tronwallet-adapter-tronlink';
import { toast } from 'react-hot-toast';

interface TronLinkContextType {
  connected: boolean;
  connecting: boolean;
  address: string | null;
  balance: number;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  signTransaction: (transaction: any) => Promise<any>;
}

const TronLinkContext = createContext<TronLinkContextType | null>(null);

export const TronLinkProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [adapter] = useState(() => new TronLinkAdapter());
  
  return (
    <WalletProvider 
      adapters={[adapter]}
      onError={(error: WalletError) => {
        console.error('Wallet error:', error);
        toast.error(error.message || '지갑 연결 오류가 발생했습니다');
      }}
    >
      <TronLinkContextInner>
        {children}
      </TronLinkContextInner>
    </WalletProvider>
  );
};

const TronLinkContextInner: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const { 
    wallet, 
    address, 
    connected, 
    connecting, 
    connect, 
    disconnect,
    signTransaction 
  } = useWallet();
  
  const [balance, setBalance] = useState(0);
  
  // 잔액 조회
  useEffect(() => {
    if (connected && address) {
      fetchBalance();
    }
  }, [connected, address]);
  
  const fetchBalance = async () => {
    try {
      const response = await fetch(`/api/wallet/balance?address=${address}`);
      const data = await response.json();
      setBalance(data.balance);
    } catch (error) {
      console.error('잔액 조회 실패:', error);
    }
  };
  
  const contextValue: TronLinkContextType = {
    connected,
    connecting,
    address,
    balance,
    connect: async () => {
      try {
        await connect();
        toast.success('TronLink 연결 성공');
      } catch (error) {
        toast.error('TronLink 연결 실패');
        throw error;
      }
    },
    disconnect: async () => {
      await disconnect();
      toast.success('TronLink 연결 해제');
    },
    signTransaction
  };
  
  return (
    <TronLinkContext.Provider value={contextValue}>
      {children}
    </TronLinkContext.Provider>
  );
};

export const useTronLink = () => {
  const context = useContext(TronLinkContext);
  if (!context) {
    throw new Error('useTronLink must be used within TronLinkProvider');
  }
  return context;
};
```

#### 2.2 지갑 연결 컴포넌트
```typescript
// src/components/wallet/TronLinkConnect.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { WalletIcon, LinkIcon, PowerIcon } from '@heroicons/react/24/outline';
import { useTronLink } from '@/providers/TronLinkProvider';
import { Button } from '@/components/common/Button';
import { formatAddress, formatBalance } from '@/lib/utils/format';

export const TronLinkConnect: React.FC = () => {
  const { connected, connecting, address, balance, connect, disconnect } = useTronLink();
  
  if (connected && address) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-md p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            TronLink 지갑
          </h3>
          <span className="flex items-center text-sm text-green-600">
            <span className="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
            연결됨
          </span>
        </div>
        
        <div className="space-y-3">
          <div>
            <p className="text-sm text-gray-500">주소</p>
            <p className="font-mono text-sm">{formatAddress(address)}</p>
          </div>
          
          <div>
            <p className="text-sm text-gray-500">잔액</p>
            <p className="text-2xl font-bold">{formatBalance(balance)} TRX</p>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={disconnect}
            className="w-full"
          >
            <PowerIcon className="w-4 h-4 mr-2" />
            연결 해제
          </Button>
        </div>
      </motion.div>
    );
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md p-6"
    >
      <div className="text-center">
        <WalletIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          TronLink 연결
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          TronLink 지갑을 연결하여 출금 관리를 시작하세요
        </p>
        
        <Button
          onClick={connect}
          loading={connecting}
          className="w-full"
        >
          <LinkIcon className="w-4 h-4 mr-2" />
          TronLink 연결
        </Button>
        
        <p className="text-xs text-gray-400 mt-4">
          TronLink 브라우저 확장 프로그램이 필요합니다
        </p>
      </div>
    </motion.div>
  );
};
```

### Phase 3: 메인 대시보드 구현 (2일)

#### 3.1 대시보드 페이지
```typescript
// src/app/(dashboard)/page.tsx
import React from 'react';
import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { AssetChart } from '@/components/dashboard/AssetChart';
import { EnergyStatus } from '@/components/energy/EnergyStatus';
import { RecentTransactions } from '@/components/dashboard/RecentTransactions';
import { WithdrawalQueue } from '@/components/withdrawals/WithdrawalQueue';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-500">실시간 운영 현황을 확인하세요</p>
      </div>
      
      <StatsGrid />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AssetChart />
        </div>
        <div>
          <EnergyStatus />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentTransactions />
        <WithdrawalQueue />
      </div>
    </div>
  );
}
```

#### 3.2 통계 카드 컴포넌트
```typescript
// src/components/dashboard/StatsGrid.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  CurrencyDollarIcon,
  UsersIcon,
  ArrowTrendingUpIcon,
  BoltIcon 
} from '@heroicons/react/24/outline';
import { StatsCard } from './StatsCard';
import { api } from '@/lib/api';

export const StatsGrid: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: api.dashboard.getStats,
    refetchInterval: 30000 // 30초마다 갱신
  });
  
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-gray-200 rounded-lg h-32"></div>
          </div>
        ))}
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard
        title="총 자산"
        value={`$${stats?.totalAssets.toLocaleString()}`}
        change={stats?.assetChange}
        icon={CurrencyDollarIcon}
        color="blue"
      />
      
      <StatsCard
        title="활성 사용자"
        value={stats?.activeUsers.toLocaleString()}
        change={stats?.userChange}
        icon={UsersIcon}
        color="green"
      />
      
      <StatsCard
        title="일일 거래량"
        value={`$${stats?.dailyVolume.toLocaleString()}`}
        change={stats?.volumeChange}
        icon={ArrowTrendingUpIcon}
        color="purple"
      />
      
      <StatsCard
        title="에너지 상태"
        value={`${stats?.energyPercentage}%`}
        subtitle={`${stats?.availableEnergy.toLocaleString()} / ${stats?.totalEnergy.toLocaleString()}`}
        icon={BoltIcon}
        color="yellow"
        showProgress
        progress={stats?.energyPercentage}
      />
    </div>
  );
};
```

### Phase 4: 에너지 풀 모니터링 구현 (1일)

#### 4.1 에너지 상태 컴포넌트
```typescript
// src/components/energy/EnergyStatus.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { BoltIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { EnergyGauge } from './EnergyGauge';
import { Button } from '@/components/common/Button';

export const EnergyStatus: React.FC = () => {
  const { data: energy, isLoading } = useQuery({
    queryKey: ['energy-status'],
    queryFn: api.energy.getStatus,
    refetchInterval: 10000 // 10초마다 갱신
  });
  
  const isLow = energy && energy.percentage < 20;
  const isCritical = energy && energy.percentage < 10;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`bg-white rounded-lg shadow-md p-6 ${
        isCritical ? 'ring-2 ring-red-500' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          에너지 풀 상태
        </h3>
        {isLow && (
          <ExclamationTriangleIcon className={`w-5 h-5 ${
            isCritical ? 'text-red-500' : 'text-yellow-500'
          }`} />
        )}
      </div>
      
      <div className="mb-6">
        <EnergyGauge
          percentage={energy?.percentage || 0}
          loading={isLoading}
        />
      </div>
      
      <div className="space-y-3 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">사용 가능</span>
          <span className="font-medium">
            {energy?.available.toLocaleString()} Energy
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">총 에너지</span>
          <span className="font-medium">
            {energy?.total.toLocaleString()} Energy
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">동결된 TRX</span>
          <span className="font-medium">
            {energy?.frozenTrx.toLocaleString()} TRX
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">일일 소비량</span>
          <span className="font-medium">
            {energy?.dailyConsumption.toLocaleString()} Energy
          </span>
        </div>
      </div>
      
      {isLow && (
        <div className={`p-3 rounded-lg mb-4 ${
          isCritical ? 'bg-red-50' : 'bg-yellow-50'
        }`}>
          <p className={`text-sm ${
            isCritical ? 'text-red-700' : 'text-yellow-700'
          }`}>
            {isCritical 
              ? '⚠️ 에너지가 매우 부족합니다. 즉시 TRX를 스테이킹하세요.'
              : '⚡ 에너지가 부족합니다. TRX 스테이킹을 고려하세요.'}
          </p>
        </div>
      )}
      
      <Button
        variant={isCritical ? 'danger' : 'primary'}
        size="sm"
        className="w-full"
        onClick={() => window.open('/energy/manage', '_self')}
      >
        <BoltIcon className="w-4 h-4 mr-2" />
        에너지 관리
      </Button>
    </motion.div>
  );
};
```

#### 4.2 에너지 게이지 컴포넌트
```typescript
// src/components/energy/EnergyGauge.tsx
import React from 'react';
import { motion } from 'framer-motion';

interface EnergyGaugeProps {
  percentage: number;
  loading?: boolean;
}

export const EnergyGauge: React.FC<EnergyGaugeProps> = ({ 
  percentage, 
  loading 
}) => {
  const getColor = () => {
    if (percentage >= 50) return 'text-green-500';
    if (percentage >= 20) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  return (
    <div className="relative w-48 h-48 mx-auto">
      <svg className="transform -rotate-90 w-48 h-48">
        <circle
          cx="96"
          cy="96"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="none"
          className="text-gray-200"
        />
        <motion.circle
          cx="96"
          cy="96"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="none"
          strokeLinecap="round"
          className={getColor()}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          {loading ? (
            <div className="animate-pulse">
              <div className="h-12 w-20 bg-gray-200 rounded mb-2"></div>
            </div>
          ) : (
            <>
              <p className={`text-4xl font-bold ${getColor()}`}>
                {percentage}%
              </p>
              <p className="text-sm text-gray-500">에너지</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
```

### Phase 5: 출금 관리 UI 구현 (2일)

#### 5.1 출금 대기열 컴포넌트
```typescript
// src/components/withdrawals/WithdrawalQueue.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  DocumentDuplicateIcon 
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { useTronLink } from '@/providers/TronLinkProvider';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { formatAddress, formatAmount } from '@/lib/utils/format';
import { toast } from 'react-hot-toast';

interface Withdrawal {
  id: string;
  userId: string;
  amount: number;
  toAddress: string;
  status: 'pending' | 'approved' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  autoApproved: boolean;
}

export const WithdrawalQueue: React.FC = () => {
  const queryClient = useQueryClient();
  const { connected, signTransaction } = useTronLink();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  const { data: withdrawals, isLoading } = useQuery({
    queryKey: ['withdrawal-queue'],
    queryFn: api.withdrawals.getPending,
    refetchInterval: 5000
  });
  
  const approveMutation = useMutation({
    mutationFn: api.withdrawals.approve,
    onSuccess: () => {
      queryClient.invalidateQueries(['withdrawal-queue']);
      toast.success('출금 승인 완료');
    }
  });
  
  const createBatchMutation = useMutation({
    mutationFn: api.withdrawals.createBatch,
    onSuccess: async (batch) => {
      // TronLink로 배치 서명
      if (connected) {
        try {
          const signature = await signTransaction(batch.transactionData);
          await api.withdrawals.submitBatchSignature(batch.id, signature);
          toast.success('배치 생성 및 서명 완료');
        } catch (error) {
          toast.error('배치 서명 실패');
        }
      }
      queryClient.invalidateQueries(['withdrawal-queue']);
      setSelectedIds([]);
    }
  });
  
  const handleSelectAll = () => {
    if (selectedIds.length === withdrawals?.pending.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(withdrawals?.pending.map(w => w.id) || []);
    }
  };
  
  const handleCreateBatch = () => {
    if (selectedIds.length === 0) {
      toast.error('출금 요청을 선택하세요');
      return;
    }
    
    createBatchMutation.mutate({ withdrawalIds: selectedIds });
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          출금 대기열
        </h3>
        <div className="flex items-center space-x-2">
          <Badge variant="info">
            {withdrawals?.pending.length || 0} 대기중
          </Badge>
          {withdrawals?.settings.policyType === 'batch' && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleCreateBatch}
              disabled={selectedIds.length === 0}
            >
              <DocumentDuplicateIcon className="w-4 h-4 mr-2" />
              배치 생성 ({selectedIds.length})
            </Button>
          )}
        </div>
      </div>
      
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {withdrawals?.settings.policyType === 'batch' && (
            <div className="flex items-center p-2 bg-gray-50 rounded">
              <input
                type="checkbox"
                checked={selectedIds.length === withdrawals?.pending.length}
                onChange={handleSelectAll}
                className="mr-3"
              />
              <span className="text-sm text-gray-600">전체 선택</span>
            </div>
          )}
          
          <AnimatePresence>
            {withdrawals?.pending.map((withdrawal) => (
              <motion.div
                key={withdrawal.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="border rounded-lg p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {withdrawals?.settings.policyType === 'batch' && (
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(withdrawal.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedIds([...selectedIds, withdrawal.id]);
                          } else {
                            setSelectedIds(selectedIds.filter(id => id !== withdrawal.id));
                          }
                        }}
                      />
                    )}
                    
                    <div>
                      <p className="font-medium">
                        {formatAmount(withdrawal.amount)} USDT
                      </p>
                      <p className="text-sm text-gray-500">
                        → {formatAddress(withdrawal.toAddress)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {withdrawal.autoApproved && (
                      <Badge variant="success" size="sm">
                        자동승인
                      </Badge>
                    )}
                    
                    {withdrawals?.settings.policyType === 'realtime' && (
                      <div className="flex space-x-1">
                        <Button
                          size="xs"
                          variant="success"
                          onClick={() => approveMutation.mutate(withdrawal.id)}
                        >
                          <CheckCircleIcon className="w-4 h-4" />
                        </Button>
                        <Button
                          size="xs"
                          variant="danger"
                          onClick={() => {/* 거부 처리 */}}
                        >
                          <XCircleIcon className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="mt-2 flex items-center text-xs text-gray-500">
                  <ClockIcon className="w-3 h-3 mr-1" />
                  {new Date(withdrawal.createdAt).toLocaleString()}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {withdrawals?.pending.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <ClockIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>대기 중인 출금 요청이 없습니다</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### Phase 6: 사용자 관리 및 분석 (1일)

#### 6.1 사용자 관리 테이블
```typescript
// src/components/users/UserTable.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  CheckBadgeIcon,
  XCircleIcon 
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import { Table } from '@/components/common/Table';
import { Input } from '@/components/common/Input';
import { Select } from '@/components/common/Select';
import { Badge } from '@/components/common/Badge';
import { formatDate } from '@/lib/utils/format';

export const UserTable: React.FC = () => {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState({
    kycStatus: 'all',
    status: 'all'
  });
  
  const { data, isLoading } = useQuery({
    queryKey: ['users', search, filter],
    queryFn: () => api.users.getList({ search, ...filter })
  });
  
  const columns = [
    {
      header: '사용자',
      accessor: 'user',
      cell: (user: any) => (
        <div>
          <p className="font-medium">{user.name}</p>
          <p className="text-sm text-gray-500">{user.email}</p>
        </div>
      )
    },
    {
      header: 'KYC 상태',
      accessor: 'kycStatus',
      cell: (status: string) => {
        const variants = {
          verified: { icon: CheckBadgeIcon, color: 'success', text: '인증완료' },
          pending: { icon: null, color: 'warning', text: '대기중' },
          none: { icon: null, color: 'default', text: '미인증' }
        };
        
        const variant = variants[status as keyof typeof variants];
        
        return (
          <Badge variant={variant.color as any}>
            {variant.icon && <variant.icon className="w-3 h-3 mr-1" />}
            {variant.text}
          </Badge>
        );
      }
    },
    {
      header: '잔액',
      accessor: 'balance',
      cell: (balance: number) => (
        <p className="font-medium">${balance.toLocaleString()}</p>
      )
    },
    {
      header: '가입일',
      accessor: 'createdAt',
      cell: (date: string) => formatDate(date)
    },
    {
      header: '상태',
      accessor: 'status',
      cell: (status: string) => (
        <Badge variant={status === 'active' ? 'success' : 'danger'}>
          {status === 'active' ? '활성' : '정지'}
        </Badge>
      )
    }
  ];
  
  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          사용자 관리
        </h3>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              type="search"
              placeholder="이름, 이메일로 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={MagnifyingGlassIcon}
            />
          </div>
          
          <div className="flex gap-2">
            <Select
              value={filter.kycStatus}
              onChange={(e) => setFilter({ ...filter, kycStatus: e.target.value })}
            >
              <option value="all">모든 KYC</option>
              <option value="verified">인증완료</option>
              <option value="pending">대기중</option>
              <option value="none">미인증</option>
            </Select>
            
            <Select
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            >
              <option value="all">모든 상태</option>
              <option value="active">활성</option>
              <option value="suspended">정지</option>
            </Select>
          </div>
        </div>
      </div>
      
      <Table
        columns={columns}
        data={data?.users || []}
        loading={isLoading}
        onRowClick={(user) => {
          window.open(`/users/${user.id}`, '_self');
        }}
      />
    </div>
  );
};
```

#### 6.2 수익/비용 분석 대시보드
```typescript
// src/components/analytics/RevenueAnalytics.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { api } from '@/lib/api';
import { Card } from '@/components/common/Card';
import { Select } from '@/components/common/Select';
import { formatCurrency } from '@/lib/utils/format';

export const RevenueAnalytics: React.FC = () => {
  const [period, setPeriod] = useState('7d');
  
  const { data, isLoading } = useQuery({
    queryKey: ['revenue-analytics', period],
    queryFn: () => api.analytics.getRevenue({ period })
  });
  
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          수익/비용 분석
        </h3>
        <Select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
        >
          <option value="7d">최근 7일</option>
          <option value="30d">최근 30일</option>
          <option value="90d">최근 90일</option>
        </Select>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <p className="text-sm text-gray-500">총 수익</p>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(data?.totalRevenue || 0)}
          </p>
          <p className="text-xs text-gray-500">
            +{data?.revenueGrowth || 0}% 전기 대비
          </p>
        </Card>
        
        <Card>
          <p className="text-sm text-gray-500">총 비용</p>
          <p className="text-2xl font-bold text-red-600">
            {formatCurrency(data?.totalCost || 0)}
          </p>
          <p className="text-xs text-gray-500">
            에너지 비용 포함
          </p>
        </Card>
        
        <Card>
          <p className="text-sm text-gray-500">순이익</p>
          <p className="text-2xl font-bold">
            {formatCurrency(data?.netProfit || 0)}
          </p>
          <p className="text-xs text-gray-500">
            마진율 {data?.profitMargin || 0}%
          </p>
        </Card>
      </div>
      
      <Card className="p-6">
        <h4 className="font-medium mb-4">수익 추이</h4>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data?.revenueChart || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => formatCurrency(value as number)} />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#3B82F6"
              fill="#3B82F6"
              fillOpacity={0.1}
            />
            <Area
              type="monotone"
              dataKey="cost"
              stroke="#EF4444"
              fill="#EF4444"
              fillOpacity={0.1}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h4 className="font-medium mb-4">수익 구성</h4>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data?.revenueBreakdown || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data?.revenueBreakdown?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
            </PieChart>
          </ResponsiveContainer>
        </Card>
        
        <Card className="p-6">
          <h4 className="font-medium mb-4">비용 구성</h4>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data?.costBreakdown || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data?.costBreakdown?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
};
```

## 📱 반응형 및 다크모드 지원

```typescript
// src/app/layout.tsx
import { ThemeProvider } from '@/providers/ThemeProvider';
import { TronLinkProvider } from '@/providers/TronLinkProvider';
import { QueryProvider } from '@/providers/QueryProvider';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <ThemeProvider>
          <QueryProvider>
            <TronLinkProvider>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Sidebar />
                <div className="lg:pl-64">
                  <Header />
                  <main className="p-4 lg:p-8">
                    {children}
                  </main>
                </div>
              </div>
            </TronLinkProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

## 🎨 브랜딩 커스터마이징

```typescript
// src/lib/branding/config.ts
export interface BrandingConfig {
  companyName: string;
  logo: string;
  favicon: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
  fonts: {
    heading: string;
    body: string;
  };
}

// 파트너별 브랜딩 설정 로드
export const loadBrandingConfig = async (): Promise<BrandingConfig> => {
  const response = await fetch('/api/partner/branding');
  return response.json();
};

// CSS 변수 적용
export const applyBranding = (config: BrandingConfig) => {
  const root = document.documentElement;
  root.style.setProperty('--color-primary', config.colors.primary);
  root.style.setProperty('--color-secondary', config.colors.secondary);
  root.style.setProperty('--color-accent', config.colors.accent);
  root.style.setProperty('--font-heading', config.fonts.heading);
  root.style.setProperty('--font-body', config.fonts.body);
};
```

## ✅ 검증 포인트

### 기능 검증
- [ ] TronLink 연결이 원활하게 작동하는가?
- [ ] 실시간 데이터 업데이트가 작동하는가?
- [ ] 출금 배치 생성 및 서명이 가능한가?
- [ ] 사용자 검색 및 필터링이 작동하는가?
- [ ] 분석 차트가 정확히 표시되는가?

### UI/UX 검증
- [ ] 모바일 반응형이 제대로 작동하는가?
- [ ] 다크모드가 모든 컴포넌트에 적용되는가?
- [ ] 로딩 상태와 에러 처리가 적절한가?
- [ ] 애니메이션이 부드럽게 작동하는가?

### 성능 검증
- [ ] 대량 데이터 로딩 시 성능이 유지되는가?
- [ ] 실시간 업데이트가 성능에 영향을 주지 않는가?
- [ ] 번들 크기가 적절한가?

## 🎉 기대 효과

1. **즉시 사용 가능**: 파트너사가 바로 운영을 시작할 수 있는 완성형 대시보드
2. **TronLink 통합**: 안전하고 편리한 지갑 관리
3. **실시간 모니터링**: 모든 운영 지표를 한눈에 확인
4. **효율적 운영**: 자동화된 프로세스로 운영 부담 감소
5. **커스터마이징**: 파트너사별 브랜딩 적용 가능