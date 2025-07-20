'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Shield, 
  Zap,
  Target,
  BookOpen,
  Settings,
  ChevronRight,
  Play,
  RotateCcw,
  Users,
  TrendingUp,
  FileText
} from 'lucide-react'
import { useOnboardingProgress, useOnboardingSteps, useCompleteOnboardingStep } from '@/lib/hooks'

// 온보딩 단계 타입 정의
interface OnboardingStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  progress: number
  estimated_time: string
  required: boolean
  category: 'setup' | 'verification' | 'integration' | 'testing'
  details: {
    checklist: string[]
    resources: { title: string; url: string; type: 'doc' | 'video' | 'guide' }[]
    automated: boolean
  }
}

interface OnboardingProgress {
  overall_progress: number
  completed_steps: number
  total_steps: number
  estimated_completion: string
  current_step: string
  blockers: string[]
}

export default function OnboardingPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  
  // API 훅 사용
  const { data: progressData, isLoading: progressLoading } = useOnboardingProgress()
  const { data: stepsData, isLoading: stepsLoading } = useOnboardingSteps()
  const completeStepMutation = useCompleteOnboardingStep()

  // 폴백 데이터
  const fallbackProgress: OnboardingProgress = {
    overall_progress: 78,
    completed_steps: 14,
    total_steps: 18,
    estimated_completion: '2일 후',
    current_step: 'wallet_integration',
    blockers: ['KYC 문서 검토 대기', 'API 키 승인 필요']
  }

  const fallbackSteps: OnboardingStep[] = [
    {
      id: 'account_setup',
      title: '계정 설정 완료',
      description: '기본 파트너 계정 정보 및 프로필 설정',
      status: 'completed',
      progress: 100,
      estimated_time: '5분',
      required: true,
      category: 'setup',
      details: {
        checklist: ['프로필 정보 입력', '연락처 확인', '초기 비밀번호 설정'],
        resources: [
          { title: '계정 설정 가이드', url: '/docs/account-setup', type: 'doc' },
          { title: '보안 설정 방법', url: '/docs/security', type: 'guide' }
        ],
        automated: false
      }
    },
    {
      id: 'kyc_verification',
      title: 'KYC 인증',
      description: '신원 확인 및 사업자 등록증 검토',
      status: 'in_progress',
      progress: 60,
      estimated_time: '1-2일',
      required: true,
      category: 'verification',
      details: {
        checklist: [
          '신분증 업로드 완료',
          '사업자 등록증 업로드 완료',
          '법인 통장 사본 대기',
          '관리자 검토 대기'
        ],
        resources: [
          { title: 'KYC 가이드라인', url: '/docs/kyc', type: 'doc' },
          { title: 'KYC 절차 영상', url: '/videos/kyc-process', type: 'video' }
        ],
        automated: true
      }
    },
    {
      id: 'wallet_integration',
      title: '지갑 연동',
      description: 'TronLink 지갑 연동 및 테스트',
      status: 'in_progress',
      progress: 80,
      estimated_time: '30분',
      required: true,
      category: 'integration',
      details: {
        checklist: [
          'TronLink 지갑 설치 완료',
          '테스트넷 연결 확인',
          '기본 거래 테스트 완료',
          '메인넷 연결 대기'
        ],
        resources: [
          { title: 'TronLink 연동 가이드', url: '/docs/tronlink', type: 'doc' },
          { title: '지갑 테스트 방법', url: '/docs/wallet-test', type: 'guide' }
        ],
        automated: false
      }
    },
    {
      id: 'api_integration',
      title: 'API 연동',
      description: '백엔드 API 키 발급 및 연동 테스트',
      status: 'pending',
      progress: 25,
      estimated_time: '1시간',
      required: true,
      category: 'integration',
      details: {
        checklist: [
          'API 키 신청 완료',
          'API 키 승인 대기',
          '테스트 API 호출',
          '프로덕션 환경 설정'
        ],
        resources: [
          { title: 'API 문서', url: '/docs/api', type: 'doc' },
          { title: 'API 연동 예제', url: '/docs/api-examples', type: 'guide' }
        ],
        automated: true
      }
    },
    {
      id: 'energy_setup',
      title: '에너지 관리 설정',
      description: '에너지 풀 설정 및 렌탈 서비스 활성화',
      status: 'pending',
      progress: 0,
      estimated_time: '45분',
      required: false,
      category: 'setup',
      details: {
        checklist: [
          '에너지 풀 생성',
          '스테이킹 설정',
          '렌탈 정책 구성',
          '모니터링 설정'
        ],
        resources: [
          { title: '에너지 관리 가이드', url: '/docs/energy', type: 'doc' },
          { title: '에너지 렌탈 설정', url: '/docs/energy-rental', type: 'guide' }
        ],
        automated: false
      }
    },
    {
      id: 'testing_phase',
      title: '통합 테스트',
      description: '모든 기능의 종합 테스트 수행',
      status: 'pending',
      progress: 0,
      estimated_time: '2시간',
      required: true,
      category: 'testing',
      details: {
        checklist: [
          '지갑 연동 테스트',
          '출금 프로세스 테스트',
          '에너지 관리 테스트',
          '대시보드 기능 테스트'
        ],
        resources: [
          { title: '테스트 체크리스트', url: '/docs/testing', type: 'doc' },
          { title: '테스트 시나리오', url: '/docs/test-scenarios', type: 'guide' }
        ],
        automated: true
      }
    }
  ]

  // 실제 API 데이터와 폴백 데이터 병합
  const progress = (progressData as OnboardingProgress | undefined) || fallbackProgress
  const steps = (stepsData as { steps?: OnboardingStep[] })?.steps || fallbackSteps

  // 카테고리별 필터링
  const filteredSteps = selectedCategory === 'all' 
    ? steps 
    : steps.filter(step => step.category === selectedCategory)

  const handleCompleteStep = async (stepId: string) => {
    try {
      await completeStepMutation.mutateAsync({ stepId })
    } catch (error) {
      console.error('단계 완료 실패:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'in_progress': return <Clock className="w-5 h-5 text-blue-500" />
      case 'pending': return <AlertCircle className="w-5 h-5 text-gray-400" />
      default: return <AlertCircle className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string, required: boolean) => {
    const variant = status === 'completed' ? 'default' : 
                   status === 'in_progress' ? 'secondary' : 'outline'
    const text = status === 'completed' ? '완료' :
                 status === 'in_progress' ? '진행중' : '대기'
    
    return (
      <div className="flex items-center space-x-2">
        <Badge variant={variant}>{text}</Badge>
        {required && <Badge variant="destructive" className="text-xs">필수</Badge>}
      </div>
    )
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'setup': return <Settings className="w-4 h-4" />
      case 'verification': return <Shield className="w-4 h-4" />
      case 'integration': return <Zap className="w-4 h-4" />
      case 'testing': return <Target className="w-4 h-4" />
      default: return <BookOpen className="w-4 h-4" />
    }
  }

  if (progressLoading || stepsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <RotateCcw className="h-6 w-6 animate-spin" />
          <span className="text-lg">온보딩 정보를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  return (
    <Sidebar>
      <div className="flex h-screen bg-background">      
        <main className="flex-1 p-8 overflow-auto">
          <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">파트너 온보딩</h1>
                <p className="text-muted-foreground">
                  Doc-29: 자동화된 온보딩 프로세스를 통해 빠르고 안전하게 시작하세요
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-primary">{progress.overall_progress}%</div>
                <div className="text-sm text-muted-foreground">전체 진행률</div>
              </div>
            </div>
          </div>

          {/* 진행률 개요 */}
          <div className="grid gap-6 md:grid-cols-4 mb-8">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{progress.completed_steps}/{progress.total_steps}</div>
                    <div className="text-sm text-muted-foreground">완료된 단계</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Clock className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{progress.estimated_completion}</div>
                    <div className="text-sm text-muted-foreground">완료 예상</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Users className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{progress.blockers.length}</div>
                    <div className="text-sm text-muted-foreground">대기 항목</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Target className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{steps.filter(s => s.status === 'in_progress').length}</div>
                    <div className="text-sm text-muted-foreground">진행중</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 전체 진행률 바 */}
          <Card className="mb-8">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">전체 온보딩 진행률</h3>
                <span className="text-sm text-muted-foreground">
                  현재: {steps.find(s => s.id === progress.current_step)?.title || '알 수 없음'}
                </span>
              </div>
              <Progress value={progress.overall_progress} className="w-full h-3" />
              
              {progress.blockers.length > 0 && (
                <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <h4 className="font-medium text-orange-800 mb-2">대기 중인 항목</h4>
                  <ul className="space-y-1">
                    {progress.blockers.map((blocker, index) => (
                      <li key={index} className="text-sm text-orange-700 flex items-center">
                        <AlertCircle className="w-4 h-4 mr-2" />
                        {blocker}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 탭 및 필터 */}
          <Tabs defaultValue="steps" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="steps">온보딩 단계</TabsTrigger>
              <TabsTrigger value="resources">리소스 & 가이드</TabsTrigger>
            </TabsList>

            {/* 온보딩 단계 탭 */}
            <TabsContent value="steps" className="space-y-6">
              {/* 카테고리 필터 */}
              <div className="flex space-x-2 mb-6">
                <Button 
                  variant={selectedCategory === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory('all')}
                >
                  전체
                </Button>
                <Button 
                  variant={selectedCategory === 'setup' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory('setup')}
                  className="flex items-center space-x-1"
                >
                  <Settings className="w-4 h-4" />
                  <span>설정</span>
                </Button>
                <Button 
                  variant={selectedCategory === 'verification' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory('verification')}
                  className="flex items-center space-x-1"
                >
                  <Shield className="w-4 h-4" />
                  <span>인증</span>
                </Button>
                <Button 
                  variant={selectedCategory === 'integration' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory('integration')}
                  className="flex items-center space-x-1"
                >
                  <Zap className="w-4 h-4" />
                  <span>연동</span>
                </Button>
                <Button 
                  variant={selectedCategory === 'testing' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory('testing')}
                  className="flex items-center space-x-1"
                >
                  <Target className="w-4 h-4" />
                  <span>테스트</span>
                </Button>
              </div>

              {/* 단계 목록 */}
              <div className="space-y-4">
                {filteredSteps.map((step) => (
                  <Card key={step.id}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-3">
                            {getStatusIcon(step.status)}
                            <div className="flex items-center space-x-2">
                              {getCategoryIcon(step.category)}
                              <h3 className="text-lg font-semibold">{step.title}</h3>
                            </div>
                            {getStatusBadge(step.status, step.required)}
                          </div>
                          
                          <p className="text-muted-foreground mb-4">{step.description}</p>
                          
                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium">진행률</span>
                              <span className="text-sm text-muted-foreground">
                                {step.progress}% • 예상 시간: {step.estimated_time}
                              </span>
                            </div>
                            <Progress value={step.progress} className="w-full" />
                          </div>                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <h4 className="font-medium mb-2">체크리스트</h4>
                          <ul className="space-y-1">
                            {step.details.checklist.map((item, idx) => (
                              <li key={idx} className="text-sm flex items-center">
                                <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">참고 자료</h4>
                          <ul className="space-y-1">
                            {step.details.resources.map((resource, idx) => (
                              <li key={idx} className="text-sm">
                                <a 
                                  href={resource.url} 
                                  className="flex items-center text-blue-600 hover:text-blue-800"
                                >
                                  <FileText className="w-3 h-3 mr-2" />
                                  {resource.title}
                                  <ChevronRight className="w-3 h-3 ml-1" />
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                        </div>

                        <div className="ml-6 flex flex-col space-y-2">
                          {step.status === 'in_progress' && (
                            <Button 
                              size="sm"
                              onClick={() => handleCompleteStep(step.id)}
                              disabled={completeStepMutation.isPending}
                            >
                              {completeStepMutation.isPending ? (
                                <RotateCcw className="w-4 h-4 animate-spin" />
                              ) : (
                                <CheckCircle className="w-4 h-4" />
                              )}
                              완료 처리
                            </Button>
                          )}
                          
                          {step.status === 'pending' && (
                            <Button variant="outline" size="sm">
                              <Play className="w-4 h-4" />
                              시작하기
                            </Button>
                          )}

                          {step.details.automated && (
                            <Badge variant="secondary" className="text-xs">
                              자동화
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* 리소스 탭 */}
            <TabsContent value="resources" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="w-5 h-5" />
                    참고 문서 및 가이드
                  </CardTitle>
                  <CardDescription>
                    온보딩 과정에서 도움이 되는 모든 리소스를 한곳에서 확인하세요
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>리소스 라이브러리가 여기에 표시됩니다</p>
                    <p className="text-sm">(문서 시스템 연동 후 활성화)</p>
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
