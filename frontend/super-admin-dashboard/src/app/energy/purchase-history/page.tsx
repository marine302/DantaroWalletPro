'use client';

import { useState, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import BasePage from "@/components/ui/BasePage";
import { Section, StatCard, Button, FormField } from '@/components/ui/DarkThemeComponents';
import { Download, RefreshCw } from 'lucide-react';

interface PurchaseHistory {
  id: string;
  timestamp: string;
  provider: string;
  amount: number;
  pricePerEnergy: number;
  totalCost: number;
  status: 'completed' | 'pending' | 'failed' | 'cancelled';
  type: 'auto' | 'manual';
  urgency: 'normal' | 'high' | 'emergency';
  approvedBy?: string;
  deliveryTime?: string;
  transactionHash?: string;
}

export default function PurchaseHistoryPage() {
  const { locale: _language } = useI18n();
  const [filteredPurchases, setFilteredPurchases] = useState<PurchaseHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const mockPurchases: PurchaseHistory[] = [
      {
        id: '1',
        timestamp: '2024-01-15T10:30:00Z',
        provider: 'P2P Energy Trading',
        amount: 1000000,
        pricePerEnergy: 0.0041,
        totalCost: 4100,
        status: 'completed',
        type: 'auto',
        urgency: 'high',
        approvedBy: 'System Auto',
        deliveryTime: '2 minutes',
        transactionHash: '0x1234...abcd'
      },
      {
        id: '2',
        timestamp: '2024-01-15T09:15:00Z',
        provider: 'Energy Market Pro',
        amount: 750000,
        pricePerEnergy: 0.0038,
        totalCost: 2850,
        status: 'completed',
        type: 'manual',
        urgency: 'normal',
        approvedBy: 'Admin User',
        deliveryTime: '5 minutes',
        transactionHash: '0x5678...efgh'
      }
    ];

    setFilteredPurchases(mockPurchases);
    setFilteredPurchases(mockPurchases);
    setIsLoading(false);
  }, []);

  const _getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'pending': return 'text-yellow-400';
      case 'failed': return 'text-red-400';
      case 'cancelled': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  const _getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'emergency': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'normal': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  if (isLoading) {
    return (
      <BasePage title="에너지 구매 내역" description="에너지 구매 기록을 확인하고 관리합니다">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </BasePage>
    );
  }

  return (
    <BasePage title="에너지 구매 내역" description="에너지 구매 기록을 확인하고 관리합니다">
      <div className="space-y-6">
        {/* 통계 요약 */}
        <Section title="구매 통계">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="총 구매량"
              value="1,750,000"
              trend="up"
            />
            <StatCard
              title="총 구매 비용"
              value="$6,950"
              trend="up"
            />
            <StatCard
              title="평균 단가"
              value="$0.0040"
              trend="neutral"
            />
            <StatCard
              title="성공률"
              value="98.5%"
              trend="up"
            />
          </div>
        </Section>

        {/* 필터 및 검색 */}
        <Section title="필터 및 검색">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <FormField
              label="검색"
              type="text"
              value={searchTerm}
              onChange={(value) => setSearchTerm(value.toString())}
              placeholder="거래 ID, 제공업체 검색..."
            />
            <div className="flex gap-2 mt-4">
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                새로고침
              </Button>
              <Button>
                <Download className="w-4 h-4 mr-2" />
                내역 다운로드
              </Button>
            </div>
          </div>
        </Section>

        {/* 구매 내역 목록 */}
        <Section title="구매 내역">
          <div className="space-y-4">
            {filteredPurchases.map((purchase) => (
              <div key={purchase.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">거래 ID</p>
                    <p className="font-medium">{purchase.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">제공업체</p>
                    <p className="font-medium">{purchase.provider}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">구매량</p>
                    <p className="font-medium">{purchase.amount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">총 비용</p>
                    <p className="font-medium">${purchase.totalCost.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">상태</p>
                    <p className={`font-medium ${getStatusColor(purchase.status)}`}>
                      {purchase.status}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">긴급도</p>
                    <p className={`font-medium ${getUrgencyColor(purchase.urgency)}`}>
                      {purchase.urgency}
                    </p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">시간: </span>
                      <span>{new Date(purchase.timestamp).toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">단가: </span>
                      <span>${purchase.pricePerEnergy}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">유형: </span>
                      <span>{purchase.type}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">승인자: </span>
                      <span>{purchase.approvedBy || 'N/A'}</span>
                    </div>
                  </div>
                  {purchase.transactionHash && (
                    <div className="mt-2">
                      <span className="text-gray-400">트랜잭션 해시: </span>
                      <span className="font-mono text-sm">{purchase.transactionHash}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
