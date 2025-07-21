'use client';

import { useState, useEffect, useRef } from 'react';
import { BasePage } from "@/components/ui/BasePage";
import { Section, StatCard, Button } from '@/components/ui/DarkThemeComponents';
import { RefreshCw, TrendingUp, TrendingDown, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import { tronNRGService, TronNRGProvider, TronNRGMarketData, TronNRGPrice } from '@/services/tron-nrg-service';
import { energyTronService, EnergyTronProvider, EnergyTronMarketData, ProviderComparison } from '@/services/energytron-service';

interface CombinedProvider {
  id: string;
  name: string;
  provider: 'TronNRG' | 'EnergyTron';
  status: 'online' | 'offline' | 'maintenance';
  pricePerEnergy: number;
  availableEnergy: number;
  reliability: number;
  avgResponseTime: number;
  minOrderSize: number;
  maxOrderSize: number;
  fees: {
    tradingFee: number;
    withdrawalFee: number;
  };
  lastUpdated: string;
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
  const [combinedProviders, setCombinedProviders] = useState<CombinedProvider[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [providerComparison, setProviderComparison] = useState<ProviderComparison | null>(null);
  const [tronNRGPrice, setTronNRGPrice] = useState<TronNRGPrice | null>(null);
  const [energyTronData, setEnergyTronData] = useState<EnergyTronMarketData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');
  const [sortBy, setSortBy] = useState('price');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterProvider, setFilterProvider] = useState('all'); // 추가: 공급자별 필터
  const [lastUpdate, setLastUpdate] = useState<string>('');
  
  const tronWSRef = useRef<WebSocket | null>(null);
  const energyTronWSRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 초기 데이터 로드
    loadInitialData();
    
    // 실시간 가격 업데이트 연결
    connectPriceStreams();

    // 정기적으로 공급자 정보 업데이트 (30초마다)
    const providerInterval = setInterval(loadAllProviders, 30000);

    // 컴포넌트 언마운트 시 정리
    return () => {
      if (tronWSRef.current) {
        tronWSRef.current.close();
      }
      if (energyTronWSRef.current) {
        energyTronWSRef.current.close();
      }
      clearInterval(providerInterval);
    };
  }, []);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setConnectionStatus('connecting');
      
      console.log('🔄 Loading initial external energy market data...');
      
      // 병렬로 두 공급자의 데이터 로드 (timeout 추가)
      const dataPromises = [
        Promise.race([
          tronNRGService.getMarketData(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
        ]),
        Promise.race([
          tronNRGService.getProviders(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
        ]),
        Promise.race([
          tronNRGService.getCurrentPrice(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
        ]),
        Promise.race([
          energyTronService.getMarketData(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
        ]),
        Promise.race([
          energyTronService.getProviders(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
        ]),
        Promise.race([
          energyTronService.compareProviders(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
        ])
      ];

      const [
        tronNRGMarketData,
        tronNRGProviders,
        tronNRGPrice,
        energyTronMarketData,
        energyTronProviders,
        comparison
      ] = await Promise.allSettled(dataPromises);

      // 결과 처리 (실패한 요청은 기본값 사용)
      const tronMarketData = tronNRGMarketData.status === 'fulfilled' ? tronNRGMarketData.value : {
        currentPrice: 0.0041,
        dailyVolume: 0,
        dailyChange: 0
      };
      
      const tronProviders = tronNRGProviders.status === 'fulfilled' 
        ? (Array.isArray(tronNRGProviders.value) ? tronNRGProviders.value : []) 
        : [];
      const tronPrice = tronNRGPrice.status === 'fulfilled' ? tronNRGPrice.value : null;
      
      const energyMarketData = energyTronMarketData.status === 'fulfilled' ? energyTronMarketData.value : {
        currentPrice: 0.0040,
        dailyVolume: 0,
        dailyChange: 0
      };
      
      const energyProviders = energyTronProviders.status === 'fulfilled' 
        ? (Array.isArray(energyTronProviders.value) ? energyTronProviders.value : [])
        : [];
      const providerComparison = comparison.status === 'fulfilled' ? comparison.value : null;

      // 공급자 데이터 통합
      const combined: CombinedProvider[] = [
        ...tronProviders.map((p: any) => ({
          ...p,
          provider: 'TronNRG' as const,
          priceChangeStatus: 'stable' as const
        })),
        ...energyProviders.map((p: any) => ({
          ...p,
          provider: 'EnergyTron' as const,
          priceChangeStatus: 'stable' as const
        }))
      ];

      // 마켓 서머리 계산
      const allPrices = combined.filter(p => p.status === 'online').map(p => p.pricePerEnergy);
      const bestPrice = allPrices.length > 0 ? Math.min(...allPrices) : 0;
      const bestProvider = combined.find(p => p.pricePerEnergy === bestPrice)?.name || 'Unknown';
      
      const summary: MarketSummary = {
        bestPrice,
        bestProvider,
        totalProviders: combined.length,
        activeProviders: combined.filter(p => p.status === 'online').length,
        avgPrice: allPrices.length > 0 ? allPrices.reduce((a, b) => a + b, 0) / allPrices.length : 0,
        priceChange24h: ((tronMarketData as any)?.dailyChange || 0) + ((energyMarketData as any)?.dailyChange || 0) / 2,
        totalVolume: ((tronMarketData as any)?.dailyVolume || 0) + ((energyMarketData as any)?.dailyVolume || 0),
        lastUpdated: new Date().toISOString()
      };

      setCombinedProviders(combined);
      setMarketSummary(summary);
      setTronNRGPrice(tronPrice as any);
      setEnergyTronData(energyMarketData as any);
      setProviderComparison(providerComparison as any);
      setLastUpdate(new Date().toLocaleTimeString());
      setConnectionStatus('connected');
      
      console.log('✅ External energy market data loaded successfully');
      
    } catch (error) {
      console.error('❌ Failed to load initial data:', error);
      setConnectionStatus('disconnected');
      
      // 에러 발생 시에도 기본 데이터 설정
      setCombinedProviders([]);
      setMarketSummary({
        bestPrice: 0,
        bestProvider: 'N/A',
        totalProviders: 0,
        activeProviders: 0,
        avgPrice: 0,
        priceChange24h: 0,
        totalVolume: 0,
        lastUpdated: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadAllProviders = async () => {
    try {
      const [tronNRGProviders, energyTronProviders] = await Promise.all([
        tronNRGService.getProviders(),
        energyTronService.getProviders()
      ]);
      
      const combined: CombinedProvider[] = [
        ...tronNRGProviders.map(p => ({
          ...p,
          provider: 'TronNRG' as const,
          priceChangeStatus: 'stable' as const
        })),
        ...energyTronProviders.map(p => ({
          ...p,
          provider: 'EnergyTron' as const,
          priceChangeStatus: 'stable' as const
        }))
      ];
      
      setCombinedProviders(combined);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('❌ Failed to update providers:', error);
    }
  };

  const connectPriceStreams = () => {
    try {
      setConnectionStatus('connecting');
      
      console.log('🔌 Connecting to price streams...');
      
      // TronNRG 가격 스트림 (timeout 설정)
      setTimeout(() => {
        try {
          const tronWS = tronNRGService.connectPriceStream((price: TronNRGPrice) => {
            setTronNRGPrice(price);
            setLastUpdate(new Date().toLocaleTimeString());
          });
          
          if (tronWS) {
            tronWSRef.current = tronWS;
          }
        } catch (error) {
          console.warn('⚠️ TronNRG WebSocket connection failed:', error);
        }
      }, 500);
      
      // EnergyTron 가격 스트림 (timeout 설정)
      setTimeout(() => {
        try {
          const energyTronWS = energyTronService.connectPriceStream((data: any) => {
            if (data.type === 'price_update') {
              setEnergyTronData(prev => prev ? {
                ...prev,
                currentPrice: data.data.price,
                timestamp: data.data.timestamp
              } : null);
              setLastUpdate(new Date().toLocaleTimeString());
            }
          });
          
          if (energyTronWS) {
            energyTronWSRef.current = energyTronWS;
          }
        } catch (error) {
          console.warn('⚠️ EnergyTron WebSocket connection failed:', error);
        }
      }, 1000);
      
      // 연결 상태를 connected로 설정 (WebSocket 실패해도 페이지는 동작)
      setTimeout(() => {
        setConnectionStatus('connected');
        console.log('✅ Price streams connection attempt completed');
      }, 1500);
      
    } catch (error) {
      console.error('❌ Failed to connect price streams:', error);
      setConnectionStatus('disconnected');
    }
  };

  const handleRefresh = async () => {
    await loadInitialData();
  };

  const handlePurchase = async (provider: CombinedProvider) => {
    try {
      // 구매 페이지로 이동
      window.location.href = `/energy/external-market/purchase?provider=${provider.id}&source=${provider.provider}`;
    } catch (error) {
      console.error('❌ Purchase navigation failed:', error);
      alert('구매 페이지 이동 중 오류가 발생했습니다.');
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

  // 필터링 및 정렬 로직
  const filteredAndSortedProviders = combinedProviders
    .filter(provider => {
      if (filterStatus !== 'all' && provider.status !== filterStatus) return false;
      if (filterProvider !== 'all' && provider.provider !== filterProvider) return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'price':
          return a.pricePerEnergy - b.pricePerEnergy;
        case 'reliability':
          return b.reliability - a.reliability;
        case 'response':
          return a.avgResponseTime - b.avgResponseTime;
        case 'available':
          return b.availableEnergy - a.availableEnergy;
        default:
          return 0;
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
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 space-y-4">
            {/* TronNRG 연결 상태 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getConnectionStatusIcon()}
                <span className="text-sm font-medium">
                  TronNRG API: {connectionStatus === 'connected' ? '연결됨' : connectionStatus === 'connecting' ? '연결 중...' : '연결 실패'}
                </span>
                {tronNRGPrice && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-400">TronNRG 가격:</span>
                    <span className="font-mono text-green-400">${tronNRGPrice.price.toFixed(6)}</span>
                    <span className={`text-xs ${tronNRGPrice.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({tronNRGPrice.change24h >= 0 ? '+' : ''}{tronNRGPrice.change24h.toFixed(2)}%)
                    </span>
                  </div>
                )}
              </div>
              <div className="text-xs text-gray-500">
                마지막 업데이트: {lastUpdate}
              </div>
            </div>

            {/* EnergyTron 연결 상태 */}
            <div className="flex items-center justify-between border-t border-gray-700 pt-3">
              <div className="flex items-center gap-3">
                {getConnectionStatusIcon()}
                <span className="text-sm font-medium">
                  EnergyTron API: {connectionStatus === 'connected' ? '연결됨' : connectionStatus === 'connecting' ? '연결 중...' : '연결 실패'}
                </span>
                {energyTronData && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-400">EnergyTron 가격:</span>
                    <span className="font-mono text-purple-400">${energyTronData.currentPrice.toFixed(6)}</span>
                    <span className={`text-xs ${energyTronData.dailyChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({energyTronData.dailyChange >= 0 ? '+' : ''}{energyTronData.dailyChange.toFixed(2)}%)
                    </span>
                  </div>
                )}
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
                value={filterProvider}
                onChange={(e) => setFilterProvider(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">전체 공급자</option>
                <option value="TronNRG">TronNRG</option>
                <option value="EnergyTron">EnergyTron</option>
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
              <Button variant="secondary" onClick={connectPriceStreams}>
                실시간 연결
              </Button>
            </div>
          </div>
        </Section>

        {/* 공급자 비교 */}
        {providerComparison && (
          <Section title="공급자 비교 분석">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 최적가 공급자 */}
                <div className="bg-green-900/20 rounded-lg p-4 border border-green-500/30">
                  <h4 className="text-lg font-semibold text-green-400 mb-2">💰 최저가 공급자</h4>
                  <p className="text-sm text-gray-300 mb-1">공급자: {providerComparison.bestPrice.provider}</p>
                  <p className="text-xl font-bold text-green-400">${providerComparison.bestPrice.price.toFixed(6)}</p>
                  <p className="text-sm text-green-300">절약: ${providerComparison.bestPrice.savings.toFixed(6)}</p>
                </div>

                {/* 최고 신뢰도 공급자 */}
                <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-500/30">
                  <h4 className="text-lg font-semibold text-blue-400 mb-2">🛡️ 최고 신뢰도</h4>
                  <p className="text-sm text-gray-300 mb-1">공급자: {providerComparison.bestReliability.provider}</p>
                  <p className="text-xl font-bold text-blue-400">{providerComparison.bestReliability.reliability}%</p>
                  <p className="text-sm text-blue-300">신뢰도 지수</p>
                </div>

                {/* 추천 공급자 */}
                <div className="bg-purple-900/20 rounded-lg p-4 border border-purple-500/30">
                  <h4 className="text-lg font-semibold text-purple-400 mb-2">⭐ 추천 공급자</h4>
                  <p className="text-sm text-gray-300 mb-1">추천: {providerComparison.recommendation.suggested}</p>
                  <p className="text-sm text-purple-300 mb-1">{providerComparison.recommendation.reason}</p>
                  <p className="text-sm font-bold text-purple-400">{providerComparison.recommendation.savings}</p>
                </div>
              </div>

              {/* 상세 비교 테이블 */}
              <div className="mt-6">
                <h4 className="text-lg font-semibold text-white mb-4">상세 비교</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-2 text-gray-300">공급자</th>
                        <th className="text-right py-2 text-gray-300">평균 가격</th>
                        <th className="text-right py-2 text-gray-300">신뢰도</th>
                        <th className="text-right py-2 text-gray-300">응답시간</th>
                        <th className="text-right py-2 text-gray-300">가용량</th>
                      </tr>
                    </thead>
                    <tbody>
                      {providerComparison.comparison.map((comp, index) => (
                        <tr key={index} className="border-b border-gray-800">
                          <td className="py-2 font-medium text-white">{comp.provider}</td>
                          <td className="py-2 text-right font-mono text-green-400">${comp.avgPrice.toFixed(6)}</td>
                          <td className="py-2 text-right text-blue-400">{comp.reliability}%</td>
                          <td className="py-2 text-right text-gray-300">{comp.responseTime}ms</td>
                          <td className="py-2 text-right text-gray-300">{comp.availableEnergy.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </Section>
        )}

        {/* 필터 및 정렬 */}
        <Section title="필터 및 정렬">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-200 min-w-[60px]">정렬:</label>
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
              <label className="text-sm font-medium text-gray-200 min-w-[80px]">공급자:</label>
              <select
                value={filterProvider}
                onChange={(e) => setFilterProvider(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">전체 공급자</option>
                <option value="TronNRG">TronNRG</option>
                <option value="EnergyTron">EnergyTron</option>
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
              <Button variant="secondary" onClick={connectPriceStreams}>
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
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      provider.provider === 'TronNRG' 
                        ? 'bg-blue-900 text-blue-200' 
                        : 'bg-purple-900 text-purple-200'
                    }`}>
                      {provider.provider}
                    </span>
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

          {tronNRGPrice && (
            <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-yellow-400" />
                실시간 TronNRG 데이터
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-400">현재가</p>
                  <p className="text-xl font-bold text-green-400">${tronNRGPrice.price.toFixed(6)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">24h 변동</p>
                  <p className={`text-lg font-semibold ${tronNRGPrice.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {tronNRGPrice.change24h >= 0 ? '+' : ''}{tronNRGPrice.change24h.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">24h 거래량</p>
                  <p className="text-lg font-semibold">{tronNRGPrice.volume24h.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">통화</p>
                  <p className="text-lg font-semibold text-yellow-400">{tronNRGPrice.currency}</p>
                </div>
              </div>
            </div>
          )}
        </Section>
      </div>
    </BasePage>
  );
}
