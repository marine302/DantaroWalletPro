'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  FileText, 
  Search, 
  Download, 
  AlertTriangle,
  CheckCircle,
  Eye,
  TrendingUp,
  Settings,
  Bell,
  Activity
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useAuditLogs, useComplianceReports, useSecurityEvents } from '@/lib/hooks'

// 감사 로그 타입 정의
interface AuditLog {
  id: string
  timestamp: string
  user_id: string
  user_name: string
  action: string
  resource: string
  details: Record<string, unknown>
  ip_address: string
  user_agent: string
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  compliance_flags: string[]
}

interface ComplianceReport {
  id: string
  type: 'kyc' | 'aml' | 'transaction' | 'security' | 'operational'
  title: string
  generated_at: string
  period: string
  status: 'pending' | 'completed' | 'flagged'
  findings: number
  recommendations: string[]
  file_url?: string
}

interface SecurityEvent {
  id: string
  timestamp: string
  event_type: 'failed_login' | 'suspicious_transaction' | 'api_abuse' | 'data_access'
  severity: 'info' | 'warning' | 'critical'
  description: string
  source_ip: string
  affected_user?: string
  status: 'open' | 'investigating' | 'resolved' | 'false_positive'
  assigned_to?: string
}

export default function AuditCompliancePage() {
  const [auditSearchTerm, setAuditSearchTerm] = useState('')
  const [auditDateFilter, setAuditDateFilter] = useState('7d')
  const [riskLevelFilter, setRiskLevelFilter] = useState<string>('all')
  const [selectedEventType, setSelectedEventType] = useState<string>('all')

  // API 훅 사용
  const { data: auditData, isLoading: auditLoading } = useAuditLogs({
    search: auditSearchTerm,
    period: auditDateFilter,
    risk_level: riskLevelFilter !== 'all' ? riskLevelFilter : undefined
  })
  const { data: reportsData, isLoading: reportsLoading } = useComplianceReports()
  const { data: securityData, isLoading: securityLoading } = useSecurityEvents({
    event_type: selectedEventType !== 'all' ? selectedEventType : undefined
  })

  // 폴백 데이터
  const fallbackAuditLogs: AuditLog[] = [
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
      risk_level: 'medium',
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
      risk_level: 'high',
      compliance_flags: ['policy_change', 'limit_increase']
    }
  ]

  const fallbackReports: ComplianceReport[] = [
    {
      id: 'report_001',
      type: 'aml',
      title: '자금세탁방지 월간 리포트',
      generated_at: '2025-07-20T00:00:00Z',
      period: '2025-06',
      status: 'completed',
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
      type: 'security',
      title: '보안 감사 주간 리포트',
      generated_at: '2025-07-19T00:00:00Z',
      period: '2025-W29',
      status: 'flagged',
      findings: 5,
      recommendations: [
        'API 접근 로그 모니터링 강화',
        '2FA 강제 적용 검토',
        '비정상 로그인 패턴 차단 규칙 추가'
      ]
    }
  ]

  const fallbackSecurityEvents: SecurityEvent[] = [
    {
      id: 'sec_001',
      timestamp: '2025-07-20T11:00:00Z',
      event_type: 'suspicious_transaction',
      severity: 'warning',
      description: '단시간 내 대량 출금 요청 감지',
      source_ip: '192.168.1.50',
      affected_user: 'user_12345',
      status: 'investigating',
      assigned_to: 'security_team'
    },
    {
      id: 'sec_002',
      timestamp: '2025-07-20T10:45:00Z',
      event_type: 'failed_login',
      severity: 'info',
      description: '다중 로그인 실패 시도',
      source_ip: '203.0.113.10',
      status: 'resolved'
    }
  ]

  // 실제 API 데이터와 폴백 데이터 병합
  const auditLogs = (auditData as { logs?: AuditLog[] })?.logs || fallbackAuditLogs
  const reports = (reportsData as { reports?: ComplianceReport[] })?.reports || fallbackReports
  const securityEvents = (securityData as { events?: SecurityEvent[] })?.events || fallbackSecurityEvents

  const getRiskLevelBadge = (level: string) => {
    const config = {
      low: { variant: 'secondary' as const, text: '낮음', color: 'text-green-600' },
      medium: { variant: 'outline' as const, text: '보통', color: 'text-yellow-600' },
      high: { variant: 'destructive' as const, text: '높음', color: 'text-orange-600' },
      critical: { variant: 'destructive' as const, text: '심각', color: 'text-red-600' }
    }
    const cfg = config[level as keyof typeof config] || config.low
    return <Badge variant={cfg.variant} className={cfg.color}>{cfg.text}</Badge>
  }

  const getReportStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge variant="default">완료</Badge>
      case 'pending': return <Badge variant="secondary">진행중</Badge>
      case 'flagged': return <Badge variant="destructive">이슈발견</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return <Badge variant="destructive">심각</Badge>
      case 'warning': return <Badge variant="outline" className="text-orange-600">경고</Badge>
      case 'info': return <Badge variant="secondary">정보</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  const getEventStatusBadge = (status: string) => {
    switch (status) {
      case 'open': return <Badge variant="destructive">열림</Badge>
      case 'investigating': return <Badge variant="outline" className="text-blue-600">조사중</Badge>
      case 'resolved': return <Badge variant="default">해결</Badge>
      case 'false_positive': return <Badge variant="secondary">오탐</Badge>
      default: return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  if (auditLoading || reportsLoading || securityLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6 animate-spin" />
          <span className="text-lg">감사 정보를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  return (
    <Sidebar>
      <div className="flex h-screen bg-background">      
        <main className="flex-1 p-8 overflow-auto">
          <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">감사 및 컴플라이언스</h1>
                <p className="text-muted-foreground">
                  Doc-30: 실시간 감사 추적, 컴플라이언스 리포팅 및 보안 모니터링
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="outline" className="flex items-center space-x-2">
                  <Download className="w-4 h-4" />
                  <span>감사 리포트 다운로드</span>
                </Button>
                <Button className="flex items-center space-x-2">
                  <Settings className="w-4 h-4" />
                  <span>감사 설정</span>
                </Button>
              </div>
            </div>
          </div>

          {/* 개요 통계 */}
          <div className="grid gap-6 md:grid-cols-4 mb-8">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{auditLogs.length}</div>
                    <div className="text-sm text-muted-foreground">오늘 감사 로그</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {auditLogs.filter(log => log.risk_level === 'high' || log.risk_level === 'critical').length}
                    </div>
                    <div className="text-sm text-muted-foreground">고위험 이벤트</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {reports.filter(r => r.status === 'completed').length}
                    </div>
                    <div className="text-sm text-muted-foreground">완료된 리포트</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Bell className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {securityEvents.filter(e => e.status === 'open' || e.status === 'investigating').length}
                    </div>
                    <div className="text-sm text-muted-foreground">활성 보안 이벤트</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="audit-logs" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="audit-logs">감사 로그</TabsTrigger>
              <TabsTrigger value="compliance">컴플라이언스 리포트</TabsTrigger>
              <TabsTrigger value="security">보안 이벤트</TabsTrigger>
              <TabsTrigger value="monitoring">실시간 모니터링</TabsTrigger>
            </TabsList>

            {/* 감사 로그 탭 */}
            <TabsContent value="audit-logs" className="space-y-6">
              {/* 검색 및 필터 */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <div className="relative">
                        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="사용자, 액션, 리소스 검색..."
                          value={auditSearchTerm}
                          onChange={(e) => setAuditSearchTerm(e.target.value)}
                          className="pl-9"
                        />
                      </div>
                    </div>
                    <select 
                      value={auditDateFilter} 
                      onChange={(e) => setAuditDateFilter(e.target.value)}
                      className="px-3 py-2 border rounded-md"
                    >
                      <option value="1d">최근 1일</option>
                      <option value="7d">최근 7일</option>
                      <option value="30d">최근 30일</option>
                    </select>
                    <select 
                      value={riskLevelFilter} 
                      onChange={(e) => setRiskLevelFilter(e.target.value)}
                      className="px-3 py-2 border rounded-md"
                    >
                      <option value="all">모든 위험도</option>
                      <option value="low">낮음</option>
                      <option value="medium">보통</option>
                      <option value="high">높음</option>
                      <option value="critical">심각</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              {/* 감사 로그 목록 */}
              <div className="space-y-3">
                {auditLogs.map((log) => (
                  <Card key={log.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="text-sm text-muted-foreground">
                              {formatDate(log.timestamp)}
                            </span>
                            {getRiskLevelBadge(log.risk_level)}
                            <Badge variant="outline">{log.action}</Badge>
                          </div>
                          
                          <div className="mb-2">
                            <span className="font-medium">{log.user_name}</span>
                            <span className="text-muted-foreground"> • {log.resource}</span>
                          </div>
                          
                          <div className="text-sm text-muted-foreground mb-2">
                            IP: {log.ip_address} • User Agent: {log.user_agent.substring(0, 50)}...
                          </div>

                          {log.compliance_flags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              {log.compliance_flags.map((flag, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {flag}
                                </Badge>
                              ))}
                            </div>
                          )}

                          <details className="text-sm">
                            <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                              상세 정보 보기
                            </summary>
                            <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </details>
                        </div>
                        
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* 컴플라이언스 리포트 탭 */}
            <TabsContent value="compliance" className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                {reports.map((report) => (
                  <Card key={report.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{report.title}</CardTitle>
                        {getReportStatusBadge(report.status)}
                      </div>
                      <CardDescription>
                        {report.period} • 생성일: {formatDate(report.generated_at)}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">발견 사항</span>
                          <Badge variant={report.findings > 0 ? 'destructive' : 'default'}>
                            {report.findings}건
                          </Badge>
                        </div>

                        {report.recommendations.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2">권장 사항</h4>
                            <ul className="space-y-1">
                              {report.recommendations.map((rec, idx) => (
                                <li key={idx} className="text-sm text-muted-foreground flex items-start">
                                  <CheckCircle className="w-3 h-3 mr-2 mt-0.5 text-green-500" />
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="flex items-center space-x-2 pt-2">
                          {report.file_url && (
                            <Button variant="outline" size="sm" className="flex items-center space-x-1">
                              <Download className="w-3 h-3" />
                              <span>다운로드</span>
                            </Button>
                          )}
                          <Button variant="outline" size="sm" className="flex items-center space-x-1">
                            <Eye className="w-3 h-3" />
                            <span>상세보기</span>
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* 보안 이벤트 탭 */}
            <TabsContent value="security" className="space-y-6">
              {/* 이벤트 필터 */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-4">
                    <select 
                      value={selectedEventType} 
                      onChange={(e) => setSelectedEventType(e.target.value)}
                      className="px-3 py-2 border rounded-md"
                    >
                      <option value="all">모든 이벤트</option>
                      <option value="failed_login">로그인 실패</option>
                      <option value="suspicious_transaction">의심 거래</option>
                      <option value="api_abuse">API 남용</option>
                      <option value="data_access">데이터 접근</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              {/* 보안 이벤트 목록 */}
              <div className="space-y-3">
                {securityEvents.map((event) => (
                  <Card key={event.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="text-sm text-muted-foreground">
                              {formatDate(event.timestamp)}
                            </span>
                            {getSeverityBadge(event.severity)}
                            {getEventStatusBadge(event.status)}
                          </div>
                          
                          <h3 className="font-medium mb-2">{event.description}</h3>
                          
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div>소스 IP: {event.source_ip}</div>
                            {event.affected_user && (
                              <div>영향받은 사용자: {event.affected_user}</div>
                            )}
                            {event.assigned_to && (
                              <div>담당자: {event.assigned_to}</div>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex space-x-2">
                          <Button variant="outline" size="sm">조치</Button>
                          <Button variant="outline" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* 실시간 모니터링 탭 */}
            <TabsContent value="monitoring" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    실시간 감사 대시보드
                  </CardTitle>
                  <CardDescription>
                    시스템 활동과 보안 이벤트를 실시간으로 모니터링합니다
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>실시간 모니터링 차트가 여기에 표시됩니다</p>
                    <p className="text-sm">(WebSocket 연동 후 활성화)</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
    </Sidebar>
  )
}
