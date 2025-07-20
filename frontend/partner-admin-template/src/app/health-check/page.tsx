'use client'

import { useState, useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { HealthCheckManagementSection } from '@/components/health-check/HealthCheckManagementSection'
import { checkBackendHealth, testApiEndpoints, validateEnvironmentVariables, type HealthCheckResult } from '@/lib/health-check'

export default function HealthCheckPage() {
  const [healthStatus, setHealthStatus] = useState<HealthCheckResult | null>(null)
  const [apiTests, setApiTests] = useState<Array<{
    name: string
    path: string
    status: number
    ok: boolean
    responseTime: number
    message: string
  }>>([])
  const [envValidation, setEnvValidation] = useState<{
    valid: boolean
    missing: string[]
    present: string[]
    optionalPresent: string[]
    values: Record<string, string | undefined>
  } | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // 페이지 로드시 환경 변수 검증
    setEnvValidation(validateEnvironmentVariables())
  }, [])

  const runHealthCheck = async () => {
    setIsLoading(true)
    try {
      const health = await checkBackendHealth()
      setHealthStatus(health)
    } catch (error) {
      console.error('Health check failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const runApiTests = async () => {
    setIsLoading(true)
    try {
      const tests = await testApiEndpoints()
      setApiTests(tests)
    } catch (error) {
      console.error('API tests failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefresh = () => {
    setEnvValidation(validateEnvironmentVariables())
    runHealthCheck()
    runApiTests()
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <HealthCheckManagementSection
          healthStatus={healthStatus}
          apiTests={apiTests}
          envValidation={envValidation}
          isLoading={isLoading}
          onRunHealthCheck={runHealthCheck}
          onRunApiTests={runApiTests}
          onRefresh={handleRefresh}
        />
      </div>
    </Sidebar>
  )
}
