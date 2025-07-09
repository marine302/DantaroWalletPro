# Copilot 문서 #37: 에너지 렌탈 서비스를 위한 프론트엔드 개선사항

## 📋 개요
Copilot 문서 #36(에너지 렌탈 서비스)의 추가로 인한 프론트엔드 UI/UX 개선사항을 정리합니다. 기존 문서 #31-35의 내용을 보완하여 새로운 기능을 원활하게 통합합니다.

## 🎯 주요 개선 영역

### 1. 파트너 관리자 대시보드 개선 (문서 #31 보완)

#### 1.1 에너지 렌탈 위젯 추가
```typescript
// components/dashboard/EnergyRentalWidget.tsx
import React from 'react';
import { Card, Progress, Badge, Button } from '@/components/ui';
import { BoltIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';
import { useEnergyRental } from '@/hooks/useEnergyRental';

export const EnergyRentalWidget: React.FC = () => {
  const { rentalPlan, usage, pricing } = useEnergyRental();
  
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BoltIcon className="w-5 h-5 text-yellow-500" />
          에너지 렌탈 현황
        </h3>
        <Badge variant={rentalPlan?.is_active ? 'success' : 'warning'}>
          {rentalPlan?.subscription_tier || '종량제'}
        </Badge>
      </div>
      
      {/* 구독 플랜 정보 */}
      {rentalPlan?.plan_type === 'subscription' && (
        <div className="space-y-3 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">월 할당량</span>
            <span className="font-medium">
              {formatNumber(rentalPlan.monthly_energy_quota)} 에너지
            </span>
          </div>
          <Progress 
            value={(usage.monthly_used / rentalPlan.monthly_energy_quota) * 100}
            className="h-2"
          />
          <div className="text-xs text-gray-500 text-right">
            {formatNumber(usage.monthly_used)} / {formatNumber(rentalPlan.monthly_energy_quota)} 사용
          </div>
        </div>
      )}
      
      {/* 비용 정보 */}
      <div className="border-t pt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">현재 단가</span>
          <span className="font-medium">
            {pricing.current_rate} TRX/에너지
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">이번 달 예상 비용</span>
          <span className="font-semibold text-lg">
            {formatCurrency(usage.estimated_monthly_cost)}
          </span>
        </div>
      </div>
      
      {/* 액션 버튼 */}
      <div className="mt-4 flex gap-2">
        <Button size="sm" variant="outline" className="flex-1">
          사용 내역
        </Button>
        <Button size="sm" variant="primary" className="flex-1">
          플랜 변경
        </Button>
      </div>
    </Card>
  );
};
```

#### 1.2 실시간 에너지 사용량 모니터링
```typescript
// components/energy/RealtimeEnergyMonitor.tsx
import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '@/hooks/useWebSocket';

export const RealtimeEnergyMonitor: React.FC = () => {
  const [data, setData] = useState([]);
  const ws = useWebSocket();
  
  useEffect(() => {
    const handleEnergyUpdate = (event) => {
      if (event.type === 'energy_usage') {
        setData(prev => [...prev.slice(-20), {
          time: new Date().toLocaleTimeString(),
          usage: event.data.energy_used,
          cost: event.data.cost
        }]);
      }
    };
    
    ws.on('energy_update', handleEnergyUpdate);
    return () => ws.off('energy_update', handleEnergyUpdate);
  }, []);
  
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">실시간 에너지 사용량</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis dataKey="time" />
          <YAxis yAxisId="left" label="에너지" />
          <YAxis yAxisId="right" orientation="right" label="비용 (TRX)" />
          <Tooltip />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="usage" 
            stroke="#3B82F6" 
            strokeWidth={2}
            dot={false}
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="cost" 
            stroke="#10B981" 
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* 실시간 통계 */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {formatNumber(data[data.length - 1]?.usage || 0)}
          </div>
          <div className="text-xs text-gray-500">현재 사용량</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {formatCurrency(data[data.length - 1]?.cost || 0)}
          </div>
          <div className="text-xs text-gray-500">현재 비용</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {calculateAverage(data.map(d => d.usage))}
          </div>
          <div className="text-xs text-gray-500">평균 사용량</div>
        </div>
      </div>
    </Card>
  );
};
```

### 2. 에너지 렌탈 관리 페이지 (신규)

#### 2.1 렌탈 플랜 선택 UI
```typescript
// pages/energy/rental-plans.tsx
import React, { useState } from 'react';
import { Card, Button, Badge } from '@/components/ui';
import { CheckIcon } from '@heroicons/react/24/solid';

const RENTAL_PLANS = [
  {
    id: 'pay_as_you_go',
    name: '종량제',
    description: '사용한 만큼만 지불',
    price: '0.00010 TRX/에너지',
    features: [
      '초기 비용 없음',
      '유연한 사용량',
      '실시간 과금',
      '최소 약정 없음'
    ]
  },
  {
    id: 'bronze',
    name: '브론즈',
    tier: 'bronze',
    description: '소규모 파트너용',
    price: '40 TRX/월',
    quota: '500,000 에너지',
    features: [
      '월 50만 에너지 제공',
      '초과분 0.00010 TRX/에너지',
      '기본 지원',
      '월 15건 출금 가능'
    ]
  },
  {
    id: 'silver',
    name: '실버',
    tier: 'silver',
    description: '중규모 파트너용',
    price: '300 TRX/월',
    quota: '5,000,000 에너지',
    features: [
      '월 500만 에너지 제공',
      '초과분 0.00008 TRX/에너지',
      '우선 지원',
      '월 156건 출금 가능'
    ],
    recommended: true
  },
  {
    id: 'gold',
    name: '골드',
    tier: 'gold',
    description: '대규모 파트너용',
    price: '2,000 TRX/월',
    quota: '50,000,000 에너지',
    features: [
      '월 5000만 에너지 제공',
      '초과분 0.00006 TRX/에너지',
      'VIP 지원',
      '월 1,562건 출금 가능'
    ]
  }
];

export default function RentalPlansPage() {
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [isUpgrading, setIsUpgrading] = useState(false);
  
  const handlePlanSelect = async (plan) => {
    setIsUpgrading(true);
    try {
      await api.energy.updateRentalPlan({
        plan_type: plan.tier ? 'subscription' : 'pay_as_you_go',
        subscription_tier: plan.tier
      });
      toast.success('플랜이 성공적으로 변경되었습니다');
    } catch (error) {
      toast.error('플랜 변경에 실패했습니다');
    } finally {
      setIsUpgrading(false);
    }
  };
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900">
          에너지 렌탈 플랜 선택
        </h1>
        <p className="mt-4 text-lg text-gray-600">
          비즈니스 규모에 맞는 최적의 플랜을 선택하세요
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {RENTAL_PLANS.map((plan) => (
          <Card 
            key={plan.id}
            className={`relative p-6 ${plan.recommended ? 'ring-2 ring-blue-500' : ''}`}
          >
            {plan.recommended && (
              <Badge className="absolute -top-3 right-4" variant="primary">
                추천
              </Badge>
            )}
            
            <div className="mb-6">
              <h3 className="text-xl font-semibold">{plan.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
            </div>
            
            <div className="mb-6">
              <div className="text-3xl font-bold">{plan.price}</div>
              {plan.quota && (
                <div className="text-sm text-gray-500 mt-1">{plan.quota}</div>
              )}
            </div>
            
            <ul className="space-y-3 mb-6">
              {plan.features.map((feature, idx) => (
                <li key={idx} className="flex items-start">
                  <CheckIcon className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-sm">{feature}</span>
                </li>
              ))}
            </ul>
            
            <Button
              variant={plan.recommended ? 'primary' : 'outline'}
              className="w-full"
              onClick={() => handlePlanSelect(plan)}
              disabled={isUpgrading}
            >
              {isUpgrading ? '처리 중...' : '플랜 선택'}
            </Button>
          </Card>
        ))}
      </div>
      
      {/* 비용 계산기 */}
      <div className="mt-12">
        <CostCalculator />
      </div>
    </div>
  );
}
```

#### 2.2 비용 계산기 컴포넌트
```typescript
// components/energy/CostCalculator.tsx
export const CostCalculator: React.FC = () => {
  const [monthlyWithdrawals, setMonthlyWithdrawals] = useState(100);
  const [selectedPlan, setSelectedPlan] = useState('pay_as_you_go');
  
  const calculateCost = () => {
    const energyPerWithdrawal = 32000;
    const totalEnergy = monthlyWithdrawals * energyPerWithdrawal;
    
    switch (selectedPlan) {
      case 'pay_as_you_go':
        return totalEnergy * 0.00010;
      case 'bronze':
        const bronzeOverage = Math.max(0, totalEnergy - 500000);
        return 40 + (bronzeOverage * 0.00010);
      case 'silver':
        const silverOverage = Math.max(0, totalEnergy - 5000000);
        return 300 + (silverOverage * 0.00008);
      case 'gold':
        const goldOverage = Math.max(0, totalEnergy - 50000000);
        return 2000 + (goldOverage * 0.00006);
      default:
        return 0;
    }
  };
  
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">비용 계산기</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            월 예상 출금 건수
          </label>
          <input
            type="range"
            min="10"
            max="10000"
            value={monthlyWithdrawals}
            onChange={(e) => setMonthlyWithdrawals(Number(e.target.value))}
            className="w-full"
          />
          <div className="text-center mt-2 text-2xl font-bold">
            {monthlyWithdrawals.toLocaleString()}건
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            선택한 플랜
          </label>
          <select
            value={selectedPlan}
            onChange={(e) => setSelectedPlan(e.target.value)}
            className="w-full p-2 border rounded-lg"
          >
            <option value="pay_as_you_go">종량제</option>
            <option value="bronze">브론즈</option>
            <option value="silver">실버</option>
            <option value="gold">골드</option>
          </select>
        </div>
        
        <div className="border-t pt-4">
          <div className="flex justify-between items-center">
            <span className="text-lg">예상 월 비용</span>
            <span className="text-3xl font-bold text-blue-600">
              {calculateCost().toFixed(2)} TRX
            </span>
          </div>
          <div className="text-sm text-gray-500 text-right mt-1">
            ≈ ${(calculateCost() * 0.12).toFixed(2)} USD
          </div>
        </div>
      </div>
    </Card>
  );
};
```

### 3. 사용자 모바일 앱 개선 (문서 #32 보완)

#### 3.1 에너지 상태 표시
```typescript
// mobile/components/EnergyStatusBadge.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useEnergyStatus } from '../hooks/useEnergyStatus';

export const EnergyStatusBadge: React.FC = () => {
  const { status, isLowEnergy } = useEnergyStatus();
  
  return (
    <View style={[styles.badge, isLowEnergy && styles.lowEnergy]}>
      <Text style={styles.text}>
        {isLowEnergy ? '⚠️ 에너지 부족' : '✅ 정상'}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    backgroundColor: '#10B981',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  lowEnergy: {
    backgroundColor: '#F59E0B',
  },
  text: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
});
```

### 4. 파트너사 운영 가이드 추가 (문서 #33 보완)

#### 4.1 에너지 렌탈 운영 가이드 섹션
```markdown
## 📋 에너지 렌탈 서비스 운영 가이드

### 1. 플랜 선택 가이드
- **종량제**: 초기 사업자, 불규칙한 거래량
- **브론즈**: 월 500건 미만 거래
- **실버**: 월 500-5,000건 거래
- **골드**: 월 5,000건 이상 거래

### 2. 비용 최적화 전략
1. **사용 패턴 분석**
   - 피크 시간대 파악
   - 월별 사용량 추이 확인
   
2. **플랜 전환 시점**
   - 3개월 연속 할당량 80% 초과 시 업그레이드
   - 3개월 연속 할당량 30% 미만 시 다운그레이드

3. **비용 절감 팁**
   - 배치 출금으로 에너지 효율화
   - 오프피크 시간대 활용
   - 불필요한 트랜잭션 최소화
```

### 5. 종합 대시보드 개선 (문서 #34 보완)

#### 5.1 에너지 비용 분석 위젯
```typescript
// components/analytics/EnergyCostAnalytics.tsx
export const EnergyCostAnalytics: React.FC = () => {
  const { data } = useEnergyCostAnalytics();
  
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">에너지 비용 분석</h3>
      
      {/* 비용 추이 차트 */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data.daily}>
          <defs>
            <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Area
            type="monotone"
            dataKey="cost"
            stroke="#3B82F6"
            fillOpacity={1}
            fill="url(#colorCost)"
          />
        </AreaChart>
      </ResponsiveContainer>
      
      {/* 핵심 지표 */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <MetricCard
          title="일 평균 비용"
          value={`${data.avgDailyCost} TRX`}
          change={data.costChange}
        />
        <MetricCard
          title="거래당 비용"
          value={`${data.costPerTx} TRX`}
          subtitle="평균"
        />
        <MetricCard
          title="비용 효율성"
          value={`${data.efficiency}%`}
          subtitle="vs 자체 스테이킹"
        />
        <MetricCard
          title="예상 월 비용"
          value={`${data.projectedMonthlyCost} TRX`}
          subtitle={`≈ $${data.projectedMonthlyCostUSD}`}
        />
      </div>
    </Card>
  );
};
```

### 6. 슈퍼 어드민 대시보드 추가 기능

#### 6.1 전체 에너지 렌탈 현황
```typescript
// superadmin/components/EnergyRentalOverview.tsx
export const EnergyRentalOverview: React.FC = () => {
  const { data } = useSuperAdminEnergyData();
  
  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold mb-6">에너지 렌탈 서비스 현황</h2>
      
      {/* 수익 현황 */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">수익 현황</h3>
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            title="일일 수익"
            value={`${data.dailyRevenue} TRX`}
            subtitle={`$${data.dailyRevenueUSD}`}
            trend={data.revenueTrend}
          />
          <StatCard
            title="활성 구독"
            value={data.activeSubscriptions}
            subtitle={`${data.subscriptionGrowth}% 성장`}
          />
          <StatCard
            title="평균 단가"
            value={`${data.avgPricePerEnergy} TRX`}
            subtitle="에너지당"
          />
        </div>
      </div>
      
      {/* 파트너별 사용량 TOP 10 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">상위 사용 파트너사</h3>
        <PartnerUsageRanking data={data.topPartners} />
      </div>
    </Card>
  );
};
```

## 🎨 UI/UX 개선사항

### 1. 에너지 관련 알림 디자인
```typescript
// 에너지 부족 경고 알림
<Alert variant="warning" icon={<ExclamationTriangleIcon />}>
  <AlertTitle>에너지 잔량 부족</AlertTitle>
  <AlertDescription>
    현재 에너지가 20% 남았습니다. 플랜 업그레이드를 고려해보세요.
  </AlertDescription>
  <AlertActions>
    <Button size="sm" variant="outline">나중에</Button>
    <Button size="sm" variant="primary">플랜 보기</Button>
  </AlertActions>
</Alert>

// 비용 초과 알림
<Alert variant="error" icon={<CurrencyDollarIcon />}>
  <AlertTitle>월 예산 초과 경고</AlertTitle>
  <AlertDescription>
    이번 달 에너지 비용이 설정한 예산을 초과했습니다.
  </AlertDescription>
</Alert>
```

### 2. 에너지 사용 시각화 개선
```typescript
// 실시간 게이지 차트
<GaugeChart
  value={currentUsage}
  max={dailyLimit}
  segments={[
    { threshold: 50, color: '#10B981' },
    { threshold: 80, color: '#F59E0B' },
    { threshold: 100, color: '#EF4444' }
  ]}
  label="오늘 사용량"
/>
```

## 📱 모바일 최적화

### 1. 터치 친화적 UI
- 최소 터치 영역 44x44px 보장
- 스와이프 제스처로 플랜 전환
- 하단 시트로 상세 정보 표시

### 2. 오프라인 지원
- 최근 에너지 사용 내역 캐싱
- 오프라인 비용 계산기
- 동기화 상태 표시

## 🔔 실시간 업데이트

### WebSocket 이벤트
```typescript
// 에너지 관련 실시간 이벤트
ws.on('energy:usage', (data) => {
  // 실시간 사용량 업데이트
  updateEnergyUsage(data);
});

ws.on('energy:threshold', (data) => {
  // 임계값 도달 알림
  showThresholdAlert(data);
});

ws.on('rental:plan_updated', (data) => {
  // 플랜 변경 알림
  refreshRentalPlan();
});
```

## 📊 분석 및 리포트

### 1. 에너지 효율성 리포트
- 시간대별 사용 패턴
- 거래 유형별 에너지 소비
- 비용 절감 기회 식별

### 2. ROI 분석
- 렌탈 vs 자체 스테이킹 비교
- 손익분기점 계산
- 장기 비용 예측

## 🎉 기대 효과

1. **직관적인 비용 관리**: 파트너사가 에너지 비용을 쉽게 이해하고 관리
2. **실시간 모니터링**: 에너지 사용량과 비용을 실시간으로 추적
3. **최적화된 의사결정**: 데이터 기반 플랜 선택 및 변경
4. **향상된 사용자 경험**: 모든 디바이스에서 일관된 경험
5. **프로액티브 관리**: 알림과 예측을 통한 선제적 대응