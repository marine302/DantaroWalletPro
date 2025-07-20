'use client';

import React, { useState } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import { withRBAC } from '@/components/auth/withRBAC';
import { useI18n } from '@/contexts/I18nContext';

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
    criticalIssues: 3,
    resolvedIssues: 128
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
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isExecutingAudit, setIsExecutingAudit] = useState(false);

  // 보고서 생성 함수
  const handleGenerateReport = async () => {
    try {
      setIsGeneratingReport(true);
      
      // Mock API 호출 - 실제로는 백엔드 API를 호출
      console.log('📊 보고서 생성 시작...');
      
      // 로딩 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 보고서 데이터 생성 (Mock)
      const reportData = {
        reportId: `AUDIT_RPT_${Date.now()}`,
        generatedAt: new Date().toISOString(),
        period: 'monthly',
        totalAudits: metrics.totalAudits,
        passedAudits: metrics.passedAudits,
        failedAudits: metrics.failedAudits,
        complianceScore: metrics.complianceScore,
        criticalIssues: metrics.criticalIssues
      };
      
      // 파일 다운로드 시뮬레이션
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-compliance-report-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      alert('✅ 보고서가 성공적으로 생성되어 다운로드되었습니다.');
      console.log('📊 보고서 생성 완료');
      
    } catch (error) {
      console.error('❌ 보고서 생성 실패:', error);
      alert('❌ 보고서 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // 감사 실행 함수
  const handleExecuteAudit = async () => {
    try {
      setIsExecutingAudit(true);
      
      console.log('🔍 감사 실행 시작...');
      
      // 사용자 확인
      const confirmed = window.confirm('감사를 실행하시겠습니까? 이 작업은 시간이 걸릴 수 있습니다.');
      if (!confirmed) {
        setIsExecutingAudit(false);
        return;
      }
      
      // Mock 감사 실행 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 새로운 감사 로그 추가 (Mock)
      const newAuditLog: AuditLog = {
        id: auditLogs.length + 1,
        timestamp: new Date().toISOString(),
        userId: 'system@audit.com',
        action: 'MANUAL_AUDIT',
        resource: 'Full System Audit',
        details: 'Manual audit execution completed',
        ipAddress: '127.0.0.1',
        status: 'success',
        riskLevel: 'low'
      };
      
      // 실제로는 상태를 업데이트하거나 페이지를 새로고침해야 함
      console.log('새 감사 로그:', newAuditLog);
      
      alert('✅ 감사가 성공적으로 실행되었습니다. 결과가 감사 로그에 추가되었습니다.');
      console.log('🔍 감사 실행 완료');
      
      // 페이지 새로고침으로 최신 데이터 가져오기
      window.location.reload();
      
    } catch (error) {
      console.error('❌ 감사 실행 실패:', error);
      alert('❌ 감사 실행 중 오류가 발생했습니다.');
    } finally {
      setIsExecutingAudit(false);
    }
  };

  // 컴플라이언스 도구 핸들러 함수들
  const handleAmlReport = () => {
    alert('📄 AML 보고서 기능을 실행합니다.\n\n실제 구현 시 AML 분석 대시보드로 이동하거나 보고서를 생성합니다.');
    console.log('📄 AML 보고서 실행');
  };

  const handleTransactionMonitoring = () => {
    alert('🔍 실시간 거래 모니터링 기능을 실행합니다.\n\n실제 구현 시 거래 모니터링 대시보드를 표시합니다.');
    console.log('🔍 거래 모니터링 실행');
  };

  const handleComplianceCheck = () => {
    alert('🛡️ 컴플라이언스 체크를 실행합니다.\n\n실제 구현 시 자동화된 컴플라이언스 검사를 시작합니다.');
    console.log('🛡️ 컴플라이언스 체크 실행');
  };

  const handleSuspiciousTransactionReport = () => {
    alert('⚠️ 의심거래 보고 기능을 실행합니다.\n\n실제 구현 시 의심스러운 거래 분석 및 보고서를 생성합니다.');
    console.log('⚠️ 의심거래 보고 실행');
  };

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
      <Button 
        variant="secondary"
        onClick={handleGenerateReport}
        disabled={isGeneratingReport}
      >
        {isGeneratingReport ? '📊 생성 중...' : t.auditCompliance.generateReport}
      </Button>
      <Button 
        variant="primary"
        onClick={handleExecuteAudit}
        disabled={isExecutingAudit}
      >
        {isExecutingAudit ? '🔍 실행 중...' : t.auditCompliance.executeAudit}
      </Button>
    </div>
  );

  return (
    <BasePage 
      title={t.auditCompliance.title}
      description={t.auditCompliance.description}
      headerActions={headerActions}
    >
      {/* 컴플라이언스 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4 mb-6">
        <StatCard
          title={t.auditCompliance.totalAudits}
          value={metrics.totalAudits.toString()}
          icon="📋"
          description={t.auditCompliance.totalAuditsDesc}
        />
        <StatCard
          title={t.auditCompliance.passedAudits}
          value={metrics.passedAudits.toString()}
          icon="✅"
          description={t.auditCompliance.passedAuditsDesc}
        />
        <StatCard
          title={t.auditCompliance.failedAudits}
          value={metrics.failedAudits.toString()}
          icon="❌"
          description={t.auditCompliance.failedAuditsDesc}
        />
        <StatCard
          title={t.auditCompliance.pendingReviews}
          value={metrics.pendingReviews.toString()}
          icon="⏳"
          description={t.auditCompliance.pendingReviewsDesc}
        />
        <StatCard
          title={t.auditCompliance.complianceScore}
          value={`${metrics.complianceScore}%`}
          icon="📊"
          description={t.auditCompliance.complianceScoreDesc}
        />
        <StatCard
          title={t.auditCompliance.lastAuditTime}
          value={new Date(metrics.lastAuditDate).toLocaleDateString()}
          icon="📅"
          description={t.auditCompliance.lastAuditTimeDesc}
        />
        <StatCard
          title={t.auditCompliance.criticalAlerts}
          value={metrics.criticalIssues.toString()}
          icon="🚨"
          description={t.auditCompliance.criticalAlertsDesc}
        />
        <StatCard
          title={t.auditCompliance.monthlyReports}
          value={metrics.resolvedIssues.toString()}
          icon="🔧"
          description={t.auditCompliance.monthlyReportsDesc}
        />
      </div>

      {/* 필터 및 감사 로그 */}
      <Section title={t.auditCompliance.auditLog}>
        {/* 필터 버튼 */}
        <div className="flex gap-2 mb-4">
          <Button 
            variant={filter === 'all' ? 'primary' : 'secondary'}
            onClick={() => setFilter('all')}
          >
            {t.auditCompliance.allLogs}
          </Button>
          <Button 
            variant={filter === 'success' ? 'primary' : 'secondary'}
            onClick={() => setFilter('success')}
          >
            {t.auditCompliance.successLogs}
          </Button>
          <Button 
            variant={filter === 'failed' ? 'primary' : 'secondary'}
            onClick={() => setFilter('failed')}
          >
            {t.auditCompliance.failedLogs}
          </Button>
          <Button 
            variant={filter === 'warning' ? 'primary' : 'secondary'}
            onClick={() => setFilter('warning')}
          >
            {t.auditCompliance.warningLogs}
          </Button>
        </div>

        {/* 감사 로그 테이블 */}
        <div className="overflow-x-auto shadow ring-1 ring-gray-700 rounded-lg">
          <div className="min-w-full">
            <table className="w-full divide-y divide-gray-600">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[150px]">
                    {t.auditCompliance.time}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[200px]">
                    {t.auditCompliance.user}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[160px]">
                    {t.auditCompliance.action}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[180px]">
                    {t.auditCompliance.resource}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[100px]">
                    {t.auditCompliance.status}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[100px]">
                    {t.auditCompliance.riskLevel}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[140px]">
                    {t.auditCompliance.ipAddress}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[250px]">
                    {t.auditCompliance.details}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-900 divide-y divide-gray-700">
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 min-w-[150px]">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100 min-w-[200px]">
                      {log.userId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white min-w-[160px]">
                      {log.action}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 min-w-[180px]">
                      {log.resource}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap min-w-[100px]">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap min-w-[100px]">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(log.riskLevel)}`}>
                        {log.riskLevel}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 min-w-[140px]">
                      {log.ipAddress}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300 min-w-[250px]">
                      {log.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Section>

      {/* 컴플라이언스 액션 */}
      <Section title={t.auditCompliance.complianceTools}>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <Button 
            variant="secondary" 
            className="h-20 flex-col"
            onClick={handleAmlReport}
          >
            <span className="text-2xl mb-2">📄</span>
            {t.auditCompliance.amlReport}
          </Button>
          <Button 
            variant="secondary" 
            className="h-20 flex-col"
            onClick={handleTransactionMonitoring}
          >
            <span className="text-2xl mb-2">🔍</span>
            {t.auditCompliance.transactionMonitoring}
          </Button>
          <Button 
            variant="secondary" 
            className="h-20 flex-col"
            onClick={handleComplianceCheck}
          >
            <span className="text-2xl mb-2">🛡️</span>
            {t.auditCompliance.complianceCheckTool}
          </Button>
          <Button 
            variant="secondary" 
            className="h-20 flex-col"
            onClick={handleSuspiciousTransactionReport}
          >
            <span className="text-2xl mb-2">⚠️</span>
            {t.auditCompliance.suspiciousTransactionReport}
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
