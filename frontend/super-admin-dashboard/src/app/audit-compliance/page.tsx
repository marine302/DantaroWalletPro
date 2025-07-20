'use client';

import React, { useState } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import { Badge } from '@/components/ui/Badge';
import { useI18n } from '@/contexts/I18nContext';
import { withRBAC } from '@/components/auth/withRBAC';

// 타입 정의
interface AuditLog {
  id: number;
  timestamp: string;
  userId: string;
  action: string;
  resource: string;
  details: string;
  ipAddress: string;
  status: 'success' | 'failed' | 'warning';
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
}

interface ComplianceMetrics {
  totalAudits: number;
  passedAudits: number;
  failedAudits: number;
  pendingReviews: number;
  complianceScore: number;
  lastAuditDate: string;
  criticalIssues: number;
  resolvedIssues: number;
}

function AuditCompliancePage() {
  const { t } = useI18n();
  
  const [metrics] = useState<ComplianceMetrics>({
    totalAudits: 156,
    passedAudits: 142,
    failedAudits: 8,
    pendingReviews: 6,
    complianceScore: 94.2,
    lastAuditDate: '2025-01-20',
    criticalIssues: 2,
    resolvedIssues: 147
  });

  const [auditLogs] = useState<AuditLog[]>([
    {
      id: 1,
      timestamp: '2025-01-20T10:30:00Z',
      userId: 'admin@system.com',
      action: 'LOGIN',
      resource: 'Admin Dashboard',
      details: 'Successful admin login',
      ipAddress: '192.168.1.100',
      status: 'success',
      riskLevel: 'low'
    },
    {
      id: 2,
      timestamp: '2025-01-20T09:45:00Z',
      userId: 'partner@crypto.com',
      action: 'TRANSACTION_REVIEW',
      resource: 'Large Transaction',
      details: 'Reviewed $100K+ transaction',
      ipAddress: '10.0.0.50',
      status: 'success',
      riskLevel: 'medium'
    },
    {
      id: 3,
      timestamp: '2025-01-20T08:15:00Z',
      userId: 'system@auto.com',
      action: 'COMPLIANCE_CHECK',
      resource: 'AML Screening',
      details: 'Automated AML check failed',
      ipAddress: '127.0.0.1',
      status: 'failed',
      riskLevel: 'high'
    },
    {
      id: 4,
      timestamp: '2025-01-19T16:22:00Z',
      userId: 'auditor@external.com',
      action: 'AUDIT_REPORT',
      resource: 'Monthly Compliance',
      details: 'Generated monthly compliance report',
      ipAddress: '203.0.113.1',
      status: 'success',
      riskLevel: 'low'
    }
  ]);

  const [filter, setFilter] = useState('all');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-900/30 text-green-300';
      case 'failed': return 'bg-red-900/30 text-red-300';
      case 'warning': return 'bg-yellow-900/30 text-yellow-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-blue-900/30 text-blue-300';
      case 'medium': return 'bg-yellow-900/30 text-yellow-300';
      case 'high': return 'bg-orange-900/30 text-orange-300';
      case 'critical': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  };

  const filteredLogs = filter === 'all' ? auditLogs : auditLogs.filter(log => log.status === filter);

  const headerActions = (
    <div className="flex gap-2">
      <Button variant="secondary">
        보고서 생성
      </Button>
      <Button variant="primary">
        감사 실행
      </Button>
    </div>
  );

  return (
    <BasePage 
      title={t.auditCompliance?.title || "감사 및 컴플라이언스"}
      description={t.auditCompliance?.description || "시스템 감사, 컴플라이언스 모니터링 및 규정 준수를 관리합니다"}
      headerActions={headerActions}
    >
      {/* 컴플라이언스 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4 mb-6">
        <StatCard
          title="전체 감사"
          value={metrics.totalAudits.toString()}
          icon="📋"
          description="총 감사 건수"
        />
        <StatCard
          title="통과"
          value={metrics.passedAudits.toString()}
          icon="✅"
          description="성공한 감사"
        />
        <StatCard
          title="실패"
          value={metrics.failedAudits.toString()}
          icon="❌"
          description="실패한 감사"
        />
        <StatCard
          title="대기중"
          value={metrics.pendingReviews.toString()}
          icon="⏳"
          description="검토 대기"
        />
        <StatCard
          title="컴플라이언스 점수"
          value={`${metrics.complianceScore}%`}
          icon="📊"
          description="전체 준수율"
        />
        <StatCard
          title="마지막 감사"
          value={new Date(metrics.lastAuditDate).toLocaleDateString()}
          icon="📅"
          description="최근 감사일"
        />
        <StatCard
          title="심각한 이슈"
          value={metrics.criticalIssues.toString()}
          icon="🚨"
          description="긴급 처리 필요"
        />
        <StatCard
          title="해결된 이슈"
          value={metrics.resolvedIssues.toString()}
          icon="🔧"
          description="처리 완료"
        />
      </div>

      {/* 필터 및 감사 로그 */}
      <Section title="감사 로그">
        {/* 필터 버튼 */}
        <div className="flex gap-2 mb-4">
          <Button 
            variant={filter === 'all' ? 'primary' : 'secondary'}
            onClick={() => setFilter('all')}
          >
            전체
          </Button>
          <Button 
            variant={filter === 'success' ? 'primary' : 'secondary'}
            onClick={() => setFilter('success')}
          >
            성공
          </Button>
          <Button 
            variant={filter === 'failed' ? 'primary' : 'secondary'}
            onClick={() => setFilter('failed')}
          >
            실패
          </Button>
          <Button 
            variant={filter === 'warning' ? 'primary' : 'secondary'}
            onClick={() => setFilter('warning')}
          >
            경고
          </Button>
        </div>

        {/* 감사 로그 테이블 */}
        <div className="overflow-hidden shadow ring-1 ring-gray-700 rounded-lg">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  시간
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  사용자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  액션
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  리소스
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  위험도
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  IP 주소
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  세부사항
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-900 divide-y divide-gray-700">
              {filteredLogs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                    {log.userId}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                    {log.action}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {log.resource}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(log.status)}`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(log.riskLevel)}`}>
                      {log.riskLevel}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {log.ipAddress}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">
                    {log.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* 컴플라이언스 액션 */}
      <Section title="컴플라이언스 도구">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">📄</span>
            AML 보고서
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">🔍</span>
            거래 모니터링
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">🛡️</span>
            컴플라이언스 체크
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">⚠️</span>
            의심거래 보고
          </Button>
        </div>
      </Section>
    </BasePage>
  );
}

// Export protected component
export default withRBAC(AuditCompliancePage, { 
  requiredPermissions: ['audit.view', 'compliance.view']
});
