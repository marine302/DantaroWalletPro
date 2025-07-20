'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/common/PageHeader'
import { 
  Activity, 
  Check, 
  X, 
  AlertTriangle,
  RefreshCw,
  Server,
  Database
} from 'lucide-react'

interface HealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'error'
  message: string
  timestamp: string
  responseTime?: number
  version?: string
}

interface ApiTest {
  name: string
  path: string
  status: number
  ok: boolean
  responseTime: number
  message: string
}

interface EnvValidation {
  valid: boolean
  missing: string[]
  present: string[]
  optionalPresent: string[]
  values: Record<string, string | undefined>
}

interface HealthCheckManagementSectionProps {
  healthStatus: HealthCheckResult | null
  apiTests: ApiTest[]
  envValidation: EnvValidation | null
  isLoading: boolean
  onRunHealthCheck: () => void
  onRunApiTests: () => void
  onRefresh: () => void
}

export function HealthCheckManagementSection({
  healthStatus,
  apiTests,
  envValidation,
  isLoading,
  onRunHealthCheck,
  onRunApiTests,
  onRefresh
}: HealthCheckManagementSectionProps) {
  const [activeTab, setActiveTab] = useState('health')

  const getStatusColor = (status: string) => {
    const colors = {
      healthy: 'bg-green-100 text-green-800',
      unhealthy: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800'
    }
    return colors[status as keyof typeof colors] || colors.error
  }

  const getStatusIcon = (status: string) => {
    const icons = {
      healthy: <Check className="h-4 w-4" />,
      unhealthy: <AlertTriangle className="h-4 w-4" />,
      error: <X className="h-4 w-4" />
    }
    return icons[status as keyof typeof icons] || icons.error
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="시스템 상태 점검"
        description="백엔드 API, 환경 변수, 네트워크 연결 상태를 점검합니다"
      >
        <Button 
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          새로고침
        </Button>
      </PageHeader>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            헬스 체크
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            API 테스트
          </TabsTrigger>
          <TabsTrigger value="env" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            환경 변수
          </TabsTrigger>
        </TabsList>

        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                백엔드 헬스 체크
              </CardTitle>
              <CardDescription>
                백엔드 서버 상태를 확인합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button 
                  onClick={onRunHealthCheck}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? '점검 중...' : '헬스 체크 실행'}
                </Button>

                {healthStatus && (
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(healthStatus.status)}
                        <span className="font-medium">시스템 상태</span>
                      </div>
                      <Badge className={getStatusColor(healthStatus.status)}>
                        {healthStatus.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      {healthStatus.message}
                    </p>
                    <p className="text-xs text-gray-500">
                      마지막 점검: {new Date(healthStatus.timestamp).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                API 엔드포인트 테스트
              </CardTitle>
              <CardDescription>
                주요 API 엔드포인트의 응답 상태를 확인합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button 
                  onClick={onRunApiTests}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? '테스트 중...' : 'API 테스트 실행'}
                </Button>

                {apiTests.length > 0 && (
                  <div className="space-y-2">
                    {apiTests.map((test, index) => (
                      <div key={index} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{test.name}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant={test.ok ? 'success' : 'destructive'}>
                              {test.status}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {test.responseTime}ms
                            </span>
                          </div>
                        </div>
                        <div className="text-xs text-gray-600">
                          <code className="bg-gray-100 px-1 rounded">{test.path}</code>
                        </div>
                        {test.message && (
                          <p className="text-xs text-gray-500 mt-1">{test.message}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="env" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                환경 변수 검증
              </CardTitle>
              <CardDescription>
                필수 환경 변수가 올바르게 설정되었는지 확인합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              {envValidation && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    {envValidation.valid ? (
                      <Check className="h-5 w-5 text-green-600" />
                    ) : (
                      <X className="h-5 w-5 text-red-600" />
                    )}
                    <span className="font-medium">
                      환경 변수 상태: {envValidation.valid ? '정상' : '오류'}
                    </span>
                  </div>

                  {envValidation.missing.length > 0 && (
                    <div className="border border-red-200 rounded-lg p-3">
                      <h4 className="font-medium text-red-800 mb-2">누락된 환경 변수:</h4>
                      <ul className="text-sm text-red-600 list-disc list-inside">
                        {envValidation.missing.map((key) => (
                          <li key={key}><code>{key}</code></li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {envValidation.present.length > 0 && (
                    <div className="border border-green-200 rounded-lg p-3">
                      <h4 className="font-medium text-green-800 mb-2">설정된 필수 변수:</h4>
                      <ul className="text-sm text-green-600 list-disc list-inside">
                        {envValidation.present.map((key) => (
                          <li key={key}><code>{key}</code></li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {envValidation.optionalPresent.length > 0 && (
                    <div className="border border-blue-200 rounded-lg p-3">
                      <h4 className="font-medium text-blue-800 mb-2">설정된 선택적 변수:</h4>
                      <ul className="text-sm text-blue-600 list-disc list-inside">
                        {envValidation.optionalPresent.map((key) => (
                          <li key={key}><code>{key}</code></li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
