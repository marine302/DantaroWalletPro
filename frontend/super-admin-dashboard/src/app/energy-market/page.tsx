'use client';

import React, { useState, useEffect } from 'react';
import BasePage from '@/components/ui/BasePage';
import { Section, StatCard, Button, FormField } from '@/components/ui/DarkThemeComponents';
import { TrendingUp, TrendingDown, Zap, DollarSign } from 'lucide-react';

interface EnergyProvider {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'maintenance';
  pricePerEnergy: number;
  availableEnergy: number;
  reliability: number;
  lastUpdate: string;
}

interface MarketStats {
  activeProviders: number;
  totalPurchases: number;
  totalCost: number;
  avgPrice: number;
  priceChange24h: number;
}

export default function EnergyMarketPage() {
  const [providers, setProviders] = useState<EnergyProvider[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [purchaseAmount, setPurchaseAmount] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const _loadData = async () => {
    try {
      setLoading(true);

      // Mock data
      const mockProviders: EnergyProvider[] = [
        {
          id: '1',
          name: 'P2P Energy Trading',
          status: 'active',
          pricePerEnergy: 0.0041,
          availableEnergy: 5000000,
          reliability: 98.5,
          lastUpdate: new Date().toISOString()
        },
        {
          id: '2',
          name: 'Energy Market Pro',
          status: 'active',
          pricePerEnergy: 0.0038,
          availableEnergy: 3500000,
          reliability: 96.8,
          lastUpdate: new Date().toISOString()
        },
        {
          id: '3',
          name: 'TronNRG',
          status: 'maintenance',
          pricePerEnergy: 0.0045,
          availableEnergy: 2000000,
          reliability: 94.2,
          lastUpdate: new Date().toISOString()
        }
      ];

      const mockStats: MarketStats = {
        activeProviders: 12,
        totalPurchases: 2450000,
        totalCost: 9875,
        avgPrice: 0.004,
        priceChange24h: -2.3
      };

      setProviders(mockProviders);
      setMarketStats(mockStats);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const _getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'inactive': return 'text-red-400';
      case 'maintenance': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const _getStatusBadge = (status: string) => {
    const _colors = {
      active: 'bg-green-900 text-green-200',
      inactive: 'bg-red-900 text-red-200',
      maintenance: 'bg-yellow-900 text-yellow-200'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-900 text-gray-200';
  };

  const _handlePurchase = () => {
    if (!selectedProvider || !purchaseAmount) {
      alert('제공업체와 구매량을 선택해주세요.');
      return;
    }
    alert(`${selectedProvider}에서 ${purchaseAmount} 에너지 구매 요청이 전송되었습니다.`);
  };

  if (loading) {
    return (
      <BasePage title="에너지 마켓" description="에너지 제공업체와 시장 현황을 관리합니다">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </BasePage>
    );
  }

  return (
    <BasePage title="에너지 마켓" description="에너지 제공업체와 시장 현황을 관리합니다">
      <div className="space-y-6">
        {/* 시장 통계 */}
        {marketStats && (
          <Section title="시장 현황">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="활성 제공업체"
                value={marketStats.activeProviders.toString()}
                icon={<Zap className="w-4 h-4" />}
                trend="up"
              />
              <StatCard
                title="총 구매량"
                value={marketStats.totalPurchases.toLocaleString()}
                icon={<TrendingUp className="w-4 h-4" />}
                trend="up"
              />
              <StatCard
                title="총 구매 비용"
                value={`$${marketStats.totalCost.toLocaleString()}`}
                icon={<DollarSign className="w-4 h-4" />}
                trend="up"
              />
              <StatCard
                title="평균 가격"
                value={`$${marketStats.avgPrice}`}
                icon={marketStats.priceChange24h > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                trend={marketStats.priceChange24h > 0 ? "up" : "down"}
                description={`24h: ${marketStats.priceChange24h}%`}
              />
            </div>
          </Section>
        )}

        {/* 에너지 구매 */}
        <Section title="에너지 구매">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <FormField
              label="제공업체 선택"
              type="text"
              value={selectedProvider}
              onChange={(value) => setSelectedProvider(value.toString())}
              placeholder="제공업체를 선택하세요"
            />
            <FormField
              label="구매량"
              type="number"
              value={purchaseAmount}
              onChange={(value) => setPurchaseAmount(typeof value === 'number' ? value : parseInt(value.toString()) || 0)}
              placeholder="구매할 에너지량"
              min={1}
            />
            <div className="flex items-end">
              <Button onClick={handlePurchase}>
                구매하기
              </Button>
            </div>
          </div>
        </Section>

        {/* 제공업체 목록 */}
        <Section title="에너지 제공업체">
          <div className="grid gap-4">
            {providers.map((provider) => (
              <div key={provider.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Zap className="w-6 h-6 text-blue-400" />
                    <div>
                      <h3 className="text-lg font-semibold">{provider.name}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(provider.status)}`}>
                        {provider.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => setSelectedProvider(provider.name)}>
                      선택
                    </Button>
                    <Button variant="secondary">
                      상세정보
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                    <p className="text-sm text-gray-400">마지막 업데이트</p>
                    <p className="text-sm">{new Date(provider.lastUpdate).toLocaleTimeString()}</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm">
                      <span className={`flex items-center gap-1 ${getStatusColor(provider.status)}`}>
                        <div className={`w-2 h-2 rounded-full ${
                          provider.status === 'active' ? 'bg-green-400' :
                          provider.status === 'maintenance' ? 'bg-yellow-400' : 'bg-red-400'
                        }`}></div>
                        {provider.status === 'active' ? '서비스 중' :
                         provider.status === 'maintenance' ? '점검 중' : '서비스 중단'}
                      </span>
                      <span className="text-gray-400">
                        신뢰도: {provider.reliability}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      업데이트: {new Date(provider.lastUpdate).toLocaleString()}
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
