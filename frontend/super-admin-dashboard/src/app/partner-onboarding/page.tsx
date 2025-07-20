'use client';

import React, { useState } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import { Badge } from '@/components/ui/Badge';
import { useI18n } from '@/contexts/I18nContext';
import { withRBAC } from '@/components/auth/withRBAC';

// 타입 정의
interface Partner {
  id: number;
  companyName: string;
  contactEmail: string;
  contactPhone: string;
  businessType: string;
  onboardingStage: 'registration' | 'kyc_pending' | 'kyc_approved' | 'contract_pending' | 'contract_signed' | 'deployment' | 'completed';
  status: 'active' | 'pending' | 'suspended' | 'rejected';
  registrationDate: string;
  riskScore: number;
}

interface OnboardingStats {
  totalPartners: number;
  pendingApproval: number;
  activePartners: number;
  completedThisMonth: number;
  averageOnboardingTime: number;
  rejectionRate: number;
}

function PartnerOnboardingPage() {
  const { t } = useI18n();
  
  const [stats] = useState<OnboardingStats>({
    totalPartners: 47,
    pendingApproval: 8,
    activePartners: 32,
    completedThisMonth: 5,
    averageOnboardingTime: 4.2,
    rejectionRate: 8.5
  });

  const [partners] = useState<Partner[]>([
    {
      id: 1,
      companyName: "CryptoTech Solutions",
      contactEmail: "admin@cryptotech.com",
      contactPhone: "+1-555-0123",
      businessType: "DeFi Platform",
      onboardingStage: "completed",
      status: "active",
      registrationDate: "2025-07-01T09:00:00Z",
      riskScore: 25
    },
    {
      id: 2,
      companyName: "BlockChain Enterprises",
      contactEmail: "contact@blockchain-ent.com",
      contactPhone: "+44-20-7946-0958",
      businessType: "Cryptocurrency Exchange",
      onboardingStage: "contract_pending",
      status: "pending",
      registrationDate: "2025-07-10T14:20:00Z",
      riskScore: 45
    },
    {
      id: 3,
      companyName: "FinTech Innovations",
      contactEmail: "support@fintech-innov.com",
      contactPhone: "+81-3-1234-5678",
      businessType: "Payment Gateway",
      onboardingStage: "kyc_pending",
      status: "pending",
      registrationDate: "2025-07-15T11:30:00Z",
      riskScore: 35
    }
  ]);

  const handleAdvanceStage = (partnerId: number) => {
    console.log('Advancing stage for partner:', partnerId);
    // API 호출 로직
  };

  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'completed': return 'success';
      case 'contract_signed': 
      case 'deployment': return 'primary';
      case 'kyc_approved':
      case 'contract_pending': return 'warning';
      default: return 'secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'pending': return 'warning';
      case 'suspended': return 'danger';
      case 'rejected': return 'danger';
      default: return 'secondary';
    }
  };

  const handleNewPartnerRegistration = () => {
    // 실제로는 모달을 열거나 새 페이지로 이동
    alert('신규 파트너 등록 양식을 여기에 구현할 예정입니다.\n\n포함 사항:\n- 회사 정보\n- 사업자 등록증\n- 담당자 연락처\n- 사업 유형\n- KYC 문서');
  };

  const headerActions = (
    <Button variant="primary" onClick={handleNewPartnerRegistration}>
      새 파트너 등록
    </Button>
  );

  return (
    <BasePage 
      title={t.partnerOnboarding?.title || "파트너 온보딩 관리"}
      description={t.partnerOnboarding?.description || "파트너사의 온보딩 프로세스를 관리하고 모니터링합니다"}
      headerActions={headerActions}
    >
      {/* 통계 현황 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        <StatCard
          title="전체 파트너"
          value={stats.totalPartners.toString()}
          icon="🏢"
          description="등록된 파트너"
        />
        <StatCard
          title="승인 대기"
          value={stats.pendingApproval.toString()}
          icon="⏳"
          description="검토 필요"
        />
        <StatCard
          title="활성 파트너"
          value={stats.activePartners.toString()}
          icon="✅"
          description="운영중"
        />
        <StatCard
          title="이번 달 완료"
          value={stats.completedThisMonth.toString()}
          icon="📈"
          description="온보딩 완료"
        />
        <StatCard
          title="평균 처리 시간"
          value={`${stats.averageOnboardingTime}일`}
          icon="⏱️"
          description="온보딩 기간"
        />
        <StatCard
          title="거부율"
          value={`${stats.rejectionRate}%`}
          icon="📊"
          description="심사 거부율"
        />
      </div>

      {/* 파트너 목록 */}
      <Section title="파트너 온보딩 현황">
        <div className="overflow-hidden shadow ring-1 ring-gray-700 rounded-lg">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  회사명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  연락처
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  온보딩 단계
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  리스크 점수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  등록일
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  액션
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-900 divide-y divide-gray-700">
              {partners.map((partner) => (
                <tr key={partner.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-white">
                        {partner.companyName}
                      </div>
                      <div className="text-sm text-gray-300">
                        {partner.businessType}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-100">{partner.contactEmail}</div>
                    <div className="text-sm text-gray-300">{partner.contactPhone}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      getStageColor(partner.onboardingStage) === 'success' ? 'bg-green-900/30 text-green-300' :
                      getStageColor(partner.onboardingStage) === 'primary' ? 'bg-blue-900/30 text-blue-300' :
                      getStageColor(partner.onboardingStage) === 'warning' ? 'bg-yellow-900/30 text-yellow-300' :
                      'bg-gray-900/30 text-gray-300'
                    }`}>
                      {partner.onboardingStage}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      getStatusColor(partner.status) === 'success' ? 'bg-green-900/30 text-green-300' :
                      getStatusColor(partner.status) === 'warning' ? 'bg-yellow-900/30 text-yellow-300' :
                      getStatusColor(partner.status) === 'danger' ? 'bg-red-900/30 text-red-300' :
                      'bg-gray-900/30 text-gray-300'
                    }`}>
                      {partner.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm text-gray-100">{partner.riskScore}</span>
                      <div className="ml-2 w-16 bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            partner.riskScore <= 30 ? 'bg-green-600' :
                            partner.riskScore <= 60 ? 'bg-yellow-600' : 'bg-red-600'
                          }`}
                          style={{ width: `${partner.riskScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {new Date(partner.registrationDate).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Button 
                      variant="secondary" 
                      onClick={() => handleAdvanceStage(partner.id)}
                      className="mr-2"
                    >
                      단계 진행
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </BasePage>
  );
}

// Export protected component
export default withRBAC(PartnerOnboardingPage, { 
  requiredPermissions: ['partners.view', 'partners.create']
});
