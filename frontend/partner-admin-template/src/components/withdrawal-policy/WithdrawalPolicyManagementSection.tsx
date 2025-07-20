'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/common/PageHeader'
import { 
  Settings, 
  Shield, 
  CheckCircle, 
  Clock,
  DollarSign,
  Target,
  Save,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react'

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

interface WithdrawalPolicyManagementSectionProps {
  policies: WithdrawalPolicy[]
  rules: AutoApprovalRule[]
  showAdvanced: boolean
  onToggleAdvanced: () => void
  onUpdatePolicy: (policyId: string, updates: Partial<WithdrawalPolicy>) => void
  onUpdateRule: (ruleId: string, updates: Partial<AutoApprovalRule>) => void
  onSave: () => void
  onRefresh: () => void
}

export function WithdrawalPolicyManagementSection({
  policies,
  rules,
  showAdvanced,
  onToggleAdvanced,
  onUpdatePolicy,
  onUpdateRule,
  onSave,
  onRefresh
}: WithdrawalPolicyManagementSectionProps) {
  const [activeTab, setActiveTab] = useState('policies')

  const getStatusColor = (enabled: boolean) => {
    return enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="출금 정책 관리"
        description="사용자 그룹별 출금 한도 및 승인 정책을 설정합니다"
      >
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={onToggleAdvanced}
            className="flex items-center gap-2"
          >
            {showAdvanced ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            {showAdvanced ? '기본 설정' : '고급 설정'}
          </Button>
          <Button 
            onClick={onRefresh}
            variant="outline"
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            새로고침
          </Button>
          <Button 
            onClick={onSave}
            className="flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            저장
          </Button>
        </div>
      </PageHeader>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="policies" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            정책 설정
          </TabsTrigger>
          <TabsTrigger value="rules" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            자동 승인 규칙
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            모니터링
          </TabsTrigger>
        </TabsList>

        <TabsContent value="policies" className="space-y-4">
          {policies.map((policy) => (
            <Card key={policy.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {policy.name}
                      <Badge className={getStatusColor(policy.enabled)}>
                        {policy.enabled ? '활성' : '비활성'}
                      </Badge>
                    </CardTitle>
                    <CardDescription>{policy.description}</CardDescription>
                  </div>
                  <Switch
                    checked={policy.enabled}
                    onCheckedChange={(enabled) => 
                      onUpdatePolicy(policy.id, { enabled })
                    }
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">최소 출금 금액</label>
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-gray-500" />
                      <Input
                        type="number"
                        value={policy.min_amount}
                        onChange={(e) => 
                          onUpdatePolicy(policy.id, { min_amount: Number(e.target.value) })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">최대 출금 금액</label>
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-gray-500" />
                      <Input
                        type="number"
                        value={policy.max_amount}
                        onChange={(e) => 
                          onUpdatePolicy(policy.id, { max_amount: Number(e.target.value) })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">일일 한도</label>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <Input
                        type="number"
                        value={policy.daily_limit}
                        onChange={(e) => 
                          onUpdatePolicy(policy.id, { daily_limit: Number(e.target.value) })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">월 한도</label>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <Input
                        type="number"
                        value={policy.monthly_limit}
                        onChange={(e) => 
                          onUpdatePolicy(policy.id, { monthly_limit: Number(e.target.value) })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">자동 승인 임계값</label>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-gray-500" />
                      <Input
                        type="number"
                        value={policy.auto_approval_threshold}
                        onChange={(e) => 
                          onUpdatePolicy(policy.id, { auto_approval_threshold: Number(e.target.value) })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>

                  {showAdvanced && (
                    <>
                      <div className="space-y-2">
                        <label className="text-sm font-medium flex items-center gap-2">
                          <Switch
                            checked={policy.require_admin_approval}
                            onCheckedChange={(require_admin_approval) => 
                              onUpdatePolicy(policy.id, { require_admin_approval })
                            }
                          />
                          관리자 승인 필요
                        </label>
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium flex items-center gap-2">
                          <Switch
                            checked={policy.whitelist_enabled}
                            onCheckedChange={(whitelist_enabled) => 
                              onUpdatePolicy(policy.id, { whitelist_enabled })
                            }
                          />
                          화이트리스트 사용
                        </label>
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium flex items-center gap-2">
                          <Switch
                            checked={policy.blacklist_enabled}
                            onCheckedChange={(blacklist_enabled) => 
                              onUpdatePolicy(policy.id, { blacklist_enabled })
                            }
                          />
                          블랙리스트 사용
                        </label>
                      </div>
                    </>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t text-sm text-gray-500">
                  <div className="grid grid-cols-2 gap-4">
                    <div>생성일: {new Date(policy.created_at).toLocaleDateString()}</div>
                    <div>수정일: {new Date(policy.updated_at).toLocaleDateString()}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                자동 승인 규칙
              </CardTitle>
              <CardDescription>
                특정 조건을 만족하는 출금 요청을 자동으로 승인하는 규칙을 설정합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {rules.map((rule) => (
                  <div key={rule.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-medium">{rule.name}</h4>
                        <p className="text-sm text-gray-600">{rule.condition}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">우선순위: {rule.priority}</Badge>
                        <Switch
                          checked={rule.enabled}
                          onCheckedChange={(enabled) => 
                            onUpdateRule(rule.id, { enabled })
                          }
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">임계값</label>
                        <Input
                          type="number"
                          value={rule.threshold}
                          onChange={(e) => 
                            onUpdateRule(rule.id, { threshold: Number(e.target.value) })
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">우선순위</label>
                        <Input
                          type="number"
                          value={rule.priority}
                          onChange={(e) => 
                            onUpdateRule(rule.id, { priority: Number(e.target.value) })
                          }
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                정책 적용 현황
              </CardTitle>
              <CardDescription>
                현재 적용 중인 출금 정책의 효과를 모니터링합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">87%</div>
                  <div className="text-sm text-gray-600">자동 승인률</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">13%</div>
                  <div className="text-sm text-gray-600">수동 검토율</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-red-600">0.1%</div>
                  <div className="text-sm text-gray-600">거부율</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>최근 정책 변경 이력</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { time: '2시간 전', action: 'VIP 정책 일일 한도 증가', user: '관리자' },
                  { time: '1일 전', action: '기본 정책 자동승인 임계값 변경', user: '관리자' },
                  { time: '3일 전', action: '새 자동승인 규칙 추가', user: '시스템' }
                ].map((log, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">{log.action}</div>
                      <div className="text-sm text-gray-600">{log.time}</div>
                    </div>
                    <Badge variant="outline">{log.user}</Badge>
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
