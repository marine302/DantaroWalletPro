"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import BasePage from '@/components/ui/BasePage';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Table from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { apiClient } from '@/lib/api';

// 타입 정의
interface PartnerEnergyAllocation {
  id: number;
  partner_id: string;
  partner_name: string;
  partner_tier: 'STARTUP' | 'BUSINESS' | 'ENTERPRISE';
  allocated_amount: number;
  remaining_amount: number;
  us_ed_amount: number;
  purchas_e_price: number;
  markup_percentage: number;
  rental_price: number;
  billing_cycle: string;
  s_tatus: 'ACTIVE' | 'SUSPENDED' | 'EXPIRED' | 'CANCELLED';
  allocation_date: string;
  expiry_date?: string;
  utilization_rate: number;
  total_revenue: number;
  notes?: string;
}

interface RevenueAnalytics {
  total_revenue: number;
  total_margin: number;
  total_us_age: number;
  partner_count: number;
  avg_margin_rate: number;
  top_partners: Array<{
    partner_id: string;
    partner_name: string;
    revenue: number;
    us_age: number;
  }>;
  revenue_by_tier: Record<string, number>;
}

interface EnergyMarginConfig {
  id: number;
  partner_tier: string;
  default_margin_percentage: number;
  min_margin_percentage: number;
  max_margin_percentage: number;
  volume_thres_hold_1: number;
  volume_margin_1: number;
  volume_thres_hold_2: number;
  volume_margin_2: number;
}

export default function PartnerEnergyManagementPage() {
  const { locale: _language } = useI18n();
  const [loading, setLoading] = useState(true);
  const [allocations] = useState<PartnerEnergyAllocation[]>([]);
  const [analytics, setAnalytics] = useState<RevenueAnalytics | null>(null);
  const [marginConfigs, setMarginConfigs] = useState<EnergyMarginConfig[]>([]);
  const [selectedPartner, setSelectedPartner] = useState<string>('all');
  const [showAllocationModal, setShowAllocationModal] = useState(false);

  // 데이터 로딩
  useEffect(() => {
    loadData();
  }, []);

  const _loadData = async () => {
    try {
      setLoading(true);

      // 수익 분석 데이터 로딩
      const _analyticsResponse = await apiClient.get('/admin/energy/revenue-analytics');
      setAnalytics(analyticsResponse.data);

      // 마진 설정 로딩
      const _marginResponse = await apiClient.get('/admin/energy/margin-config');
      setMarginConfigs(marginResponse.data);

      // 파트너별 할당 데이터 로딩 (전체 파트너)
      // TODO: 전체 파트너 할당 조회 API 필요

    } catch (error) {
      console.error('데이터 로딩 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  // 상태 뱃지 렌더링
  const _renderStatusBadge = (_status: string) => {
    const _statusConfig: Record<string, { color: string; text: string }> = {
      ACTIVE: { color: 'green', text: '활성' },
      SUSPENDED: { color: 'yellow', text: '중단' },
      EXPIRED: { color: 'red', text: '만료' },
      CANCELLED: { color: 'gray', text: '취소' }
    };

    const _config = _statusConfig[_status];
    return <Badge variant={_config?.color as 'green' | 'yellow' | 'red' | 'gray'}>{_config?.text || _status}</Badge>;
  };

  // 파트너 등급 뱃지 렌더링
  const _renderTierBadge = (_tier: string) => {
    const tierConfig: Record<string, { color: string; text: string }> = {
      STARTUP: { color: 'blue', text: '스타트업' },
      BUSINESS: { color: 'purple', text: '중소기업' },
      ENTERPRISE: { color: 'orange', text: '대기업' }
    };

    const _config = tierConfig[tier];
    return <Badge variant={config?.color as 'blue' | 'purple' | 'orange'}>{config?.text || tier}</Badge>;
  };

  // 숫자 포맷팅
  const _formatNumber = (_num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num);
  };

  // 통화 포맷팅
  const _formatCurrency = (_amount: number) => {
    return `${amount.toFixed(6)} TRX`;
  };

  // 할당 테이블 컬럼 정의
  const _allocationColumns = [
    {
      key: 'partner_name',
      label: '파트너명',
      render: (_allocation: PartnerEnergyAllocation) => (
        <div>
          <div className="font-medium">{allocation.partner_name}</div>
          <div className="text-sm text-gray-500">{allocation.partner_id}</div>
        </div>
      )
    },
    {
      key: 'partner_tier',
      label: '등급',
      render: (_allocation: PartnerEnergyAllocation) => renderTierBadge(allocation.partner_tier)
    },
    {
      key: 'allocated_amount',
      label: '할당량',
      render: (_allocation: PartnerEnergyAllocation) => (
        <div>
          <div>{formatNumber(allocation.allocated_amount)} Energy</div>
          <div className="text-sm text-gray-500">
            사용률: {allocation.utilization_rate.toFixed(1)}%
          </div>
        </div>
      )
    },
    {
      key: 'pricing',
      label: '가격 정보',
      render: (_allocation: PartnerEnergyAllocation) => (
        <div>
          <div>구매가: {formatCurrency(allocation.purchase_price)}</div>
          <div>렌탈가: {formatCurrency(allocation.rental_price)}</div>
          <div className="text-sm text-green-600">
            마진: {allocation.markup_percentage.toFixed(1)}%
          </div>
        </div>
      )
    },
    {
      key: 'revenue',
      label: '수익',
      render: (_allocation: PartnerEnergyAllocation) => (
        <div className="text-right">
          <div className="font-medium text-green-600">
            {formatCurrency(allocation.total_revenue)}
          </div>
          <div className="text-sm text-gray-500">
            사용량: {formatNumber(allocation.used_amount)}
          </div>
        </div>
      )
    },
    {
      key: 'status',
      label: '상태',
      render: (_allocation: PartnerEnergyAllocation) => renderStatusBadge(allocation.status)
    }
  ];

  return (
    <BasePage
      title="파트너 에너지 관리"
      subtitle="파트너사별 에너지 할당 및 수익 관리"
    >
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="space-y-6">

          {/* 수익 분석 대시보드 */}
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-2">총 수익</h3>
                  <p className="text-3xl font-bold text-green-600">
                    {formatCurrency(analytics.total_revenue)}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    총 {formatNumber(analytics.total_usage)} Energy 사용
                  </p>
                </div>
              </Card>

              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-2">활성 파트너</h3>
                  <p className="text-3xl font-bold text-blue-600">
                    {analytics.partner_count}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    평균 마진: {analytics.avg_margin_rate.toFixed(1)}%
                  </p>
                </div>
              </Card>

              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-2">등급별 수익</h3>
                  <div className="space-y-1">
                    {Object.entries(analytics.revenue_by_tier).map(([tier, revenue]) => (
                      <div key={tier} className="flex justify-between text-sm">
                        <span>{tier}:</span>
                        <span className="font-medium">{formatCurrency(revenue)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>

              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-2">상위 파트너</h3>
                  <div className="space-y-1">
                    {analytics.top_partners.slice(0, 3).map((partner) => (
                      <div key={partner.partner_id} className="flex justify-between text-sm">
                        <span className="truncate">{partner.partner_name}</span>
                        <span className="font-medium">{formatCurrency(partner.revenue)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* 마진 설정 현황 */}
          <Card>
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">마진 설정 현황</h3>
                <Button variant="outline" size="sm">
                  설정 변경
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {marginConfigs.map((config) => (
                  <div key={config.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{config.partner_tier}</h4>
                      <span className="text-sm text-green-600 font-medium">
                        {config.default_margin_percentage}%
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 space-y-1">
                      <div>최소: {config.min_margin_percentage}%</div>
                      <div>최대: {config.max_margin_percentage}%</div>
                      <div>
                        볼륨 할인: {formatNumber(config.volume_threshold_1)} 이상 -{config.volume_margin_1}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* 에너지 할당 관리 */}
          <Card>
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">에너지 할당 현황</h3>
                <div className="flex gap-2">
                  <select
                    value={selectedPartner}
                    onChange={(e) => setSelectedPartner(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="all">전체 파트너</option>
                    {/* TODO: 파트너 목록 옵션 추가 */}
                  </select>
                  <Button onClick={() => setShowAllocationModal(true)}>
                    새 할당 생성
                  </Button>
                </div>
              </div>

              <Table
                columns={allocationColumns}
                data={allocations}
                emptyMessage="할당된 에너지가 없습니다."
              />
            </div>
          </Card>

          {/* TODO: 새 할당 생성 모달 */}
          {showAllocationModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 className="text-lg font-semibold mb-4">새 에너지 할당</h3>
                <div className="space-y-4">
                  {/* TODO: 할당 생성 폼 구현 */}
                  <p className="text-gray-500">할당 생성 폼을 구현해야 합니다.</p>
                </div>
                <div className="flex justify-end gap-2 mt-6">
                  <Button
                    variant="outline"
                    onClick={() => setShowAllocationModal(false)}
                  >
                    취소
                  </Button>
                  <Button onClick={() => setShowAllocationModal(false)}>
                    생성
                  </Button>
                </div>
              </div>
            </div>
          )}

        </div>
      )}
    </BasePage>
  );
}
