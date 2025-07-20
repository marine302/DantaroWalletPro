'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Settings, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  DollarSign,
  Users,
  Target,
  Save,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { useWithdrawalPolicies } from '@/lib/hooks'

// 출금 정책 타입 정의
interface WithdrawalPolicy {
  id: string
  name: string
  description: string
  enabled: boolean
  min_amount: number
  max_amount: number
  daily_limit: number
  monthly_limit: number
  auto_approval_threshold: number
  require_admin_approval: boolean
  whitelist_enabled: boolean
  blacklist_enabled: boolean
  created_at: string
  updated_at: string
}

interface AutoApprovalRule {
  id: string
  name: string
  condition: string
  threshold: number
  enabled: boolean
  priority: number
}

export default function WithdrawalPolicyPage() {
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  // API 훅 사용
  const { data: policiesData, isLoading, error } = useWithdrawalPolicies()

  // 폴백 데이터
  const fallbackPolicies: WithdrawalPolicy[] = [
    {
      id: 'default',
      name: '기본 출금 정책',
      description: '일반 사용자를 위한 기본 출금 정책',
      enabled: true,
      min_amount: 10,
      max_amount: 10000,
      daily_limit: 50000,
      monthly_limit: 1000000,
      auto_approval_threshold: 500,
      require_admin_approval: false,
      whitelist_enabled: true,
      blacklist_enabled: true,
      created_at: '2025-01-15T09:00:00Z',
      updated_at: '2025-07-20T10:30:00Z'
    },
    {
      id: 'vip',
      name: 'VIP 출금 정책',
      description: 'VIP 회원을 위한 고급 출금 정책',
      enabled: true,
      min_amount: 1,
      max_amount: 100000,
      daily_limit: 500000,
      monthly_limit: 10000000,
      auto_approval_threshold: 5000,
      require_admin_approval: false,
      whitelist_enabled: false,
      blacklist_enabled: true,
      created_at: '2025-01-20T14:00:00Z',
      updated_at: '2025-07-20T10:30:00Z'
    }
  ]

  const fallbackRules: AutoApprovalRule[] = [
    {
      id: 'small_amount',
      name: '소액 자동 승인',
      condition: 'amount < 500 AND user_verified = true',
      threshold: 500,
      enabled: true,
      priority: 1
    },
    {
      id: 'trusted_user',
      name: '신뢰 사용자 자동 승인',
      condition: 'user_trust_score > 90 AND withdrawal_count > 10',
      threshold: 2000,
      enabled: true,
      priority: 2
    },
    {
      id: 'whitelist_address',
      name: '화이트리스트 주소 자동 승인',
      condition: 'destination_address IN whitelist',
      threshold: 10000,
      enabled: true,
      priority: 3
    }
  ]

  // 실제 API 데이터와 폴백 데이터 병합
  const policies = (policiesData as { policies?: WithdrawalPolicy[] })?.policies || fallbackPolicies
  const rules = (policiesData as { auto_approval_rules?: AutoApprovalRule[] })?.auto_approval_rules || fallbackRules

  const getPolicyStatusBadge = (policy: WithdrawalPolicy) => {
    if (!policy.enabled) {
      return <Badge variant="secondary">비활성</Badge>
    }
    if (policy.require_admin_approval) {
      return <Badge variant="destructive">수동 승인</Badge>
    }
    return <Badge variant="default">자동 승인</Badge>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span className="text-lg">출금 정책을 불러오는 중...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">정책 로드 실패</h2>
          <p className="text-muted-foreground">출금 정책을 불러올 수 없습니다. 다시 시도해주세요.</p>
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
                <h1 className="text-3xl font-bold text-foreground mb-2">출금 정책 관리</h1>
                <p className="text-muted-foreground">
                  Doc-28: 자동 출금 정책 및 승인 규칙을 설정하고 관리합니다
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center space-x-2"
                >
                  {showAdvanced ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span>{showAdvanced ? '간단히 보기' : '고급 설정'}</span>
                </Button>
                <Button className="flex items-center space-x-2">
                  <Save className="w-4 h-4" />
                  <span>변경사항 저장</span>
                </Button>
              </div>
            </div>
          </div>

          <Tabs defaultValue="policies" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="policies">출금 정책</TabsTrigger>
              <TabsTrigger value="rules">자동 승인 규칙</TabsTrigger>
              <TabsTrigger value="monitoring">실시간 모니터링</TabsTrigger>
            </TabsList>

            {/* 출금 정책 탭 */}
            <TabsContent value="policies" className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                {policies.map((policy) => (
                  <Card key={policy.id} className="text-foreground">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <Settings className="w-5 h-5" />
                            {policy.name}
                          </CardTitle>
                          <CardDescription>{policy.description}</CardDescription>
                        </div>
                        {getPolicyStatusBadge(policy)}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* 기본 설정 */}
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <label className="text-sm font-medium">최소 출금액</label>
                          <div className="flex items-center space-x-2">
                            <DollarSign className="w-4 h-4 text-muted-foreground" />
                            <Input 
                              type="number" 
                              defaultValue={policy.min_amount}
                              className="flex-1"
                            />
                          </div>
                        </div>
                        <div>
                          <label className="text-sm font-medium">최대 출금액</label>
                          <div className="flex items-center space-x-2">
                            <DollarSign className="w-4 h-4 text-muted-foreground" />
                            <Input 
                              type="number" 
                              defaultValue={policy.max_amount}
                              className="flex-1"
                            />
                          </div>
                        </div>
                      </div>

                      {/* 한도 설정 */}
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <label className="text-sm font-medium">일일 한도</label>
                          <div className="flex items-center space-x-2">
                            <Clock className="w-4 h-4 text-muted-foreground" />
                            <Input 
                              type="number" 
                              defaultValue={policy.daily_limit}
                              className="flex-1"
                            />
                          </div>
                        </div>
                        <div>
                          <label className="text-sm font-medium">월간 한도</label>
                          <div className="flex items-center space-x-2">
                            <Target className="w-4 h-4 text-muted-foreground" />
                            <Input 
                              type="number" 
                              defaultValue={policy.monthly_limit}
                              className="flex-1"
                            />
                          </div>
                        </div>
                      </div>

                      {/* 자동 승인 설정 */}
                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between mb-3">
                          <label className="text-sm font-medium">자동 승인 임계값</label>
                          <span className="text-sm text-muted-foreground">
                            {formatCurrency(policy.auto_approval_threshold, 'USDT')}
                          </span>
                        </div>
                        <Input 
                          type="number" 
                          defaultValue={policy.auto_approval_threshold}
                        />
                      </div>

                      {/* 스위치 설정들 */}
                      <div className="space-y-3 border-t pt-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <Shield className="w-4 h-4" />
                            <label className="text-sm font-medium">관리자 승인 필요</label>
                          </div>
                          <Switch defaultChecked={policy.require_admin_approval} />
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4" />
                            <label className="text-sm font-medium">화이트리스트 활성화</label>
                          </div>
                          <Switch defaultChecked={policy.whitelist_enabled} />
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4" />
                            <label className="text-sm font-medium">블랙리스트 활성화</label>
                          </div>
                          <Switch defaultChecked={policy.blacklist_enabled} />
                        </div>
                      </div>

                      {/* 고급 설정 (조건부 표시) */}
                      {showAdvanced && (
                        <div className="border-t pt-4 space-y-3">
                          <h4 className="font-medium text-sm">고급 설정</h4>
                          <div className="grid gap-2 text-xs text-muted-foreground">
                            <div>생성일: {new Date(policy.created_at).toLocaleString()}</div>
                            <div>수정일: {new Date(policy.updated_at).toLocaleString()}</div>
                            <div>정책 ID: {policy.id}</div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* 자동 승인 규칙 탭 */}
            <TabsContent value="rules" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    자동 승인 규칙 엔진
                  </CardTitle>
                  <CardDescription>
                    조건에 따른 자동 승인 규칙을 설정합니다. 우선순위가 높은 규칙부터 순서대로 평가됩니다.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {rules.map((rule) => (
                      <div key={rule.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <Badge variant="outline">#{rule.priority}</Badge>
                            <h4 className="font-medium">{rule.name}</h4>
                          </div>
                          <Switch defaultChecked={rule.enabled} />
                        </div>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">조건</label>
                            <p className="text-sm font-mono bg-muted p-2 rounded mt-1">
                              {rule.condition}
                            </p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">임계값</label>
                            <div className="flex items-center space-x-2 mt-1">
                              <DollarSign className="w-4 h-4 text-muted-foreground" />
                              <Input 
                                type="number" 
                                defaultValue={rule.threshold}
                                className="flex-1"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 실시간 모니터링 탭 */}
            <TabsContent value="monitoring" className="space-y-6">
              <div className="grid gap-6 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <Users className="w-4 h-4" />
                      오늘 처리된 출금
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">1,247</div>
                    <p className="text-xs text-muted-foreground">+12% vs 어제</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      자동 승인률
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">87.3%</div>
                    <p className="text-xs text-muted-foreground">+2.1% vs 어제</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <DollarSign className="w-4 h-4 text-blue-500" />
                      처리 금액
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">$2.4M</div>
                    <p className="text-xs text-muted-foreground">+5.7% vs 어제</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>정책 효과성 분석</CardTitle>
                  <CardDescription>
                    각 정책별 성능 지표를 실시간으로 모니터링합니다
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>실시간 차트가 여기에 표시됩니다</p>
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
