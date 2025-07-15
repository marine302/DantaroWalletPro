'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

// 타입 정의
interface Partner {
  id: number;
  companyName: string;
  contactEmail: string;
  contactPhone: string;
  website: string;
  country: string;
  businessType: string;
  apiKeyId: string;
  onboardingStage: 'registration' | 'kyc_pending' | 'kyc_approved' | 'contract_pending' | 'contract_signed' | 'deployment' | 'completed';
  status: 'active' | 'pending' | 'suspended' | 'rejected';
  registrationDate: string;
  completionDate?: string;
  monthlyVolume: number;
  riskScore: number;
  kycStatus: 'pending' | 'approved' | 'rejected' | 'not_started';
  contractStatus: 'pending' | 'signed' | 'rejected' | 'not_started';
  deploymentStatus: 'pending' | 'deployed' | 'failed' | 'not_started';
}

interface OnboardingStats {
  totalPartners: number;
  pendingApproval: number;
  activePartners: number;
  completedThisMonth: number;
  averageOnboardingTime: number;
  rejectionRate: number;
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

export default function PartnerOnboardingPage() {
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
      website: "https://cryptotech.com",
      country: "United States",
      businessType: "DeFi Platform",
      apiKeyId: "ct_live_abc123xyz",
      onboardingStage: "completed",
      status: "active",
      registrationDate: "2025-07-01T09:00:00Z",
      completionDate: "2025-07-05T16:30:00Z",
      monthlyVolume: 250000,
      riskScore: 25,
      kycStatus: "approved",
      contractStatus: "signed",
      deploymentStatus: "deployed"
    },
    {
      id: 2,
      companyName: "BlockChain Enterprises",
      contactEmail: "contact@blockchain-ent.com",
      contactPhone: "+44-20-7946-0958",
      website: "https://blockchain-ent.com",
      country: "United Kingdom",
      businessType: "Cryptocurrency Exchange",
      apiKeyId: "be_test_def456uvw",
      onboardingStage: "contract_pending",
      status: "pending",
      registrationDate: "2025-07-10T14:20:00Z",
      monthlyVolume: 0,
      riskScore: 45,
      kycStatus: "approved",
      contractStatus: "pending",
      deploymentStatus: "not_started"
    },
    {
      id: 3,
      companyName: "FinTech Innovations",
      contactEmail: "support@fintech-innov.com",
      contactPhone: "+81-3-1234-5678",
      website: "https://fintech-innov.com",
      country: "Japan",
      businessType: "Payment Processor",
      apiKeyId: "fi_test_ghi789rst",
      onboardingStage: "kyc_pending",
      status: "pending",
      registrationDate: "2025-07-12T11:45:00Z",
      monthlyVolume: 0,
      riskScore: 32,
      kycStatus: "pending",
      contractStatus: "not_started",
      deploymentStatus: "not_started"
    },
    {
      id: 4,
      companyName: "Digital Asset Management",
      contactEmail: "info@dam-crypto.com",
      contactPhone: "+49-30-12345678",
      website: "https://dam-crypto.com",
      country: "Germany",
      businessType: "Asset Management",
      apiKeyId: "dam_test_jkl012mno",
      onboardingStage: "deployment",
      status: "pending",
      registrationDate: "2025-07-08T08:15:00Z",
      monthlyVolume: 0,
      riskScore: 18,
      kycStatus: "approved",
      contractStatus: "signed",
      deploymentStatus: "pending"
    }
  ]);

  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'deployment': return 'bg-blue-100 text-blue-800';
      case 'contract_signed': return 'bg-purple-100 text-purple-800';
      case 'contract_pending': return 'bg-yellow-100 text-yellow-800';
      case 'kyc_approved': return 'bg-indigo-100 text-indigo-800';
      case 'kyc_pending': return 'bg-orange-100 text-orange-800';
      case 'registration': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'suspended': return 'bg-red-100 text-red-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskColor = (score: number) => {
    if (score <= 30) return 'bg-green-100 text-green-800';
    if (score <= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getRiskLevel = (score: number) => {
    if (score <= 30) return 'Low';
    if (score <= 60) return 'Medium';
    return 'High';
  };

  const getStageLabel = (stage: string) => {
    switch (stage) {
      case 'registration': return '등록 완료';
      case 'kyc_pending': return 'KYC 검토중';
      case 'kyc_approved': return 'KYC 승인';
      case 'contract_pending': return '계약서 검토중';
      case 'contract_signed': return '계약서 체결';
      case 'deployment': return '시스템 배포중';
      case 'completed': return '온보딩 완료';
      default: return stage;
    }
  };

  const formatCurrency = (amount: number) => `$${amount.toLocaleString()}`;
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString();

  const filteredPartners = partners.filter(partner => {
    const matchesStatus = filterStatus === 'all' || partner.status === filterStatus;
    const matchesSearch = partner.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         partner.contactEmail.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleApprove = (partnerId: number) => {
    console.log('Approving partner:', partnerId);
    // API 호출 로직
  };

  const handleReject = (partnerId: number) => {
    console.log('Rejecting partner:', partnerId);
    // API 호출 로직
  };

  const handleAdvanceStage = (partnerId: number) => {
    console.log('Advancing stage for partner:', partnerId);
    // API 호출 로직
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">파트너 온보딩 관리</h1>
        <Button>
          새 파트너 등록
        </Button>
      </div>

      {/* 통계 현황 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 파트너</CardTitle>
            <span className="text-2xl">🏢</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalPartners}</div>
            <p className="text-xs text-gray-500">등록된 파트너</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">승인 대기</CardTitle>
            <span className="text-2xl">⏳</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pendingApproval}</div>
            <p className="text-xs text-gray-500">검토 필요</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">활성 파트너</CardTitle>
            <span className="text-2xl">✅</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activePartners}</div>
            <p className="text-xs text-gray-500">운영중</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이번 달 완료</CardTitle>
            <span className="text-2xl">📈</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completedThisMonth}</div>
            <p className="text-xs text-gray-500">신규 완료</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 소요시간</CardTitle>
            <span className="text-2xl">⏱️</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.averageOnboardingTime}일</div>
            <p className="text-xs text-gray-500">온보딩 완료까지</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">거절률</CardTitle>
            <span className="text-2xl">❌</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.rejectionRate}%</div>
            <p className="text-xs text-gray-500">지난 30일</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="partners" className="space-y-4">
        <TabsList>
          <TabsTrigger value="partners">파트너 목록</TabsTrigger>
          <TabsTrigger value="pipeline">온보딩 파이프라인</TabsTrigger>
          <TabsTrigger value="settings">온보딩 설정</TabsTrigger>
        </TabsList>

        <TabsContent value="partners">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>파트너 목록</CardTitle>
                <div className="flex gap-4">
                  <Input
                    placeholder="회사명 또는 이메일 검색..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-64"
                  />
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="상태 필터" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">전체</SelectItem>
                      <SelectItem value="active">활성</SelectItem>
                      <SelectItem value="pending">대기중</SelectItem>
                      <SelectItem value="suspended">중단</SelectItem>
                      <SelectItem value="rejected">거절</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredPartners.map((partner) => (
                  <div key={partner.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-lg font-semibold">{partner.companyName}</h3>
                        <p className="text-sm text-gray-500">{partner.contactEmail}</p>
                        <p className="text-sm text-gray-500">{partner.country} • {partner.businessType}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge className={getStageColor(partner.onboardingStage)}>
                          {getStageLabel(partner.onboardingStage)}
                        </Badge>
                        <Badge className={getStatusColor(partner.status)}>
                          {partner.status}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm font-medium text-gray-500">등록일</p>
                        <p className="text-sm">{formatDate(partner.registrationDate)}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">월 거래량</p>
                        <p className="text-sm">{formatCurrency(partner.monthlyVolume)}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">리스크 스코어</p>
                        <div className="flex items-center gap-2">
                          <Badge className={getRiskColor(partner.riskScore)}>
                            {getRiskLevel(partner.riskScore)}
                          </Badge>
                          <span className="text-sm text-gray-500">({partner.riskScore})</span>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">API 키</p>
                        <p className="text-sm font-mono">{partner.apiKeyId}</p>
                      </div>
                    </div>

                    {/* 진행상황 표시 */}
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-500 mb-2">온보딩 진행상황</p>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">KYC:</span>
                          <Badge className={getStatusColor(partner.kycStatus === 'approved' ? 'active' : partner.kycStatus === 'rejected' ? 'rejected' : 'pending')}>
                            {partner.kycStatus}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">계약:</span>
                          <Badge className={getStatusColor(partner.contractStatus === 'signed' ? 'active' : partner.contractStatus === 'rejected' ? 'rejected' : 'pending')}>
                            {partner.contractStatus}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">배포:</span>
                          <Badge className={getStatusColor(partner.deploymentStatus === 'deployed' ? 'active' : partner.deploymentStatus === 'failed' ? 'rejected' : 'pending')}>
                            {partner.deploymentStatus}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* 액션 버튼 */}
                    <div className="flex gap-2">
                      {partner.status === 'pending' && (
                        <>
                          <Button size="sm" onClick={() => handleApprove(partner.id)}>
                            승인
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleReject(partner.id)}>
                            거절
                          </Button>
                        </>
                      )}
                      {partner.onboardingStage !== 'completed' && (
                        <Button size="sm" variant="outline" onClick={() => handleAdvanceStage(partner.id)}>
                          다음 단계
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        상세 보기
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pipeline">
          <Card>
            <CardHeader>
              <CardTitle>온보딩 파이프라인</CardTitle>
              <p className="text-sm text-gray-500">
                각 단계별 파트너 현황을 확인할 수 있습니다.
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { stage: 'registration', label: '등록 완료', count: 2 },
                  { stage: 'kyc_pending', label: 'KYC 검토중', count: 3 },
                  { stage: 'contract_pending', label: '계약서 검토중', count: 1 },
                  { stage: 'deployment', label: '시스템 배포중', count: 2 }
                ].map((item) => (
                  <Card key={item.stage}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">{item.label}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{item.count}</div>
                      <p className="text-xs text-gray-500">파트너</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>온보딩 설정</CardTitle>
              <p className="text-sm text-gray-500">
                자동화 규칙과 승인 기준을 설정할 수 있습니다.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">자동 KYC 승인</h4>
                  <p className="text-sm text-gray-500">낮은 리스크 파트너의 KYC를 자동으로 승인합니다.</p>
                </div>
                <Button variant="outline">활성화</Button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">계약서 자동 생성</h4>
                  <p className="text-sm text-gray-500">KYC 승인 시 계약서를 자동으로 생성합니다.</p>
                </div>
                <Button variant="outline">활성화</Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">최대 리스크 스코어</label>
                  <Input type="number" defaultValue="30" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">최소 월 거래량 ($)</label>
                  <Input type="number" defaultValue="10000" />
                </div>
              </div>

              <Button className="w-full">설정 저장</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
