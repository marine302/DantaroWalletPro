'use client';

import { withRBAC } from '@/components/auth/withRBAC';
import BasePage from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import { useState, Suspense } from 'react';
import { Loading } from '@/components/ui/Loading';
import {
  RealtimeTransactionMonitorLazy,
  EmergencyBlockingPanelLazy,
  AuditLogSearchLazy
} from '@/components/lazy/LazyComponents';

// 임시 i18n mock (I18nContext가 없으므로)
const _mockI18n = {
  auditCompliance: {
    title: 'Audit & Compliance',
    description: 'Monitor audit logs and compliance status',
    auditLog: 'Audit Log',
    suspiciousActivities: 'Suspicious Activities',
    complianceCheck: 'Compliance Check',
    reports: 'Reports',
    alerts: 'Alerts',
    investigations: 'Investigations',
    complianceMetrics: 'Compliance Metrics',
    auditTrail: 'Audit Trail',
    securityIncidents: 'Security Incidents',
    generateReport: 'Generate Report',
    executeAudit: 'Execute Audit',
    totalAudits: 'Total Audits',
    totalAuditsDesc: 'Total number of audits performed',
    passedAudits: 'Passed Audits',
    passedAuditsDesc: 'Number of successful audits',
    failedAudits: 'Failed Audits',
    failedAuditsDesc: 'Number of failed audits',
    pendingReviews: 'Pending Reviews',
    pendingReviewsDesc: 'Audits pending review',
    complianceScore: 'Compliance Score',
    complianceScoreDesc: 'Overall compliance score',
    lastAuditTime: 'Last Audit',
    lastAuditTimeDesc: 'Time of last audit',
    criticalAlerts: 'Critical Alerts',
    criticalAlertsDesc: 'Number of critical alerts',
    monthlyReports: 'Monthly Reports',
    monthlyReportsDesc: 'Generated monthly reports',
    allLogs: 'All Logs',
    successLogs: 'Success',
    failedLogs: 'Failed',
    warningLogs: 'Warning',
    time: 'Time',
    user: 'User',
    action: 'Action',
    resource: 'Resource',
    status: 'Status',
    riskLevel: 'Risk Level',
    ipAddress: 'IP Address',
    details: 'Details',
    complianceTools: 'Compliance Tools',
    amlReport: 'AML Report',
    transactionMonitoring: 'Transaction Monitoring',
    complianceCheckTool: 'Compliance Check Tool',
    suspiciousTransactionReport: 'Suspicious Transaction Report'
  }
};

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
  const _t = mockI18n; // mockI18n 사용

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

  const _getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-900/30 text-green-300';
      case 'failed': return 'bg-red-900/30 text-red-300';
      case 'warning': return 'bg-yellow-900/30 text-yellow-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  };

  const _getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-blue-900/30 text-blue-300';
      case 'medium': return 'bg-yellow-900/30 text-yellow-300';
      case 'high': return 'bg-orange-900/30 text-orange-300';
      case 'critical': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  };

  const _filteredLogs = filter === 'all' ? auditLogs : auditLogs.filter(log => log.status === filter);

  const _headerActions = (
    <div className="flex gap-2">
      <Button variant="secondary">
        {t.auditCompliance.generateReport}
      </Button>
      <Button variant="primary">
        {t.auditCompliance.executeAudit}
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
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">📄</span>
            {t.auditCompliance.amlReport}
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">🔍</span>
            {t.auditCompliance.transactionMonitoring}
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">🛡️</span>
            {t.auditCompliance.complianceCheckTool}
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
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
