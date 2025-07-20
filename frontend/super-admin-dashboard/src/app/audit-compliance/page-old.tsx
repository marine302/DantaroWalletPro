'use client';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  Activity,
  AlertTriangle,
  Bell,
  Download,
  FileText,
  RefreshCw,
  Shield,
  TrendingUp
} from 'lucide-react';
import React, { useEffect, useState } from 'react';

// 간단한 Tabs 컴포넌트 구현
const Tabs = ({ defaultValue, className, children }: { defaultValue: string; className?: string; children: React.ReactNode }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);

  const childrenWithProps = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (tab: string) => void }>, {
        activeTab,
        setActiveTab
      });
    }
    return child;
  });

  return <div className={className}>{childrenWithProps}</div>;
};

const TabsList = ({ children, activeTab, setActiveTab }: { children: React.ReactNode; activeTab?: string; setActiveTab?: (tab: string) => void }) => {
  const childrenWithProps = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (tab: string) => void }>, {
        activeTab,
        setActiveTab
      });
    }
    return child;
  });

  return (
    <div className="flex space-x-1 rounded-lg bg-muted p-1 mb-4">
      {childrenWithProps}
    </div>
  );
};

const TabsTrigger = ({ value, children, activeTab, setActiveTab }: { value: string; children: React.ReactNode; activeTab?: string; setActiveTab?: (tab: string) => void }) => (
  <button
    className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === value ? 'bg-background shadow-sm' : 'hover:bg-background/60'
      }`}
    onClick={() => setActiveTab?.(value)}
  >
    {children}
  </button>
);

const TabsContent = ({ value, children, activeTab }: { value: string; children: React.ReactNode; activeTab?: string }) =>
  activeTab === value ? <div className="space-y-4">{children}</div> : null;

// 간단한 CardDescription 컴포넌트
const CardDescription = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <p className={`text-sm text-muted-foreground ${className}`}>{children}</p>
);

// 간단한 Input 컴포넌트
const Input = ({ placeholder, value, onChange, className }: {
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string
}) => (
  <input
    type="text"
    placeholder={placeholder}
    value={value}
    onChange={onChange}
    className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
  />
);

// 간단한 Select 컴포넌트
const Select = ({ value, onValueChange, children }: { value: string; onValueChange: (value: string) => void; children: React.ReactNode }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      {React.Children.map(children, child =>
        React.isValidElement(child) ? React.cloneElement(child as React.ReactElement<{ value?: string; onValueChange?: (value: string) => void; isOpen?: boolean; setIsOpen?: (open: boolean) => void }>, { value, onValueChange, isOpen, setIsOpen }) : child
      )}
    </div>
  );
};

const SelectTrigger = ({ className, children, isOpen, setIsOpen }: { className?: string; children: React.ReactNode; isOpen?: boolean; setIsOpen?: (open: boolean) => void }) => (
  <button
    className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    onClick={() => setIsOpen?.(!isOpen)}
  >
    {children}
  </button>
);

const SelectValue = ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>;

const SelectContent = ({ children, isOpen, onValueChange, setIsOpen }: {
  children: React.ReactNode;
  isOpen?: boolean;
  onValueChange?: (value: string) => void;
  setIsOpen?: (open: boolean) => void
}) =>
  isOpen ? (
    <div className="absolute z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md">
      {React.Children.map(children, child =>
        React.isValidElement(child) ? React.cloneElement(child as React.ReactElement<{ onValueChange?: (value: string) => void; setIsOpen?: (open: boolean) => void }>, { onValueChange, setIsOpen }) : child
      )}
    </div>
  ) : null;

const SelectItem = ({ value, children, onValueChange, setIsOpen }: {
  value: string;
  children: React.ReactNode;
  onValueChange?: (value: string) => void;
  setIsOpen?: (open: boolean) => void
}) => (
  <button
    className="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
    onClick={() => {
      onValueChange?.(value);
      setIsOpen?.(false);
    }}
  >
    {children}
  </button>
);

// 타입 정의
interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  user_id?: string;
  partner_id?: string;
  transaction_id?: string;
  description: string;
  risk_score: number;
  status: 'normal' | 'warning' | 'critical';
  metadata: Record<string, unknown>;
}

interface SuspiciousActivity {
  id: string;
  detected_at: string;
  activity_type: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  user_id: string;
  transaction_amount: number;
  status: 'pending' | 'investigating' | 'resolved' | 'false_positive';
}

interface ComplianceMetrics {
  total_transactions: number;
  flagged_transactions: number;
  compliance_rate: number;
  aml_checks_passed: number;
  kyc_verifications: number;
  suspicious_activities: number;
}

const AuditCompliancePage = () => {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [suspiciousActivities, setSuspiciousActivities] = useState<SuspiciousActivity[]>([]);
  const [metrics, setMetrics] = useState<ComplianceMetrics>({
    total_transactions: 0,
    flagged_transactions: 0,
    compliance_rate: 0,
    aml_checks_passed: 0,
    kyc_verifications: 0,
    suspicious_activities: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [riskLevelFilter, setRiskLevelFilter] = useState('all');

  // 모의 데이터 로드
  useEffect(() => {
    const loadMockData = () => {
      setIsLoading(true);

      // 감사 이벤트 모의 데이터
      const mockAuditEvents: AuditEvent[] = [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          event_type: 'TRANSACTION_COMPLETED',
          user_id: 'user_123',
          partner_id: 'partner_1',
          transaction_id: 'tx_456',
          description: 'Large transaction completed successfully',
          risk_score: 2.5,
          status: 'normal',
          metadata: { amount: 50000, currency: 'TRX' }
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          event_type: 'SUSPICIOUS_ACTIVITY',
          user_id: 'user_789',
          description: 'Unusual transaction pattern detected',
          risk_score: 8.5,
          status: 'critical',
          metadata: { pattern: 'rapid_succession', count: 15 }
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 600000).toISOString(),
          event_type: 'COMPLIANCE_CHECK',
          user_id: 'user_456',
          description: 'AML check passed for user verification',
          risk_score: 1.0,
          status: 'normal',
          metadata: { check_type: 'aml', result: 'passed' }
        }
      ];

      // 의심스러운 활동 모의 데이터
      const mockSuspiciousActivities: SuspiciousActivity[] = [
        {
          id: 'sa_1',
          detected_at: new Date().toISOString(),
          activity_type: 'STRUCTURING',
          risk_level: 'high',
          description: 'Multiple transactions just below reporting threshold',
          user_id: 'user_suspicious_1',
          transaction_amount: 9800,
          status: 'investigating'
        },
        {
          id: 'sa_2',
          detected_at: new Date(Date.now() - 1800000).toISOString(),
          activity_type: 'UNUSUAL_PATTERN',
          risk_level: 'medium',
          description: 'Rapid succession of transactions from new account',
          user_id: 'user_suspicious_2',
          transaction_amount: 25000,
          status: 'pending'
        }
      ];

      // 컴플라이언스 메트릭 모의 데이터
      const mockMetrics: ComplianceMetrics = {
        total_transactions: 15420,
        flagged_transactions: 127,
        compliance_rate: 99.2,
        aml_checks_passed: 847,
        kyc_verifications: 1205,
        suspicious_activities: 23
      };

      setAuditEvents(mockAuditEvents);
      setSuspiciousActivities(mockSuspiciousActivities);
      setMetrics(mockMetrics);
      setIsLoading(false);
    };

    loadMockData();
  }, []);

  // 실제 API 호출 함수들 (추후 구현)
  const fetchAuditEvents = async () => {
    try {
      // const response = await fetch('/api/v1/audit-compliance/events');
      // const data = await response.json();
      // setAuditEvents(data);
    } catch (error) {
      console.error('Failed to fetch audit events:', error);
    }
  };

  const fetchSuspiciousActivities = async () => {
    try {
      // const response = await fetch('/api/v1/audit-compliance/suspicious-activities');
      // const data = await response.json();
      // setSuspiciousActivities(data);
    } catch (error) {
      console.error('Failed to fetch suspicious activities:', error);
    }
  };

  const fetchComplianceMetrics = async () => {
    try {
      // const response = await fetch('/api/v1/audit-compliance/metrics');
      // const data = await response.json();
      // setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch compliance metrics:', error);
    }
  };

  // 필터링된 감사 이벤트
  const filteredAuditEvents = auditEvents.filter(event => {
    const matchesSearch = searchTerm === '' ||
      event.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.event_type.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesEventType = eventTypeFilter === 'all' || event.event_type === eventTypeFilter;

    return matchesSearch && matchesEventType;
  });

  // 필터링된 의심스러운 활동
  const filteredSuspiciousActivities = suspiciousActivities.filter(activity => {
    const matchesRiskLevel = riskLevelFilter === 'all' || activity.risk_level === riskLevelFilter;
    return matchesRiskLevel;
  });

  // 상태별 색상 매핑
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'bg-blue-100 text-blue-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">감사 및 컴플라이언스</h1>
          <p className="text-muted-foreground">
            실시간 트랜잭션 모니터링 및 규제 준수 관리
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              fetchAuditEvents();
              fetchSuspiciousActivities();
              fetchComplianceMetrics();
            }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            새로고침
          </Button>
          <Button>
            <Download className="w-4 h-4 mr-2" />
            보고서 다운로드
          </Button>
        </div>
      </div>

      {/* 메트릭 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 트랜잭션</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_transactions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline w-3 h-3 mr-1" />
              지난 24시간
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">컴플라이언스 율</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.compliance_rate}%</div>
            <p className="text-xs text-muted-foreground">
              규제 준수 비율
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">플래그된 트랜잭션</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.flagged_transactions}</div>
            <p className="text-xs text-muted-foreground">
              검토 필요 거래
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">의심스러운 활동</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.suspicious_activities}</div>
            <p className="text-xs text-muted-foreground">
              조사 중인 케이스
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 메인 탭 컨텐츠 */}
      <Tabs defaultValue="audit-log" className="space-y-4">
        <TabsList>
          <TabsTrigger value="audit-log">감사 로그</TabsTrigger>
          <TabsTrigger value="suspicious">의심스러운 활동</TabsTrigger>
          <TabsTrigger value="compliance">컴플라이언스 체크</TabsTrigger>
          <TabsTrigger value="reports">보고서</TabsTrigger>
        </TabsList>

        {/* 감사 로그 탭 */}
        <TabsContent value="audit-log">
          <Card>
            <CardHeader>
              <CardTitle>실시간 감사 로그</CardTitle>
              <CardDescription>
                모든 시스템 이벤트와 트랜잭션의 실시간 로그
              </CardDescription>

              {/* 필터 및 검색 */}
              <div className="flex gap-4 mt-4">
                <div className="flex-1">
                  <Input
                    placeholder="이벤트 검색..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="max-w-sm"
                  />
                </div>
                <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="이벤트 유형" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">모든 유형</SelectItem>
                    <SelectItem value="TRANSACTION_COMPLETED">트랜잭션 완료</SelectItem>
                    <SelectItem value="SUSPICIOUS_ACTIVITY">의심스러운 활동</SelectItem>
                    <SelectItem value="COMPLIANCE_CHECK">컴플라이언스 체크</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredAuditEvents.map((event) => (
                  <div key={event.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getStatusColor(event.status)}>
                          {event.status.toUpperCase()}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {event.event_type}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm">{event.description}</p>
                      {event.user_id && (
                        <p className="text-xs text-muted-foreground mt-1">
                          User: {event.user_id}
                          {event.transaction_id && ` | Transaction: ${event.transaction_id}`}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        위험도: {event.risk_score}/10
                      </div>
                      <Button variant="ghost" size="sm">
                        <FileText className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 의심스러운 활동 탭 */}
        <TabsContent value="suspicious">
          <Card>
            <CardHeader>
              <CardTitle>의심스러운 활동 탐지</CardTitle>
              <CardDescription>
                ML 기반 이상 거래 패턴 탐지 및 분석
              </CardDescription>

              {/* 위험 레벨 필터 */}
              <div className="flex gap-4 mt-4">
                <Select value={riskLevelFilter} onValueChange={setRiskLevelFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="위험 레벨" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">모든 레벨</SelectItem>
                    <SelectItem value="low">낮음</SelectItem>
                    <SelectItem value="medium">보통</SelectItem>
                    <SelectItem value="high">높음</SelectItem>
                    <SelectItem value="critical">위험</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredSuspiciousActivities.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getRiskLevelColor(activity.risk_level)}>
                          {activity.risk_level.toUpperCase()}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {activity.activity_type}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(activity.detected_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm">{activity.description}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        User: {activity.user_id} | Amount: ${activity.transaction_amount.toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        조사
                      </Button>
                      <Button variant="ghost" size="sm">
                        무시
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 컴플라이언스 체크 탭 */}
        <TabsContent value="compliance">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>AML/KYC 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>AML 체크 통과</span>
                    <span className="font-bold">{metrics.aml_checks_passed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>KYC 인증 완료</span>
                    <span className="font-bold">{metrics.kyc_verifications}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>컴플라이언스 율</span>
                    <span className="font-bold text-green-600">{metrics.compliance_rate}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>규제 보고</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button variant="outline" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    SAR 보고서 생성
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    CTR 보고서 생성
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    일일 감사 보고서
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 보고서 탭 */}
        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>보고서 생성</CardTitle>
              <CardDescription>
                각종 규제 보고서 및 감사 문서 생성
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button variant="outline" className="h-24 flex-col">
                  <FileText className="w-8 h-8 mb-2" />
                  일일 감사 보고서
                </Button>
                <Button variant="outline" className="h-24 flex-col">
                  <Shield className="w-8 h-8 mb-2" />
                  컴플라이언스 보고서
                </Button>
                <Button variant="outline" className="h-24 flex-col">
                  <AlertTriangle className="w-8 h-8 mb-2" />
                  의심거래 보고서
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AuditCompliancePage;
