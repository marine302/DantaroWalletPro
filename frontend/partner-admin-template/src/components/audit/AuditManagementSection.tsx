'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/common/PageHeader'
import { 
  FileText, 
  Search, 
  Download, 
  AlertTriangle,
  Eye,
  Settings,
  Activity
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

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
  type: 'login_anomaly' | 'failed_transaction' | 'suspicious_activity' | 'compliance_violation'
  severity: 'info' | 'warning' | 'critical'
  timestamp: string
  description: string
  user_id?: string
  ip_address: string
  resolved: boolean
  assigned_to?: string
}

interface AuditStats {
  totalLogs: number
  highRiskEvents: number
  complianceViolations: number
  securityIncidents: number
  todayGrowth: number
  weeklyGrowth: number
}

interface AuditManagementSectionProps {
  stats: AuditStats
  logs: AuditLog[]
  reports: ComplianceReport[]
  securityEvents: SecurityEvent[]
  onRefresh: () => void
  onGenerateReport: () => void
}

export function AuditManagementSection({
  stats,
  logs,
  reports,
  securityEvents,
  onRefresh,
  onGenerateReport
}: AuditManagementSectionProps) {
  const [activeTab, setActiveTab] = useState('logs')
  const [searchTerm, setSearchTerm] = useState('')
  const [riskFilter, setRiskFilter] = useState('')

  const getRiskColor = (level: string) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    }
    return colors[level as keyof typeof colors] || colors.low
  }

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      flagged: 'bg-red-100 text-red-800'
    }
    return colors[status as keyof typeof colors] || colors.pending
  }

  const getSeverityColor = (severity: string) => {
    const colors = {
      info: 'bg-blue-100 text-blue-800',
      warning: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800'
    }
    return colors[severity as keyof typeof colors] || colors.info
  }

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.user_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRisk = !riskFilter || log.risk_level === riskFilter
    return matchesSearch && matchesRisk
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="감사 로그"
        description="시스템 감사 추적 및 컴플라이언스 관리"
        onRefresh={onRefresh}
        showDownload={true}
      >
        <Button onClick={onGenerateReport}>
          <FileText className="h-4 w-4 mr-2" />
          보고서 생성
        </Button>
      </PageHeader>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 감사 로그</p>
                <p className="text-2xl font-bold text-blue-600">{stats.totalLogs.toLocaleString()}</p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">고위험 이벤트</p>
                <p className="text-2xl font-bold text-red-600">{stats.highRiskEvents}</p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">컴플라이언스 위반</p>
                <p className="text-2xl font-bold text-orange-600">{stats.complianceViolations}</p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <FileText className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">보안 인시던트</p>
                <p className="text-2xl font-bold text-purple-600">{stats.securityIncidents}</p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <Settings className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 필터 및 검색 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="작업, 사용자명으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 위험 수준</option>
              <option value="low">낮음</option>
              <option value="medium">보통</option>
              <option value="high">높음</option>
              <option value="critical">위험</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* 탭 콘텐츠 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="logs">감사 로그</TabsTrigger>
          <TabsTrigger value="reports">컴플라이언스 보고서</TabsTrigger>
          <TabsTrigger value="security">보안 이벤트</TabsTrigger>
        </TabsList>

        <TabsContent value="logs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>감사 로그 ({filteredLogs.length}건)</CardTitle>
              <CardDescription>시스템 내 모든 사용자 활동 추적</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredLogs.map((log) => (
                  <div key={log.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getRiskColor(log.risk_level)}>
                            {log.risk_level.toUpperCase()}
                          </Badge>
                          <span className="font-medium">{log.action}</span>
                          <span className="text-sm text-gray-500">by {log.user_name}</span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          리소스: {log.resource}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>{formatDate(log.timestamp)}</span>
                          <span>IP: {log.ip_address}</span>
                          {log.compliance_flags.length > 0 && (
                            <span className="text-orange-600">
                              컴플라이언스 플래그: {log.compliance_flags.join(', ')}
                            </span>
                          )}
                        </div>
                      </div>
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        상세
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>컴플라이언스 보고서</CardTitle>
              <CardDescription>정기 및 특별 감사 보고서</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {reports.map((report) => (
                  <div key={report.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getStatusColor(report.status)}>
                            {report.status.toUpperCase()}
                          </Badge>
                          <span className="font-medium">{report.title}</span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          유형: {report.type.toUpperCase()} | 기간: {report.period}
                        </p>
                        <p className="text-sm text-gray-600 mb-2">
                          발견사항: {report.findings}건
                        </p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>생성일: {formatDate(report.generated_at)}</span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          보기
                        </Button>
                        {report.file_url && (
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            다운로드
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>보안 이벤트</CardTitle>
              <CardDescription>보안 관련 이벤트 및 인시던트</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {securityEvents.map((event) => (
                  <div key={event.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getSeverityColor(event.severity)}>
                            {event.severity.toUpperCase()}
                          </Badge>
                          <span className="font-medium">{event.type.replace('_', ' ').toUpperCase()}</span>
                          {event.resolved && (
                            <Badge className="bg-green-100 text-green-800">해결됨</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {event.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>{formatDate(event.timestamp)}</span>
                          <span>IP: {event.ip_address}</span>
                          {event.user_id && <span>사용자 ID: {event.user_id}</span>}
                          {event.assigned_to && <span>담당자: {event.assigned_to}</span>}
                        </div>
                      </div>
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        처리
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
