'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { AuditManagementSection } from '@/components/audit/AuditManagementSection'

export default function AuditPage() {
  // 목업 데이터
  const [stats] = useState({
    totalLogs: 15420,
    highRiskEvents: 23,
    complianceViolations: 7,
    securityIncidents: 12,
    todayGrowth: 5.2,
    weeklyGrowth: 12.5
  })

  const [logs] = useState([
    {
      id: 'audit_001',
      timestamp: '2025-07-20T10:30:00Z',
      user_id: 'admin_001',
      user_name: '관리자',
      action: 'withdrawal_approval',
      resource: '/api/withdrawal/approve/12345',
      details: { amount: 50000, currency: 'USDT', destination: 'TRon...xyz123' },
      ip_address: '192.168.1.100',
      user_agent: 'Mozilla/5.0...',
      risk_level: 'medium' as const,
      compliance_flags: ['large_amount', 'manual_review']
    },
    {
      id: 'audit_002',
      timestamp: '2025-07-20T09:15:00Z',
      user_id: 'partner_001',
      user_name: '파트너사A',
      action: 'policy_update',
      resource: '/api/withdrawal/policy',
      details: { policy_type: 'daily_limit', old_value: 100000, new_value: 150000 },
      ip_address: '203.123.45.67',
      user_agent: 'Mozilla/5.0...',
      risk_level: 'high' as const,
      compliance_flags: ['policy_change', 'limit_increase']
    }
  ])

  const [reports] = useState([
    {
      id: 'report_001',
      type: 'aml' as const,
      title: '자금세탁방지 월간 리포트',
      generated_at: '2025-07-20T00:00:00Z',
      period: '2025-06',
      status: 'completed' as const,
      findings: 3,
      recommendations: [
        '의심 거래 모니터링 강화',
        'KYC 재검증 프로세스 개선',
        '고위험 국가 거래 추가 검토'
      ],
      file_url: '/reports/aml-2025-06.pdf'
    },
    {
      id: 'report_002',
      type: 'security' as const,
      title: '보안 감사 주간 리포트',
      generated_at: '2025-07-19T00:00:00Z',
      period: '2025-W29',
      status: 'flagged' as const,
      findings: 5,
      recommendations: [
        'API 접근 로그 모니터링 강화',
        '2FA 강제 적용 검토',
        '비정상 로그인 패턴 차단 규칙 추가'
      ]
    }
  ])

  const [securityEvents] = useState([
    {
      id: 'sec_001',
      type: 'suspicious_activity' as const,
      severity: 'warning' as const,
      timestamp: '2025-07-20T11:00:00Z',
      description: '단시간 내 대량 출금 요청 감지',
      ip_address: '192.168.1.50',
      user_id: 'user_12345',
      resolved: false,
      assigned_to: 'security_team'
    },
    {
      id: 'sec_002',
      type: 'login_anomaly' as const,
      severity: 'info' as const,
      timestamp: '2025-07-20T10:45:00Z',
      description: '다중 로그인 실패 시도',
      ip_address: '203.0.113.10',
      resolved: true
    }
  ])

  const handleRefresh = () => {
    console.log('감사 데이터 새로고침')
  }

  const handleGenerateReport = () => {
    console.log('새 리포트 생성')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <AuditManagementSection
          stats={stats}
          logs={logs}
          reports={reports}
          securityEvents={securityEvents}
          onRefresh={handleRefresh}
          onGenerateReport={handleGenerateReport}
        />
      </div>
    </Sidebar>
  )
}