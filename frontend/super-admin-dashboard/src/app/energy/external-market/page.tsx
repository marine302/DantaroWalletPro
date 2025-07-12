'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RefreshCw, Plus, TrendingUp, TrendingDown, Zap } from 'lucide-react';

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
  const [selectedAmount, setSelectedAmount] = useState(1000000);

  // 모의 데이터 - 실제 구현에서는 API 호출
  useEffect(() => {
    const mockProviders: EnergyProvider[] = [
      {
        id: '1',
        name: 'JustLend Energy',
        status: 'active',
        pricePerEnergy: 0.0045,
        availableEnergy: 5000000,
        reliability: 98.5,
        avgResponseTime: 150,
        lastUpdated: '2024-01-15T10:30:00Z'
      },
      {
        id: '2',
        name: 'TronNRG',
        status: 'active',
        pricePerEnergy: 0.0052,
        availableEnergy: 3500000,
        reliability: 96.2,
        avgResponseTime: 220,
        lastUpdated: '2024-01-15T10:28:00Z'
      },
      {
        id: '3',
        name: 'TRONSCAN Energy',
        status: 'maintenance',
        pricePerEnergy: 0.0048,
        availableEnergy: 0,
        reliability: 99.1,
        avgResponseTime: 180,
        lastUpdated: '2024-01-15T09:45:00Z'
      },
      {
        id: '4',
        name: 'P2P Energy Trading',
        status: 'active',
        pricePerEnergy: 0.0041,
        availableEnergy: 2800000,
        reliability: 94.8,
        avgResponseTime: 300,
        lastUpdated: '2024-01-15T10:32:00Z'
      }
    ];

    const mockSummary: MarketSummary = {
      bestPrice: 0.0041,
      bestProvider: 'P2P Energy Trading',
      totalProviders: 4,
      activeProviders: 3,
      avgPrice: 0.0046,
      priceChange24h: -2.3
    };

    setTimeout(() => {
      setProviders(mockProviders);
      setMarketSummary(mockSummary);
      setIsLoading(false);
    }, 1000);
  }, []);

  const handleRefresh = () => {
    setIsLoading(true);
    // 새로고침 로직
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getReliabilityColor = (reliability: number) => {
    if (reliability >= 98) return 'text-green-600';
    if (reliability >= 95) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* 헤더 섹션 */}
        <div className="md:flex md:items-center md:justify-between mb-6">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
              외부 에너지 시장
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              외부 에너지 공급자 모니터링 및 구매 관리
            </p>
          </div>
          <div className="mt-4 flex gap-3 md:ml-4 md:mt-0">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              새로고침
            </Button>
            <Button variant="default" onClick={() => window.location.href = '/energy/external-market/purchase'}>
              <Plus className="w-4 h-4 mr-2" />
              수동 구매
            </Button>
          </div>
        </div>

        {/* 시장 요약 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">최저가</p>
                  <p className="text-2xl font-bold">{marketSummary?.bestPrice.toFixed(4)} TRX</p>
                  <p className="text-xs text-gray-400">per 에너지</p>
                </div>
                <Zap className="w-8 h-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">활성 공급자</p>
                  <p className="text-2xl font-bold">{marketSummary?.activeProviders}</p>
                  <p className="text-xs text-gray-400">/ {marketSummary?.totalProviders} 총</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">🏪</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">평균 가격</p>
                  <p className="text-2xl font-bold">{marketSummary?.avgPrice.toFixed(4)} TRX</p>
                  <p className="text-xs text-gray-400">per 에너지</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 text-sm font-medium">💰</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">24시간 변동</p>
                  <p className="text-2xl font-bold flex items-center">
                    {marketSummary?.priceChange24h && marketSummary.priceChange24h > 0 ? '+' : ''}
                    {marketSummary?.priceChange24h.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-400">가격 변동</p>
                </div>
                {marketSummary?.priceChange24h && marketSummary.priceChange24h > 0 ? (
                  <TrendingUp className="w-8 h-8 text-green-500" />
                ) : (
                  <TrendingDown className="w-8 h-8 text-red-500" />
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 에너지 구매 시뮬레이션 */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>에너지 구매 시뮬레이션</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  구매 수량
                </label>
                <select
                  value={selectedAmount}
                  onChange={(e) => setSelectedAmount(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={500000}>500,000 에너지</option>
                  <option value={1000000}>1,000,000 에너지</option>
                  <option value={2000000}>2,000,000 에너지</option>
                  <option value={5000000}>5,000,000 에너지</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  최적 공급자
                </label>
                <p className="text-lg font-medium text-blue-600">
                  {marketSummary?.bestProvider}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  예상 비용
                </label>
                <p className="text-lg font-medium text-gray-900">
                  {marketSummary ? (selectedAmount * marketSummary.bestPrice).toFixed(2) : '0'} TRX
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 공급자 목록 */}
        <Card>
          <CardHeader>
            <CardTitle>에너지 공급자 현황</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {providers.map((provider) => (
                <div key={provider.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">{provider.name}</h3>
                      <p className="text-sm text-gray-500">
                        마지막 업데이트: {new Date(provider.lastUpdated).toLocaleString()}
                      </p>
                    </div>
                    <Badge className={getStatusColor(provider.status)}>
                      {provider.status}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">가격 (per 에너지)</p>
                      <p className="font-medium">{provider.pricePerEnergy.toFixed(4)} TRX</p>
                    </div>
                    <div>
                      <p className="text-gray-500">가용 에너지</p>
                      <p className="font-medium">{provider.availableEnergy.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">신뢰도</p>
                      <p className={`font-medium ${getReliabilityColor(provider.reliability)}`}>
                        {provider.reliability}%
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">응답 시간</p>
                      <p className="font-medium">{provider.avgResponseTime}ms</p>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <Button variant="outline" size="sm" disabled={provider.status !== 'active'}>
                      구매
                    </Button>
                    <Button variant="ghost" size="sm">
                      상세보기
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
