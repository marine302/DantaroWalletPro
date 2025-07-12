'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { EnergyRentalWidget } from './EnergyRentalWidget'
import { RealtimeEnergyMonitor } from './RealtimeEnergyMonitor'
import { Settings, CreditCard, BarChart3, Users, Bell, Shield } from 'lucide-react'

interface EnergyRentalManagementProps {
  className?: string
}

export function EnergyRentalManagement({ className }: EnergyRentalManagementProps) {
  const [notifications, setNotifications] = useState({
    usage_alerts: true,
    cost_threshold: true,
    efficiency_warnings: true,
    plan_recommendations: false
  })

  const [planSettings, setPlanSettings] = useState({
    auto_upgrade: false,
    cost_limit: 500,
    usage_threshold: 80
  })

  const plans = [
    {
      id: 'basic',
      name: 'Basic',
      monthly_quota: 500000,
      price: 150,
      features: ['기본 에너지 할당', '월 단위 정산', '기본 모니터링']
    },
    {
      id: 'standard',
      name: 'Standard',
      monthly_quota: 1000000,
      price: 280,
      features: ['확장 에너지 할당', '실시간 모니터링', '비용 최적화', '우선 지원']
    },
    {
      id: 'premium',
      name: 'Premium',
      monthly_quota: 2500000,
      price: 650,
      features: ['무제한 에너지*', '고급 분석', 'AI 최적화', '전담 지원', '커스텀 정책']
    }
  ]

  const currentPlan = 'standard'

  return (
    <div className={className}>
      <div className="space-y-6">
        {/* 헤더 */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">에너지 렌탈 관리</h1>
            <p className="text-muted-foreground">
              에너지 사용량을 모니터링하고 렌탈 플랜을 관리하세요
            </p>
          </div>
          <Button>
            <Settings className="w-4 h-4 mr-2" />
            고급 설정
          </Button>
        </div>

        {/* 메인 위젯들 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EnergyRentalWidget />
          <RealtimeEnergyMonitor />
        </div>

        {/* 탭 기반 상세 관리 */}
        <Tabs defaultValue="plans" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="plans">플랜 관리</TabsTrigger>
            <TabsTrigger value="usage">사용량 분석</TabsTrigger>
            <TabsTrigger value="billing">요금 정보</TabsTrigger>
            <TabsTrigger value="settings">설정</TabsTrigger>
          </TabsList>

          {/* 플랜 관리 탭 */}
          <TabsContent value="plans" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  구독 플랜 선택
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {plans.map((plan) => (
                    <Card 
                      key={plan.id} 
                      className={`relative ${currentPlan === plan.id ? 'ring-2 ring-primary' : ''}`}
                    >
                      <CardHeader className="text-center">
                        <div className="flex justify-between items-start">
                          <CardTitle className="text-lg">{plan.name}</CardTitle>
                          {currentPlan === plan.id && (
                            <Badge>현재 플랜</Badge>
                          )}
                        </div>
                        <div className="space-y-1">
                          <div className="text-3xl font-bold">${plan.price}</div>
                          <div className="text-sm text-muted-foreground">월간</div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="text-center">
                          <div className="text-lg font-semibold">
                            {(plan.monthly_quota / 1000000).toFixed(1)}M 에너지
                          </div>
                          <div className="text-sm text-muted-foreground">월 할당량</div>
                        </div>
                        
                        <ul className="space-y-2 text-sm">
                          {plan.features.map((feature, idx) => (
                            <li key={idx} className="flex items-center gap-2">
                              <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                        
                        <Button 
                          className="w-full" 
                          variant={currentPlan === plan.id ? 'outline' : 'default'}
                          disabled={currentPlan === plan.id}
                        >
                          {currentPlan === plan.id ? '현재 사용 중' : '플랜 변경'}
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 사용량 분석 탭 */}
          <TabsContent value="usage" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">오늘 사용량</p>
                      <p className="text-2xl font-bold">21,500</p>
                    </div>
                    <BarChart3 className="w-8 h-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">이번 주</p>
                      <p className="text-2xl font-bold">145,200</p>
                    </div>
                    <BarChart3 className="w-8 h-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">이번 달</p>
                      <p className="text-2xl font-bold">650,000</p>
                    </div>
                    <BarChart3 className="w-8 h-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">효율성</p>
                      <p className="text-2xl font-bold">85.5%</p>
                    </div>
                    <Users className="w-8 h-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 요금 정보 탭 */}
          <TabsContent value="billing" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>이번 달 요금 내역</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b">
                  <span>기본 구독료 (Standard)</span>
                  <span className="font-medium">$280.00</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span>추가 사용량 (150,000 에너지)</span>
                  <span className="font-medium">$63.00</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span>효율성 보너스 (-5%)</span>
                  <span className="font-medium text-green-600">-$17.15</span>
                </div>
                <div className="flex justify-between items-center py-2 font-semibold text-lg">
                  <span>총 예상 요금</span>
                  <span>$325.85</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 설정 탭 */}
          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="w-5 h-5" />
                  알림 설정
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-sm font-medium">사용량 알림</label>
                    <p className="text-xs text-muted-foreground">
                      에너지 사용량이 임계값을 초과할 때 알림을 받습니다.
                    </p>
                  </div>
                  <Switch 
                    checked={notifications.usage_alerts}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, usage_alerts: checked }))
                    }
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-sm font-medium">비용 임계값 알림</label>
                    <p className="text-xs text-muted-foreground">
                      월 비용이 설정된 금액을 초과할 때 알림을 받습니다.
                    </p>
                  </div>
                  <Switch 
                    checked={notifications.cost_threshold}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, cost_threshold: checked }))
                    }
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-sm font-medium">효율성 경고</label>
                    <p className="text-xs text-muted-foreground">
                      에너지 사용 효율성이 낮을 때 개선 방안을 제안합니다.
                    </p>
                  </div>
                  <Switch 
                    checked={notifications.efficiency_warnings}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, efficiency_warnings: checked }))
                    }
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-sm font-medium">플랜 추천</label>
                    <p className="text-xs text-muted-foreground">
                      사용 패턴에 따른 최적 플랜을 추천받습니다.
                    </p>
                  </div>
                  <Switch 
                    checked={notifications.plan_recommendations}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, plan_recommendations: checked }))
                    }
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  자동화 설정
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-sm font-medium">자동 플랜 업그레이드</label>
                    <p className="text-xs text-muted-foreground">
                      사용량이 지속적으로 한도를 초과할 때 자동으로 플랜을 업그레이드합니다.
                    </p>
                  </div>
                  <Switch 
                    checked={planSettings.auto_upgrade}
                    onCheckedChange={(checked: boolean) => 
                      setPlanSettings(prev => ({ ...prev, auto_upgrade: checked }))
                    }
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default EnergyRentalManagement
