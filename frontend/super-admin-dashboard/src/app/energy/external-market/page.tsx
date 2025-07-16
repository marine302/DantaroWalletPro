'use client';

import { useState, useEffect } from 'react';
import { BasePage } from "@/components/ui/BasePage";
import { Section, StatCard, Button } from '@/components/ui/DarkThemeComponents';
import { RefreshCw, TrendingUp, TrendingDown, Zap } from 'lucide-react';

interface EnergyProvider {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'maintenance';
  pricePerEnergy: number;
  availableEnergy: number;
  reliability: number;
  avgResponseTime: number;
  lastUpdated: string;
}

interface MarketSummary {
  bestPrice: number;
  bestProvider: string;
  totalProviders: number;
  activeProviders: number;
  avgPrice: number;
  priceChange24h: number;
}

export default function ExternalEnergyMarketPage() {
  const [providers, setProviders] = useState<EnergyProvider[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState('price');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    // 모의 데이터
    const mockProviders: EnergyProvider[] = [
      {
        id: '1',
        name: 'P2P Energy Trading',
        status: 'active',
        pricePerEnergy: 0.0041,
        availableEnergy: 5000000,
        reliability: 98.5,
        avgResponseTime: 2.1,
        lastUpdated: new Date().toISOString()
      },
      {
        id: '2',
        name: 'Energy Market Pro',
        status: 'active',
        pricePerEnergy: 0.0038,
        availableEnergy: 3500000,
        reliability: 96.8,
        avgResponseTime: 3.2,
        lastUpdated: new Date().toISOString()
      },
      {
        id: '3',
        name: 'TronNRG',
        status: 'maintenance',
        pricePerEnergy: 0.0045,
        availableEnergy: 2000000,
        reliability: 94.2,
        avgResponseTime: 4.8,
        lastUpdated: new Date().toISOString()
      }
    ];

    const mockSummary: MarketSummary = {
      bestPrice: 0.0038,
      bestProvider: 'Energy Market Pro',
      totalProviders: 12,
      activeProviders: 9,
      avgPrice: 0.0042,
      priceChange24h: -2.3
    };

    setProviders(mockProviders);
    setMarketSummary(mockSummary);
    setIsLoading(false);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'inactive': return 'text-red-400';
      case 'maintenance': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-900 text-green-200',
      inactive: 'bg-red-900 text-red-200',
      maintenance: 'bg-yellow-900 text-yellow-200'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-900 text-gray-200';
  };

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
        {/* 시장 요약 */}
        {marketSummary && (
          <Section title="시장 요약">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="최저가"
                value={`$${marketSummary.bestPrice}`}
                trend="down"
              />
              <StatCard
                title="활성 제공업체"
                value={`${marketSummary.activeProviders}/${marketSummary.totalProviders}`}
                trend="up"
              />
              <StatCard
                title="평균 가격"
                value={`$${marketSummary.avgPrice}`}
                trend="neutral"
              />
              <StatCard
                title="24h 변동"
                value={`${marketSummary.priceChange24h}%`}
                trend={marketSummary.priceChange24h > 0 ? "up" : "down"}
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
                <option value="active">활성</option>
                <option value="inactive">비활성</option>
                <option value="maintenance">점검중</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                새로고침
              </Button>
            </div>
          </div>
        </Section>

        {/* 에너지 제공업체 목록 */}
        <Section title="에너지 제공업체">
          <div className="grid gap-4">
            {providers.map((provider) => (
              <div key={provider.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Zap className="w-6 h-6 text-blue-400" />
                    <h3 className="text-lg font-semibold">{provider.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(provider.status)}`}>
                      {provider.status}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button>
                      구매하기
                    </Button>
                    <Button variant="secondary">
                      상세정보
                    </Button>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">단가</p>
                    <p className="text-lg font-bold text-green-400">${provider.pricePerEnergy}</p>
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
                    <p className="text-sm text-gray-400">마지막 업데이트</p>
                    <p className="text-sm">{new Date(provider.lastUpdated).toLocaleTimeString()}</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm">
                      <span className={`flex items-center gap-1 ${getStatusColor(provider.status)}`}>
                        <div className={`w-2 h-2 rounded-full ${provider.status === 'active' ? 'bg-green-400' : provider.status === 'maintenance' ? 'bg-yellow-400' : 'bg-red-400'}`}></div>
                        {provider.status === 'active' ? '서비스 중' : provider.status === 'maintenance' ? '점검 중' : '서비스 중단'}
                      </span>
                      <span className="text-gray-400">
                        신뢰도: {provider.reliability}%
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

        {/* 시장 동향 */}
        <Section title="시장 동향">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <TrendingDown className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <h4 className="font-medium mb-1">가격 하락 중</h4>
                <p className="text-sm text-gray-400">지난 24시간 대비 2.3% 감소</p>
              </div>
              <div className="text-center">
                <TrendingUp className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                <h4 className="font-medium mb-1">공급량 증가</h4>
                <p className="text-sm text-gray-400">새로운 제공업체 3곳 추가</p>
              </div>
              <div className="text-center">
                <Zap className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                <h4 className="font-medium mb-1">품질 개선</h4>
                <p className="text-sm text-gray-400">평균 응답 시간 15% 단축</p>
              </div>
            </div>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
