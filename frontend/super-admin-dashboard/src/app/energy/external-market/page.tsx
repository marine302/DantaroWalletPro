'use client';

import { useState, useEffect, useRef } from 'react';
import { BasePage } from "@/components/ui/BasePage";
import { Section, StatCard, Button } from '@/components/ui/DarkThemeComponents';
import { RefreshCw, TrendingUp, TrendingDown, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import { tronNRGService, TronNRGProvider, TronNRGMarketData, TronNRGPrice } from '@/services/tron-nrg-service';

interface EnergyProvider extends TronNRGProvider {
  // 기존 필드는 TronNRGProvider에서 상속
  priceChangeStatus?: 'up' | 'down' | 'stable';
}

interface MarketSummary {
  bestPrice: number;
  bestProvider: string;
  totalProviders: number;
  activeProviders: number;
  avgPrice: number;
  priceChange24h: number;
  totalVolume: number;
  lastUpdated: string;
}

export default function ExternalEnergyMarketPage() {
  const [providers, setProviders] = useState<EnergyProvider[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [currentPrice, setCurrentPrice] = useState<TronNRGPrice | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');
  const [sortBy, setSortBy] = useState('price');
  const [filterStatus, setFilterStatus] = useState('all');
  const [lastUpdate, setLastUpdate] = useState<string>('');
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 초기 데이터 로드
    loadInitialData();
    
    // 실시간 가격 업데이트 연결
    connectPriceStream();

    // 정기적으로 공급자 정보 업데이트 (30초마다)
    const providerInterval = setInterval(loadProviders, 30000);

    // 컴포넌트 언마운트 시 정리
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearInterval(providerInterval);
    };
  }, []);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      
      // 병렬로 데이터 로드
      const [marketData, providersData, priceData] = await Promise.all([
        tronNRGService.getMarketData(),
        tronNRGService.getProviders(),
        tronNRGService.getCurrentPrice()
      ]);

      // 마켓 데이터 변환
      const summary: MarketSummary = {
        bestPrice: marketData.bestBuyPrice,
        bestProvider: 'TronNRG',
        totalProviders: providersData.length + 8, // TronNRG + 기타 공급자들
        activeProviders: providersData.filter(p => p.status === 'online').length + 6,
        avgPrice: marketData.currentPrice,
        priceChange24h: marketData.dailyChange,
        totalVolume: marketData.dailyVolume,
        lastUpdated: new Date().toISOString()
      };

      // 공급자 데이터 변환 및 추가 Mock 데이터 병합
      const enhancedProviders: EnergyProvider[] = [
        ...providersData.map(p => ({
          ...p,
          priceChangeStatus: p.pricePerEnergy > marketData.currentPrice ? 'up' as const : 'down' as const
        })),
        // 추가 Mock 공급자들 (다양성을 위해)
        {
          id: 'p2p-energy-1',
          name: 'P2P Energy Trading',
          status: 'online' as const,
          pricePerEnergy: 0.0039,
          availableEnergy: 4500000,
          reliability: 97.8,
          avgResponseTime: 2.5,
          minOrderSize: 1000,
          maxOrderSize: 8000000,
          fees: { tradingFee: 0.002, withdrawalFee: 0.0004 },
          lastUpdated: new Date().toISOString(),
          priceChangeStatus: 'down' as const
        },
        {
          id: 'energy-market-pro',
          name: 'Energy Market Pro',
          status: 'online' as const,
          pricePerEnergy: 0.0038,
          availableEnergy: 3200000,
          reliability: 96.5,
          avgResponseTime: 3.1,
          minOrderSize: 500,
          maxOrderSize: 5000000,
          fees: { tradingFee: 0.0018, withdrawalFee: 0.0006 },
          lastUpdated: new Date().toISOString(),
          priceChangeStatus: 'stable' as const
        }
      ];

      setMarketSummary(summary);
      setProviders(enhancedProviders);
      setCurrentPrice(priceData);
      setLastUpdate(new Date().toLocaleTimeString());
      setConnectionStatus('connected');
      
    } catch (error) {
      console.error('❌ Failed to load initial data:', error);
      setConnectionStatus('disconnected');
    } finally {
      setIsLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const providersData = await tronNRGService.getProviders();
      const marketData = await tronNRGService.getMarketData();
      
      setProviders(prevProviders => {
        // TronNRG 공급자들만 업데이트하고 나머지는 유지
        const nonTronProviders = prevProviders.filter(p => !p.id.startsWith('tronnrg-'));
        const updatedTronProviders = providersData.map(p => ({
          ...p,
          priceChangeStatus: p.pricePerEnergy > marketData.currentPrice ? 'up' as const : 'down' as const
        }));
        
        return [...updatedTronProviders, ...nonTronProviders];
      });
      
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('❌ Failed to update providers:', error);
    }
  };

  const connectPriceStream = () => {
    try {
      setConnectionStatus('connecting');
      
      const ws = tronNRGService.connectPriceStream((price: TronNRGPrice) => {
        setCurrentPrice(price);
        setLastUpdate(new Date().toLocaleTimeString());
        
        // 가격 변동에 따라 마켓 요약 업데이트
        setMarketSummary(prev => prev ? {
          ...prev,
          avgPrice: price.price,
          priceChange24h: price.change24h,
          lastUpdated: price.timestamp
        } : null);
      });
      
      if (ws) {
        wsRef.current = ws;
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (error) {
      console.error('❌ Failed to connect price stream:', error);
      setConnectionStatus('disconnected');
    }
  };

  const handleRefresh = async () => {
    await loadInitialData();
  };

  const handlePurchase = async (provider: EnergyProvider) => {
    try {
      // 구매 모달이나 페이지로 이동하는 로직
      // 현재는 알림으로 대체
      alert(`${provider.name}에서 에너지 구매를 시작합니다.\n가격: $${provider.pricePerEnergy}\n가용량: ${provider.availableEnergy.toLocaleString()}`);
    } catch (error) {
      console.error('❌ Purchase failed:', error);
      alert('구매 요청 중 오류가 발생했습니다.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-400';
      case 'offline': return 'text-red-400';
      case 'maintenance': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      online: 'bg-green-900 text-green-200',
      offline: 'bg-red-900 text-red-200',
      maintenance: 'bg-yellow-900 text-yellow-200'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-900 text-gray-200';
  };

  const getPriceChangeIcon = (status?: 'up' | 'down' | 'stable') => {
    switch (status) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-400" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-green-400" />;
      default: return <div className="w-4 h-4 bg-gray-400 rounded-full" />;
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': 
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'connecting': 
        return <div className="w-4 h-4 animate-spin rounded-full border-2 border-yellow-400 border-t-transparent" />;
      case 'disconnected': 
        return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
  };

  // 필터링 및 정렬된 공급자 목록
  const filteredAndSortedProviders = providers
    .filter(provider => {
      if (filterStatus === 'all') return true;
      return provider.status === filterStatus;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'price': return a.pricePerEnergy - b.pricePerEnergy;
        case 'reliability': return b.reliability - a.reliability;
        case 'response': return a.avgResponseTime - b.avgResponseTime;
        case 'available': return b.availableEnergy - a.availableEnergy;
        default: return 0;
      }
    });

  if (isLoading) {
    return (
      <BasePage title="외부 에너지 마켓" description="외부 에너지 제공업체와 시장 현황을 확인합니다">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </BasePage>
    );
  }

  return (
    <BasePage title="외부 에너지 마켓" description="외부 에너지 제공업체와 시장 현황을 확인합니다">
      <div className="space-y-6">
        {/* 연결 상태 및 실시간 정보 */}
        <Section title="연결 상태">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getConnectionStatusIcon()}
                <span className="text-sm font-medium">
                  TronNRG API: {connectionStatus === 'connected' ? '연결됨' : connectionStatus === 'connecting' ? '연결 중...' : '연결 실패'}
                </span>
                {currentPrice && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-400">현재 가격:</span>
                    <span className="font-mono text-green-400">${currentPrice.price.toFixed(6)}</span>
                    <span className={`text-xs ${currentPrice.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({currentPrice.change24h >= 0 ? '+' : ''}{currentPrice.change24h.toFixed(2)}%)
                    </span>
                  </div>
                )}
              </div>
              <div className="text-xs text-gray-500">
                마지막 업데이트: {lastUpdate}
              </div>
            </div>
          </div>
        </Section>

        {/* 시장 요약 */}
        {marketSummary && (
          <Section title="시장 요약">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <StatCard
                title="최저가"
                value={`$${marketSummary.bestPrice.toFixed(6)}`}
                trend="down"
              />
              <StatCard
                title="활성 제공업체"
                value={`${marketSummary.activeProviders}/${marketSummary.totalProviders}`}
                trend="up"
              />
              <StatCard
                title="평균 가격"
                value={`$${marketSummary.avgPrice.toFixed(6)}`}
                trend="neutral"
              />
              <StatCard
                title="24h 변동"
                value={`${marketSummary.priceChange24h.toFixed(2)}%`}
                trend={marketSummary.priceChange24h > 0 ? "up" : "down"}
              />
              <StatCard
                title="24h 거래량"
                value={marketSummary.totalVolume.toLocaleString()}
                trend="up"
              />
            </div>
          </Section>
        )}

        {/* 필터 및 정렬 */}
        <Section title="필터 및 정렬">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-200 min-w-[80px]">정렬 기준:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="price">가격순</option>
                <option value="reliability">신뢰도순</option>
                <option value="response">응답속도순</option>
                <option value="available">가용량순</option>
              </select>
            </div>
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-200 min-w-[80px]">상태 필터:</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">전체</option>
                <option value="online">온라인</option>
                <option value="offline">오프라인</option>
                <option value="maintenance">점검중</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={handleRefresh} disabled={isLoading}>
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                새로고침
              </Button>
              <Button variant="secondary" onClick={connectPriceStream}>
                실시간 연결
              </Button>
            </div>
          </div>
        </Section>

        {/* 에너지 제공업체 목록 */}
        <Section title="에너지 제공업체">
          <div className="grid gap-4">
            {filteredAndSortedProviders.map((provider) => (
              <div key={provider.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Zap className="w-6 h-6 text-blue-400" />
                    <h3 className="text-lg font-semibold">{provider.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(provider.status)}`}>
                      {provider.status === 'online' ? '온라인' : provider.status === 'maintenance' ? '점검중' : '오프라인'}
                    </span>
                    {provider.id.startsWith('tronnrg-') && (
                      <span className="px-2 py-1 bg-blue-900 text-blue-200 rounded-full text-xs">
                        TronNRG API
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      onClick={() => handlePurchase(provider)}
                      disabled={provider.status !== 'online'}
                    >
                      구매하기
                    </Button>
                    <Button variant="secondary">
                      상세정보
                    </Button>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">단가</p>
                    <div className="flex items-center gap-2">
                      <p className="text-lg font-bold text-green-400">${provider.pricePerEnergy.toFixed(6)}</p>
                      {getPriceChangeIcon(provider.priceChangeStatus)}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">가용량</p>
                    <p className="font-medium">{provider.availableEnergy.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">신뢰도</p>
                    <p className="font-medium">{provider.reliability}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">응답 시간</p>
                    <p className="font-medium">{provider.avgResponseTime}초</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">최소 주문</p>
                    <p className="text-sm">{provider.minOrderSize.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">수수료</p>
                    <p className="text-sm">{(provider.fees.tradingFee * 100).toFixed(3)}%</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm">
                      <span className={`flex items-center gap-1 ${getStatusColor(provider.status)}`}>
                        <div className={`w-2 h-2 rounded-full ${provider.status === 'online' ? 'bg-green-400' : provider.status === 'maintenance' ? 'bg-yellow-400' : 'bg-red-400'}`}></div>
                        {provider.status === 'online' ? '서비스 중' : provider.status === 'maintenance' ? '점검 중' : '서비스 중단'}
                      </span>
                      <span className="text-gray-400">
                        신뢰도: {provider.reliability}%
                      </span>
                      <span className="text-gray-400">
                        최대 주문: {provider.maxOrderSize.toLocaleString()}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      업데이트: {new Date(provider.lastUpdated).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* 시장 동향 및 실시간 데이터 */}
        <Section title="시장 동향">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-green-400" />
                가격 동향
              </h4>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">현재 최저가</span>
                  <span className="text-green-400">${marketSummary?.bestPrice.toFixed(6)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">24시간 평균</span>
                  <span>${marketSummary?.avgPrice.toFixed(6)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">변동률</span>
                  <span className={marketSummary && marketSummary.priceChange24h >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {marketSummary?.priceChange24h.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-400" />
                공급자 현황
              </h4>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">총 공급자</span>
                  <span>{marketSummary?.totalProviders}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">활성 공급자</span>
                  <span className="text-green-400">{marketSummary?.activeProviders}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TronNRG 연결</span>
                  <span className="flex items-center gap-1">
                    {getConnectionStatusIcon()}
                    <span className="text-xs">
                      {connectionStatus === 'connected' ? '실시간' : '오프라인'}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          {currentPrice && (
            <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-yellow-400" />
                실시간 TronNRG 데이터
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-400">현재가</p>
                  <p className="text-xl font-bold text-green-400">${currentPrice.price.toFixed(6)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">24h 변동</p>
                  <p className={`text-lg font-semibold ${currentPrice.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {currentPrice.change24h >= 0 ? '+' : ''}{currentPrice.change24h.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">24h 거래량</p>
                  <p className="text-lg font-semibold">{currentPrice.volume24h.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">통화</p>
                  <p className="text-lg font-semibold text-yellow-400">{currentPrice.currency}</p>
                </div>
              </div>
            </div>
          )}
        </Section>
      </div>
    </BasePage>
  );
}
