'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { superAdminService } from '@/services/super-admin-service';

// 타입 정의
interface EnergyProvider {
  id: number;
  name: string;
  providerType: string;
  isActive: boolean;
  priority: number;
  lastPrice: number;
  priceUpdatedAt: string;
  successRate: number;
  averageResponseTime: number;
  totalPurchases: number;
  maxDailyPurchase: number;
  status: 'online' | 'offline' | 'maintenance';
}

interface EnergyPurchase {
  id: number;
  providerId: number;
  providerName: string;
  energyAmount: number;
  pricePerEnergy: number;
  totalCost: number;
  status: 'pending' | 'approved' | 'executing' | 'completed' | 'failed' | 'cancelled';
  createdAt: string;
  completedAt?: string;
  margin: number;
}

interface MarketStats {
  totalProviders: number;
  activeProviders: number;
  totalEnergyPurchased: number;
  totalCostToday: number;
  averagePrice: number;
  lowestPrice: number;
  highestPrice: number;
}

// 커스텀 Tabs 컴포넌트
interface TabsProps {
  defaultValue: string;
  children: React.ReactNode;
  className?: string;
}

interface TabsListProps {
  children: React.ReactNode;
  className?: string;
}

interface TabsTriggerProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

interface TabsContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

const Tabs: React.FC<TabsProps> = ({ defaultValue, children, className }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);
  
  return (
    <div className={className}>
      {React.Children.map(children, child => 
        React.isValidElement(child) ? React.cloneElement(child as React.ReactElement<{activeTab?: string; setActiveTab?: (tab: string) => void}>, { activeTab, setActiveTab }) : child
      )}
    </div>
  );
};

const TabsList: React.FC<TabsListProps> = ({ children, className }) => (
  <div className={`flex space-x-1 border-b border-gray-200 ${className || ''}`}>
    {children}
  </div>
);

const TabsTrigger: React.FC<TabsTriggerProps & {activeTab?: string; setActiveTab?: (tab: string) => void}> = ({ 
  value, children, className, activeTab, setActiveTab 
}) => (
  <button
    onClick={() => setActiveTab?.(value)}
    className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
      activeTab === value 
        ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-700' 
        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
    } ${className || ''}`}
  >
    {children}
  </button>
);

const TabsContent: React.FC<TabsContentProps & {activeTab?: string}> = ({ 
  value, children, className, activeTab 
}) => {
  if (activeTab !== value) return null;
  return <div className={`mt-4 ${className || ''}`}>{children}</div>;
};

// 커스텀 Input 컴포넌트
interface InputProps {
  type?: string;
  placeholder?: string;
  value?: string | number;
  defaultValue?: string | number;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string;
  min?: string | number;
  max?: string | number;
  step?: string | number;
}

const Input: React.FC<InputProps> = ({ className, ...props }) => (
  <input
    className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${className || ''}`}
    {...props}
  />
);

// 커스텀 Select 컴포넌트
interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

const Select: React.FC<SelectProps> = ({ value, onValueChange, children, className }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className={`relative ${className || ''}`}>
      {React.Children.map(children, child => 
        React.isValidElement(child) ? React.cloneElement(child as React.ReactElement<{value?: string; onValueChange?: (value: string) => void; isOpen?: boolean; setIsOpen?: (open: boolean) => void}>, { value, onValueChange, isOpen, setIsOpen }) : child
      )}
    </div>
  );
};

const SelectTrigger: React.FC<SelectTriggerProps & {value?: string; isOpen?: boolean; setIsOpen?: (open: boolean) => void}> = ({ 
  children, className, isOpen, setIsOpen 
}) => (
  <button
    onClick={() => setIsOpen?.(!isOpen)}
    className={`w-full px-3 py-2 text-left border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex justify-between items-center ${className || ''}`}
  >
    {children}
    <span className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}>▼</span>
  </button>
);

const SelectContent: React.FC<SelectContentProps & {isOpen?: boolean}> = ({ children, className, isOpen }) => {
  if (!isOpen) return null;
  return (
    <div className={`absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto ${className || ''}`}>
      {children}
    </div>
  );
};

const SelectItem: React.FC<SelectItemProps & {onValueChange?: (value: string) => void; setIsOpen?: (open: boolean) => void}> = ({ 
  value, children, className, onValueChange, setIsOpen 
}) => (
  <button
    onClick={() => {
      onValueChange?.(value);
      setIsOpen?.(false);
    }}
    className={`w-full px-3 py-2 text-left hover:bg-gray-100 ${className || ''}`}
  >
    {children}
  </button>
);

const SelectValue: React.FC<{placeholder?: string; value?: string}> = ({ placeholder, value }) => (
  <span className={value ? 'text-gray-900' : 'text-gray-500'}>
    {value || placeholder}
  </span>
);

export default function EnergyMarketPage() {
  // 상태 관리
  const [marketStats, setMarketStats] = useState<MarketStats>({
    totalProviders: 0,
    activeProviders: 0,
    totalEnergyPurchased: 0,
    totalCostToday: 0,
    averagePrice: 0,
    lowestPrice: 0,
    highestPrice: 0
  });

  const [providers, setProviders] = useState<EnergyProvider[]>([]);
  const [recentPurchases, setRecentPurchases] = useState<EnergyPurchase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 새 구매 폼 상태
  const [newPurchase, setNewPurchase] = useState({
    providerId: '',
    energyAmount: '',
    margin: '15'
  });

  // 데이터 로딩
  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // 공급자 목록 조회
      const providersData = await superAdminService.getEnergyProviders();
      
      // API 응답을 페이지 타입에 맞게 변환
      const mappedProviders: EnergyProvider[] = providersData.map((provider: unknown) => {
        const p = provider as Record<string, unknown>;
        return {
          id: p.id as number,
          name: p.name as string,
          providerType: (p.provider_type || p.providerType) as string,
          isActive: (p.is_active ?? p.isActive) as boolean,
          priority: (p.priority || 1) as number,
          lastPrice: (p.last_price || p.lastPrice || 0) as number,
          priceUpdatedAt: (p.price_updated_at || p.priceUpdatedAt || new Date().toISOString()) as string,
          successRate: (p.success_rate || p.successRate || 0) as number,
          averageResponseTime: (p.average_response_time || p.averageResponseTime || 0) as number,
          totalPurchases: (p.total_purchases || p.totalPurchases || 0) as number,
          maxDailyPurchase: (p.max_daily_purchase || p.maxDailyPurchase || 0) as number,
          status: (p.is_active ? 'online' : 'offline') as 'online' | 'offline' | 'maintenance'
        };
      });
      setProviders(mappedProviders);

      // 구매 기록 조회 (API 오류 시 빈 배열 사용)
      try {
        const purchasesData = await superAdminService.getEnergyPurchases();
        const purchases = purchasesData.purchases || [];
        const mappedPurchases: EnergyPurchase[] = purchases.map((purchase: unknown) => {
          const p = purchase as Record<string, unknown>;
          return {
            id: (p.purchase_id || p.id) as number,
            providerId: (p.provider_id || p.providerId) as number,
            providerName: (p.provider_name || p.providerName || 'Unknown') as string,
            energyAmount: (p.energy_amount || p.energyAmount) as number,
            pricePerEnergy: (p.price_per_energy || p.pricePerEnergy) as number,
            totalCost: (p.total_cost || p.totalCost) as number,
            status: p.status as 'pending' | 'approved' | 'executing' | 'completed' | 'failed' | 'cancelled',
            createdAt: (p.created_at || p.createdAt) as string,
            completedAt: (p.completed_at || p.completedAt) as string | undefined,
            margin: 15 // 기본값
          };
        });
        setRecentPurchases(mappedPurchases);
        
        // 시장 통계 계산
        const stats = calculateMarketStats(mappedProviders, mappedPurchases);
        setMarketStats(stats);
      } catch (purchaseError) {
        console.warn('구매 기록 로딩 오류:', purchaseError);
        setRecentPurchases([]);
        
        // 공급자만으로 통계 계산
        const stats = calculateMarketStats(mappedProviders, []);
        setMarketStats(stats);
      }

    } catch (err) {
      console.error('데이터 로딩 오류:', err);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
      
      // 오류 시 빈 데이터로 초기화
      setProviders([]);
      setRecentPurchases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const calculateMarketStats = (
    providers: EnergyProvider[], 
    purchases: EnergyPurchase[]
  ): MarketStats => {
    const activeProviders = providers.filter(p => p.isActive);
    const prices = providers.map(p => p.lastPrice).filter(p => p > 0);
    
    const today = new Date().toISOString().split('T')[0];
    const todayPurchases = purchases.filter(p => 
      p.createdAt.startsWith(today) && 
      p.status === 'completed'
    );

    return {
      totalProviders: providers.length,
      activeProviders: activeProviders.length,
      totalEnergyPurchased: todayPurchases.reduce((sum, p) => sum + p.energyAmount, 0),
      totalCostToday: todayPurchases.reduce((sum, p) => sum + p.totalCost, 0),
      averagePrice: prices.length > 0 ? prices.reduce((sum, p) => sum + p, 0) / prices.length : 0,
      lowestPrice: prices.length > 0 ? Math.min(...prices) : 0,
      highestPrice: prices.length > 0 ? Math.max(...prices) : 0
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'offline': return 'bg-red-100 text-red-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'executing': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount: number) => `$${amount.toFixed(2)}`;
  const formatPrice = (price: number) => `$${price.toFixed(6)}`;
  const formatEnergy = (amount: number) => amount.toLocaleString();

  const handleManualPurchase = () => {
    if (!newPurchase.providerId || !newPurchase.energyAmount) {
      alert('공급자와 에너지 수량을 선택해주세요.');
      return;
    }

    const provider = providers.find(p => p.id.toString() === newPurchase.providerId);
    if (!provider) return;

    const energyAmount = parseInt(newPurchase.energyAmount);
    const totalCost = energyAmount * provider.lastPrice;
    
    const purchase: EnergyPurchase = {
      id: recentPurchases.length + 1,
      providerId: provider.id,
      providerName: provider.name,
      energyAmount,
      pricePerEnergy: provider.lastPrice,
      totalCost,
      status: 'pending',
      createdAt: new Date().toISOString(),
      margin: parseInt(newPurchase.margin)
    };

    setRecentPurchases([purchase, ...recentPurchases]);
    setNewPurchase({ providerId: '', energyAmount: '', margin: '15' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">외부 에너지 시장 관리</h1>
        <Button onClick={loadData} disabled={loading}>
          {loading ? '새로고침 중...' : '데이터 새로고침'}
        </Button>
      </div>

      {/* 로딩 상태 */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">데이터를 불러오는 중...</p>
        </div>
      )}

      {/* 오류 상태 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">오류가 발생했습니다</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <div className="-mx-2 -my-1.5 flex">
                  <Button
                    onClick={loadData}
                    className="bg-red-50 px-2 py-1.5 rounded-md text-sm text-red-800 hover:bg-red-100"
                  >
                    다시 시도
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 데이터가 로딩되었을 때만 표시 */}
      {!loading && !error && (
        <>
          {/* 시장 현황 요약 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">활성 공급자</CardTitle>
                <span className="text-2xl">🏪</span>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{marketStats.activeProviders}/{marketStats.totalProviders}</div>
                <p className="text-xs text-gray-500">전체 등록 공급자</p>
              </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">오늘 구매량</CardTitle>
            <span className="text-2xl">⚡</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatEnergy(marketStats.totalEnergyPurchased)}</div>
            <p className="text-xs text-gray-500">에너지 단위</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">오늘 구매 비용</CardTitle>
            <span className="text-2xl">💰</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(marketStats.totalCostToday)}</div>
            <p className="text-xs text-gray-500">USDT</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 시세</CardTitle>
            <span className="text-2xl">📈</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPrice(marketStats.averagePrice)}</div>
            <p className="text-xs text-gray-500">에너지당 USDT</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="providers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="providers">공급자 관리</TabsTrigger>
          <TabsTrigger value="purchase">수동 구매</TabsTrigger>
          <TabsTrigger value="history">구매 이력</TabsTrigger>
          <TabsTrigger value="settings">자동 구매 설정</TabsTrigger>
        </TabsList>

        <TabsContent value="providers">
          <div className="grid gap-4">
            {providers.map((provider) => (
              <Card key={provider.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {provider.name}
                        <Badge className={getStatusColor(provider.status)}>
                          {provider.status}
                        </Badge>
                      </CardTitle>
                      <p className="text-sm text-gray-500">
                        우선순위 {provider.priority} • {provider.providerType}
                      </p>
                    </div>
                    <Button variant={provider.isActive ? "destructive" : "default"} size="sm">
                      {provider.isActive ? '비활성화' : '활성화'}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-500">현재 시세</p>
                      <p className="text-lg font-bold">{formatPrice(provider.lastPrice)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">성공률</p>
                      <p className="text-lg font-bold">{provider.successRate}%</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">응답시간</p>
                      <p className="text-lg font-bold">{provider.averageResponseTime}ms</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">일일 한도</p>
                      <p className="text-lg font-bold">{formatEnergy(provider.maxDailyPurchase)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="purchase">
          <Card>
            <CardHeader>
              <CardTitle>수동 에너지 구매</CardTitle>
              <p className="text-sm text-gray-500">
                긴급하게 에너지가 필요한 경우 수동으로 구매할 수 있습니다.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">공급자 선택</label>
                  <Select value={newPurchase.providerId} onValueChange={(value) => setNewPurchase({...newPurchase, providerId: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="공급자를 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      {providers.filter(p => p.isActive && p.status === 'online').map((provider) => (
                        <SelectItem key={provider.id} value={provider.id.toString()}>
                          {provider.name} - {formatPrice(provider.lastPrice)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">에너지 수량</label>
                  <Input
                    type="number"
                    placeholder="예: 50000"
                    value={newPurchase.energyAmount}
                    onChange={(e) => setNewPurchase({...newPurchase, energyAmount: e.target.value})}
                    min="1000"
                    step="1000"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">마진 (%)</label>
                  <Input
                    type="number"
                    placeholder="15"
                    value={newPurchase.margin}
                    onChange={(e) => setNewPurchase({...newPurchase, margin: e.target.value})}
                    min="5"
                    max="50"
                    step="1"
                  />
                </div>
              </div>

              {newPurchase.providerId && newPurchase.energyAmount && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">구매 예상 정보</h4>
                  {(() => {
                    const provider = providers.find(p => p.id.toString() === newPurchase.providerId);
                    if (!provider) return null;
                    
                    const energyAmount = parseInt(newPurchase.energyAmount);
                    const cost = energyAmount * provider.lastPrice;
                    const margin = parseInt(newPurchase.margin);
                    const sellingPrice = provider.lastPrice * (1 + margin / 100);
                    
                    return (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">구매 비용</p>
                          <p className="font-bold">{formatCurrency(cost)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">판매 단가</p>
                          <p className="font-bold">{formatPrice(sellingPrice)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">예상 매출</p>
                          <p className="font-bold">{formatCurrency(energyAmount * sellingPrice)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">예상 수익</p>
                          <p className="font-bold text-green-600">{formatCurrency(energyAmount * sellingPrice - cost)}</p>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}

              <Button onClick={handleManualPurchase} className="w-full">
                구매 요청
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>구매 이력</CardTitle>
              <p className="text-sm text-gray-500">
                최근 에너지 구매 내역을 확인할 수 있습니다.
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentPurchases.map((purchase) => (
                  <div key={purchase.id} className="flex justify-between items-center p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{purchase.providerName}</span>
                        <Badge className={getStatusColor(purchase.status)}>
                          {purchase.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">
                        {new Date(purchase.createdAt).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{formatEnergy(purchase.energyAmount)} 에너지</p>
                      <p className="text-sm text-gray-500">{formatCurrency(purchase.totalCost)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>자동 구매 설정</CardTitle>
              <p className="text-sm text-gray-500">
                에너지 풀이 부족할 때 자동으로 구매하는 설정을 관리합니다.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">자동 구매 활성화</h4>
                  <p className="text-sm text-gray-500">임계값에 도달하면 자동으로 에너지를 구매합니다.</p>
                </div>
                <Button variant="outline">활성화</Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">임계값 (에너지)</label>
                  <Input type="number" placeholder="10000" defaultValue="10000" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">최대 구매량</label>
                  <Input type="number" placeholder="100000" defaultValue="100000" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">최대 단가 (USDT)</label>
                  <Input type="number" placeholder="0.0005" defaultValue="0.0005" step="0.0001" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">기본 마진 (%)</label>
                  <Input type="number" placeholder="15" defaultValue="15" />
                </div>
              </div>

              <Button className="w-full">설정 저장</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
        </>
      )}
    </div>
  );
}
