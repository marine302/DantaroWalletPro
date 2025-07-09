# Copilot 문서 #39: 외부 에너지 공급자 연동 프론트엔드

## 📋 개요
Copilot 문서 #38(외부 에너지 공급자 연동)의 프론트엔드 구현사항을 정리합니다. 슈퍼 어드민이 외부 에너지 시장을 모니터링하고 구매를 관리할 수 있는 UI를 제공합니다.

## 🎯 주요 구현 영역

### 1. 슈퍼 어드민 대시보드 - 에너지 시장 모니터링

#### 1.1 실시간 가격 모니터링 대시보드
```typescript
// pages/superadmin/energy-market/index.tsx
import React, { useState, useEffect } from 'react';
import { Card, Badge, Button } from '@/components/ui';
import { ArrowUpIcon, ArrowDownIcon, BoltIcon } from '@heroicons/react/24/outline';
import { useEnergyMarket } from '@/hooks/useEnergyMarket';

export default function EnergyMarketDashboard() {
  const { providers, bestPrice, priceHistory, isLoading } = useEnergyMarket();
  const [selectedAmount, setSelectedAmount] = useState(1000000);
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">외부 에너지 시장</h1>
        <div className="flex gap-4">
          <Button variant="outline" onClick={() => window.location.reload()}>
            <RefreshIcon className="w-4 h-4 mr-2" />
            새로고침
          </Button>
          <Button variant="primary" onClick={() => router.push('/superadmin/energy-market/purchase')}>
            <PlusIcon className="w-4 h-4 mr-2" />
            수동 구매
          </Button>
        </div>
      </div>
      
      {/* 시장 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">최저가</p>
              <p className="text-2xl font-bold">{bestPrice?.price || '-'} TRX</p>
              <p className="text-xs text-gray-400">per 에너지</p>
            </div>
            <BoltIcon className="w-8 h-8 text-yellow-500" />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">평균가</p>
              <p className="text-2xl font-bold">{calculateAverage(providers)} TRX</p>
              <p className="text-xs text-gray-400">per 에너지</p>
            </div>
            <TrendIndicator value={priceHistory.trend} />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">활성 공급자</p>
              <p className="text-2xl font-bold">{providers.filter(p => p.isActive).length}</p>
              <p className="text-xs text-gray-400">/ {providers.length} 전체</p>
            </div>
            <UsersIcon className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">24시간 구매량</p>
              <p className="text-2xl font-bold">{formatNumber(stats.dailyPurchased)}</p>
              <p className="text-xs text-gray-400">에너지</p>
            </div>
            <ChartBarIcon className="w-8 h-8 text-green-500" />
          </div>
        </Card>
      </div>
      
      {/* 공급자별 가격 비교 */}
      <Card>
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">공급자별 가격 비교</h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">구매량:</span>
              <input
                type="number"
                value={selectedAmount}
                onChange={(e) => setSelectedAmount(Number(e.target.value))}
                className="w-32 px-3 py-1 border rounded-lg text-sm"
                step="100000"
              />
              <span className="text-sm text-gray-500">에너지</span>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">공급자</th>
                  <th className="text-right py-3 px-4">단가 (TRX)</th>
                  <th className="text-right py-3 px-4">총 비용</th>
                  <th className="text-right py-3 px-4">가용량</th>
                  <th className="text-right py-3 px-4">예상 시간</th>
                  <th className="text-center py-3 px-4">상태</th>
                  <th className="text-center py-3 px-4">액션</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((provider) => (
                  <ProviderRow 
                    key={provider.id}
                    provider={provider}
                    amount={selectedAmount}
                    onPurchase={() => handleQuickPurchase(provider, selectedAmount)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
      
      {/* 가격 추이 차트 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">24시간 가격 추이</h2>
        <PriceHistoryChart data={priceHistory.data} providers={providers} />
      </Card>
    </div>
  );
}

// 공급자 행 컴포넌트
const ProviderRow: React.FC<{provider: Provider, amount: number, onPurchase: () => void}> = ({
  provider, amount, onPurchase
}) => {
  const totalCost = provider.price * amount;
  const canPurchase = provider.available >= amount && provider.isActive;
  
  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <img src={provider.logo} alt={provider.name} className="w-6 h-6 rounded" />
          <span className="font-medium">{provider.name}</span>
          {provider.rating && (
            <Badge variant="secondary" size="sm">
              ⭐ {provider.rating}
            </Badge>
          )}
        </div>
      </td>
      <td className="text-right py-3 px-4">
        <div className="flex items-center justify-end gap-1">
          <span className="font-mono">{provider.price.toFixed(8)}</span>
          <PriceChangeIndicator change={provider.priceChange24h} />
        </div>
      </td>
      <td className="text-right py-3 px-4 font-semibold">
        {formatCurrency(totalCost, 'TRX')}
      </td>
      <td className="text-right py-3 px-4">
        {formatNumber(provider.available)}
      </td>
      <td className="text-right py-3 px-4 text-sm text-gray-500">
        {provider.estimatedTime || '즉시'}
      </td>
      <td className="text-center py-3 px-4">
        <Badge variant={provider.isActive ? 'success' : 'default'}>
          {provider.isActive ? '활성' : '비활성'}
        </Badge>
      </td>
      <td className="text-center py-3 px-4">
        <Button
          size="sm"
          variant="outline"
          disabled={!canPurchase}
          onClick={onPurchase}
        >
          구매
        </Button>
      </td>
    </tr>
  );
};
```

#### 1.2 자동 구매 규칙 관리
```typescript
// pages/superadmin/energy-market/auto-rules.tsx
import React, { useState } from 'react';
import { Card, Button, Toggle, Modal } from '@/components/ui';
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

export default function AutoPurchaseRules() {
  const { rules, isLoading } = useAutoPurchaseRules();
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">자동 구매 규칙</h1>
        <Button onClick={() => setShowCreateModal(true)}>
          <PlusIcon className="w-4 h-4 mr-2" />
          규칙 추가
        </Button>
      </div>
      
      {/* 규칙 상태 요약 */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {rules.filter(r => r.isActive).length}
            </div>
            <div className="text-sm text-gray-500">활성 규칙</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {todayExecutions}
            </div>
            <div className="text-sm text-gray-500">오늘 실행</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">
              {successRate}%
            </div>
            <div className="text-sm text-gray-500">성공률</div>
          </div>
        </Card>
      </div>
      
      {/* 규칙 목록 */}
      <div className="space-y-4">
        {rules.map((rule) => (
          <RuleCard key={rule.id} rule={rule} />
        ))}
      </div>
      
      {/* 규칙 생성 모달 */}
      <CreateRuleModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}

// 규칙 카드 컴포넌트
const RuleCard: React.FC<{rule: PurchaseRule}> = ({ rule }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold">{rule.name}</h3>
            <Badge variant={rule.isActive ? 'success' : 'default'}>
              {rule.isActive ? '활성' : '비활성'}
            </Badge>
            <Badge variant="secondary">
              우선순위 {rule.priority}
            </Badge>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">트리거:</span>
              <span className="ml-2 font-medium">
                {rule.triggerType === 'threshold' && `에너지 < ${formatNumber(rule.energyThreshold)}`}
                {rule.triggerType === 'schedule' && `스케줄: ${rule.scheduleCron}`}
                {rule.triggerType === 'percentage' && `잔량 < ${rule.thresholdPercentage}%`}
              </span>
            </div>
            <div>
              <span className="text-gray-500">구매량:</span>
              <span className="ml-2 font-medium">
                {rule.purchaseAmount ? formatNumber(rule.purchaseAmount) : `${rule.purchasePercentage}%`}
              </span>
            </div>
            <div>
              <span className="text-gray-500">최대 가격:</span>
              <span className="ml-2 font-medium">
                {rule.maxPrice} TRX
              </span>
            </div>
            <div>
              <span className="text-gray-500">마진:</span>
              <span className="ml-2 font-medium">
                {(rule.baseMargin * 100).toFixed(0)}%
                {rule.emergencyMargin && ` (긴급: ${(rule.emergencyMargin * 100).toFixed(0)}%)`}
              </span>
            </div>
          </div>
          
          {isExpanded && (
            <div className="mt-4 pt-4 border-t">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 mb-1">실행 제한</p>
                  <p>일일 최대: {rule.maxDailyExecutions}회</p>
                  <p>쿨다운: {rule.cooldownMinutes}분</p>
                  <p>오늘 실행: {rule.dailyExecutionCount}회</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">선호 공급자</p>
                  {rule.preferredProviders?.map(p => (
                    <Badge key={p} variant="outline" size="sm" className="mr-1">
                      {p}
                    </Badge>
                  ))}
                </div>
              </div>
              
              {rule.lastExecutedAt && (
                <p className="mt-2 text-xs text-gray-500">
                  마지막 실행: {formatDateTime(rule.lastExecutedAt)}
                </p>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          <Toggle
            checked={rule.isActive}
            onChange={(checked) => toggleRule(rule.id, checked)}
          />
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <ChevronDownIcon 
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            />
          </Button>
          <Button size="sm" variant="ghost">
            <PencilIcon className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost" className="text-red-600">
            <TrashIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};
```

#### 1.3 구매 요청 및 승인
```typescript
// pages/superadmin/energy-market/purchase.tsx
import React, { useState } from 'react';
import { Card, Button, Select, Input } from '@/components/ui';
import { CalculatorIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';

export default function ManualPurchasePage() {
  const [formData, setFormData] = useState({
    energyAmount: 1000000,
    maxPrice: '',
    preferredProvider: '',
    urgency: 'normal'
  });
  const [comparison, setComparison] = useState(null);
  
  const handleCompare = async () => {
    const result = await api.energy.compareProviders(formData.energyAmount);
    setComparison(result);
  };
  
  const handlePurchase = async () => {
    await api.energy.createPurchase(formData);
    toast.success('구매 요청이 생성되었습니다');
    router.push('/superadmin/energy-market/purchases');
  };
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">수동 에너지 구매</h1>
      
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">구매 정보 입력</h2>
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              구매할 에너지량
            </label>
            <Input
              type="number"
              value={formData.energyAmount}
              onChange={(e) => setFormData({...formData, energyAmount: e.target.value})}
              placeholder="1000000"
              step="100000"
            />
            <p className="text-xs text-gray-500 mt-1">
              약 {Math.floor(formData.energyAmount / 32000)}건의 출금 가능
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              최대 허용 가격 (선택)
            </label>
            <Input
              type="number"
              value={formData.maxPrice}
              onChange={(e) => setFormData({...formData, maxPrice: e.target.value})}
              placeholder="0.00010"
              step="0.00001"
            />
            <p className="text-xs text-gray-500 mt-1">
              TRX per 에너지 (비워두면 제한 없음)
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              선호 공급자 (선택)
            </label>
            <Select
              value={formData.preferredProvider}
              onChange={(value) => setFormData({...formData, preferredProvider: value})}
            >
              <option value="">자동 선택</option>
              <option value="justlend">JustLend</option>
              <option value="tronnrg">TronNRG</option>
              <option value="tronscan">TRONSCAN</option>
              <option value="p2p">P2P Market</option>
            </Select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              긴급도
            </label>
            <Select
              value={formData.urgency}
              onChange={(value) => setFormData({...formData, urgency: value})}
            >
              <option value="normal">일반 (마진 20%)</option>
              <option value="urgent">긴급 (마진 35%)</option>
              <option value="emergency">매우 긴급 (마진 50%)</option>
            </Select>
          </div>
        </div>
        
        <div className="mt-6 flex gap-4">
          <Button variant="outline" onClick={handleCompare}>
            <CalculatorIcon className="w-4 h-4 mr-2" />
            가격 비교
          </Button>
        </div>
      </Card>
      
      {/* 가격 비교 결과 */}
      {comparison && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">가격 비교 결과</h2>
          
          <div className="space-y-3">
            {comparison.comparisons.map((offer, idx) => (
              <div 
                key={idx}
                className={`p-4 border rounded-lg ${idx === 0 ? 'border-blue-500 bg-blue-50' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{offer.provider}</span>
                      {idx === 0 && <Badge variant="primary">최저가</Badge>}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      단가: {offer.pricePerEnergy} TRX | 예상 시간: {offer.estimatedTime}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{offer.totalCost.toFixed(2)} TRX</div>
                    <div className="text-sm text-gray-500">≈ ${(offer.totalCost * 0.12).toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-2">예상 재판매 수익</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-500">구매 비용</p>
                <p className="font-semibold">{comparison.bestOffer.totalCost.toFixed(2)} TRX</p>
              </div>
              <div>
                <p className="text-gray-500">마진 ({getMarginRate(formData.urgency)}%)</p>
                <p className="font-semibold">
                  {(comparison.bestOffer.totalCost * getMarginRate(formData.urgency) / 100).toFixed(2)} TRX
                </p>
              </div>
              <div>
                <p className="text-gray-500">예상 수익</p>
                <p className="font-semibold text-green-600">
                  {(comparison.bestOffer.totalCost * (1 + getMarginRate(formData.urgency) / 100)).toFixed(2)} TRX
                </p>
              </div>
            </div>
          </div>
          
          <div className="mt-6">
            <Button className="w-full" size="lg" onClick={handlePurchase}>
              <ShoppingCartIcon className="w-5 h-5 mr-2" />
              구매 요청 생성
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
```

### 2. 구매 이력 및 승인 관리

#### 2.1 구매 요청 목록
```typescript
// pages/superadmin/energy-market/purchases.tsx
export default function PurchaseHistory() {
  const { purchases, stats } = usePurchaseHistory();
  const [filter, setFilter] = useState('all');
  
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">에너지 구매 관리</h1>
      
      {/* 통계 카드 */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          title="대기 중"
          value={stats.pending}
          icon={<ClockIcon />}
          color="yellow"
        />
        <StatCard
          title="진행 중"
          value={stats.executing}
          icon={<ArrowPathIcon />}
          color="blue"
        />
        <StatCard
          title="완료"
          value={stats.completed}
          icon={<CheckCircleIcon />}
          color="green"
        />
        <StatCard
          title="실패"
          value={stats.failed}
          icon={<XCircleIcon />}
          color="red"
        />
      </div>
      
      {/* 필터 및 액션 */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <FilterButton
            active={filter === 'all'}
            onClick={() => setFilter('all')}
          >
            전체
          </FilterButton>
          <FilterButton
            active={filter === 'pending'}
            onClick={() => setFilter('pending')}
          >
            승인 대기
          </FilterButton>
          <FilterButton
            active={filter === 'auto'}
            onClick={() => setFilter('auto')}
          >
            자동 구매
          </FilterButton>
          <FilterButton
            active={filter === 'manual'}
            onClick={() => setFilter('manual')}
          >
            수동 구매
          </FilterButton>
        </div>
      </div>
      
      {/* 구매 목록 테이블 */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>시간</TableHead>
              <TableHead>공급자</TableHead>
              <TableHead>에너지량</TableHead>
              <TableHead>비용</TableHead>
              <TableHead>마진</TableHead>
              <TableHead>상태</TableHead>
              <TableHead>유형</TableHead>
              <TableHead>액션</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {purchases.map((purchase) => (
              <PurchaseRow key={purchase.id} purchase={purchase} />
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

// 구매 행 컴포넌트
const PurchaseRow: React.FC<{purchase: Purchase}> = ({ purchase }) => {
  const statusColors = {
    pending: 'warning',
    approved: 'info',
    executing: 'info',
    completed: 'success',
    failed: 'error',
    cancelled: 'default'
  };
  
  return (
    <TableRow>
      <TableCell>{purchase.id}</TableCell>
      <TableCell>{formatDateTime(purchase.createdAt)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <img src={purchase.provider.logo} className="w-5 h-5" />
          {purchase.provider.name}
        </div>
      </TableCell>
      <TableCell>{formatNumber(purchase.energyAmount)}</TableCell>
      <TableCell>
        <div>
          <div>{purchase.totalCost.toFixed(2)} TRX</div>
          <div className="text-xs text-gray-500">
            @{purchase.pricePerEnergy}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="text-center">
          <Badge variant="secondary">
            {(purchase.marginRate * 100).toFixed(0)}%
          </Badge>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant={statusColors[purchase.status]}>
          {purchase.status}
        </Badge>
      </TableCell>
      <TableCell>
        <Badge variant="outline">
          {purchase.purchaseType}
        </Badge>
      </TableCell>
      <TableCell>
        {purchase.status === 'pending' && (
          <div className="flex gap-1">
            <Button size="xs" variant="primary" onClick={() => approvePurchase(purchase.id)}>
              승인
            </Button>
            <Button size="xs" variant="outline" onClick={() => rejectPurchase(purchase.id)}>
              거부
            </Button>
          </div>
        )}
        {purchase.status === 'completed' && purchase.transactionHash && (
          <Button size="xs" variant="ghost" onClick={() => viewOnTronscan(purchase.transactionHash)}>
            <ExternalLinkIcon className="w-3 h-3" />
          </Button>
        )}
      </TableCell>
    </TableRow>
  );
};
```

### 3. 실시간 알림 및 모니터링

#### 3.1 에너지 위기 알림 센터
```typescript
// components/energy/EmergencyAlertCenter.tsx
export const EmergencyAlertCenter: React.FC = () => {
  const { energyLevel, criticalThreshold, predictions } = useEnergyMonitor();
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  
  useEffect(() => {
    if (energyLevel < criticalThreshold) {
      setShowEmergencyModal(true);
      playAlertSound();
    }
  }, [energyLevel]);
  
  return (
    <>
      {/* 에너지 위기 배너 */}
      {energyLevel < criticalThreshold * 2 && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-red-800">
                  ⚠️ 에너지 위기 경고
                </h3>
                <p className="text-red-700">
                  현재 에너지: {formatNumber(energyLevel)} ({getPercentage(energyLevel)}%)
                  | 예상 소진 시간: {predictions.timeToDepletion}
                </p>
              </div>
            </div>
            <Button 
              variant="danger" 
              onClick={() => setShowEmergencyModal(true)}
            >
              긴급 구매
            </Button>
          </div>
        </div>
      )}
      
      {/* 긴급 구매 모달 */}
      <Modal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
        size="lg"
      >
        <div className="p-6">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mr-4">
              <BoltIcon className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold">긴급 에너지 구매</h2>
              <p className="text-gray-500">서비스 중단 방지를 위한 긴급 조치</p>
            </div>
          </div>
          
          {/* 추천 구매량 */}
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="font-semibold mb-2">AI 추천 구매량</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">최소 (1일)</p>
                <p className="text-lg font-bold">{formatNumber(predictions.minRequired)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">권장 (3일)</p>
                <p className="text-lg font-bold text-blue-600">
                  {formatNumber(predictions.recommended)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">안전 (7일)</p>
                <p className="text-lg font-bold">{formatNumber(predictions.safe)}</p>
              </div>
            </div>
          </div>
          
          {/* 빠른 구매 옵션 */}
          <div className="space-y-3">
            <QuickPurchaseOption
              amount={predictions.recommended}
              urgency="emergency"
              estimatedCost={calculateCost(predictions.recommended, 'emergency')}
              onSelect={() => executeEmergencyPurchase(predictions.recommended)}
            />
          </div>
        </div>
      </Modal>
    </>
  );
};
```

### 4. 분석 및 리포트

#### 4.1 외부 구매 분석 대시보드
```typescript
// components/analytics/ExternalPurchaseAnalytics.tsx
export const ExternalPurchaseAnalytics: React.FC = () => {
  const { analytics } = useExternalPurchaseAnalytics();
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 구매 비용 vs 재판매 수익 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">수익성 분석</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={analytics.profitability}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="purchaseCost" fill="#EF4444" name="구매 비용" />
            <Bar dataKey="resaleRevenue" fill="#10B981" name="재판매 수익" />
            <Bar dataKey="netProfit" fill="#3B82F6" name="순이익" />
          </BarChart>
        </ResponsiveContainer>
        
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">총 마진율</p>
            <p className="text-xl font-bold text-green-600">
              {analytics.averageMargin}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">ROI</p>
            <p className="text-xl font-bold text-blue-600">
              {analytics.roi}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">이번 달 순익</p>
            <p className="text-xl font-bold">
              {formatCurrency(analytics.monthlyProfit, 'TRX')}
            </p>
          </div>
        </div>
      </Card>
      
      {/* 공급자별 성과 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">공급자별 성과</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={analytics.providerPerformance}
              dataKey="volume"
              nameKey="provider"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {analytics.providerPerformance.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
};
```

## 🔔 실시간 업데이트 및 알림

### WebSocket 이벤트 처리
```typescript
// hooks/useEnergyMarketSocket.ts
export const useEnergyMarketSocket = () => {
  const ws = useWebSocket();
  const queryClient = useQueryClient();
  
  useEffect(() => {
    // 가격 업데이트
    ws.on('energy:price_update', (data) => {
      queryClient.setQueryData(['energy-providers'], (old) => {
        return updateProviderPrices(old, data);
      });
      
      // 가격 급등 알림
      if (data.priceChange > 20) {
        toast.warning(`${data.provider} 가격 ${data.priceChange}% 상승!`);
      }
    });
    
    // 구매 상태 업데이트
    ws.on('energy:purchase_status', (data) => {
      queryClient.invalidateQueries(['purchases', data.purchaseId]);
      
      if (data.status === 'completed') {
        toast.success(`에너지 구매 완료: ${formatNumber(data.energyAmount)}`);
      } else if (data.status === 'failed') {
        toast.error(`에너지 구매 실패: ${data.reason}`);
      }
    });
    
    // 에너지 위기 알림
    ws.on('energy:critical_alert', (data) => {
      showCriticalAlert(data);
    });
    
    return () => {
      ws.off('energy:price_update');
      ws.off('energy:purchase_status');
      ws.off('energy:critical_alert');
    };
  }, []);
};
```

## 🎉 기대 효과

1. **실시간 시장 모니터링**: 모든 공급자의 가격을 한눈에 비교
2. **자동화된 구매 관리**: 규칙 기반 자동 구매로 24/7 에너지 확보
3. **위기 대응 체계**: 에너지 부족 예측 및 긴급 구매 프로세스
4. **수익성 추적**: 구매 비용 대비 재판매 수익 실시간 분석
5. **효율적인 의사결정**: 데이터 기반 구매 전략 수립