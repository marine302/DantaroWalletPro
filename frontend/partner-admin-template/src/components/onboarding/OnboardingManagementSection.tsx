'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/common/PageHeader'
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Shield, 
  Zap,
  Target,
  BookOpen,
  Settings,
  Play,
  RotateCcw,
  TrendingUp,
  FileText
} from 'lucide-react'

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

interface OnboardingManagementSectionProps {
  progress: OnboardingProgress
  steps: OnboardingStep[]
  selectedCategory: string
  onCategoryChange: (category: string) => void
  onCompleteStep: (stepId: string) => void
  onSkipStep: (stepId: string) => void
  onRefresh: () => void
}

export function OnboardingManagementSection({
  progress,
  steps,
  selectedCategory,
  onCategoryChange,
  onCompleteStep,
  onSkipStep,
  onRefresh
}: OnboardingManagementSectionProps) {
  const [activeTab, setActiveTab] = useState('overview')

  const getStatusIcon = (status: string) => {
    const icons = {
      completed: <CheckCircle className="h-5 w-5 text-green-600" />,
      in_progress: <Clock className="h-5 w-5 text-blue-600" />,
      pending: <AlertCircle className="h-5 w-5 text-gray-400" />,
      skipped: <AlertCircle className="h-5 w-5 text-yellow-600" />
    }
    return icons[status as keyof typeof icons] || icons.pending
  }

  const getStatusColor = (status: string) => {
    const colors = {
      completed: 'bg-green-100 text-green-800',
      in_progress: 'bg-blue-100 text-blue-800',
      pending: 'bg-gray-100 text-gray-800',
      skipped: 'bg-yellow-100 text-yellow-800'
    }
    return colors[status as keyof typeof colors] || colors.pending
  }

  const getCategoryIcon = (category: string) => {
    const icons = {
      setup: <Settings className="h-5 w-5" />,
      verification: <Shield className="h-5 w-5" />,
      integration: <Zap className="h-5 w-5" />,
      testing: <Target className="h-5 w-5" />
    }
    return icons[category as keyof typeof icons] || icons.setup
  }

  const filteredSteps = selectedCategory === 'all' 
    ? steps 
    : steps.filter(step => step.category === selectedCategory)

  const categories = [
    { id: 'all', name: '전체', count: steps.length },
    { id: 'setup', name: '설정', count: steps.filter(s => s.category === 'setup').length },
    { id: 'verification', name: '검증', count: steps.filter(s => s.category === 'verification').length },
    { id: 'integration', name: '연동', count: steps.filter(s => s.category === 'integration').length },
    { id: 'testing', name: '테스트', count: steps.filter(s => s.category === 'testing').length }
  ]

  return (
    <div className="space-y-6">
      <PageHeader 
        title="파트너 온보딩"
        description="파트너 계정 설정 및 서비스 연동을 위한 단계별 가이드"
      >
        <Button 
          onClick={onRefresh}
          className="flex items-center gap-2"
        >
          <RotateCcw className="h-4 w-4" />
          새로고침
        </Button>
      </PageHeader>

      {/* 전체 진행률 카드 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            온보딩 진행률
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">전체 진행률</span>
              <span className="text-2xl font-bold">{progress.overall_progress}%</span>
            </div>
            <Progress value={progress.overall_progress} className="h-3" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-500">완료된 단계</div>
                <div className="font-medium">{progress.completed_steps}/{progress.total_steps}</div>
              </div>
              <div>
                <div className="text-gray-500">예상 완료</div>
                <div className="font-medium">{progress.estimated_completion}</div>
              </div>
              <div>
                <div className="text-gray-500">현재 단계</div>
                <div className="font-medium">{progress.current_step}</div>
              </div>
              <div>
                <div className="text-gray-500">차단 요인</div>
                <div className="font-medium">{progress.blockers.length}개</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 차단 요인 알림 */}
      {progress.blockers.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertCircle className="h-5 w-5" />
              주의가 필요한 항목
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {progress.blockers.map((blocker, index) => (
                <li key={index} className="flex items-center gap-2 text-orange-700">
                  <AlertCircle className="h-4 w-4" />
                  {blocker}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            단계별 진행
          </TabsTrigger>
          <TabsTrigger value="resources" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            리소스
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* 카테고리 필터 */}
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Button
                key={category.id}
                variant={selectedCategory === category.id ? 'default' : 'outline'}
                size="sm"
                onClick={() => onCategoryChange(category.id)}
                className="flex items-center gap-2"
              >
                {category.id !== 'all' && getCategoryIcon(category.id)}
                {category.name}
                <Badge variant="secondary" className="ml-1">
                  {category.count}
                </Badge>
              </Button>
            ))}
          </div>

          {/* 단계 목록 */}
          <div className="space-y-4">
            {filteredSteps.map((step) => (
              <Card key={step.id} className="transition-all hover:shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(step.status)}
                      <div className="flex-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                          {step.title}
                          {step.required && (
                            <Badge variant="outline" className="text-xs">
                              필수
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {step.description}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getStatusColor(step.status)}>
                        {step.status === 'completed' && '완료'}
                        {step.status === 'in_progress' && '진행중'}
                        {step.status === 'pending' && '대기'}
                        {step.status === 'skipped' && '건너뜀'}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">진행률</span>
                      <span className="font-medium">{step.progress}%</span>
                    </div>
                    <Progress value={step.progress} className="h-2" />
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">예상 소요시간: </span>
                        <span className="font-medium">{step.estimated_time}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">카테고리: </span>
                        <span className="font-medium">{step.category}</span>
                      </div>
                    </div>

                    {step.details.checklist.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">체크리스트:</h4>
                        <ul className="text-sm space-y-1">
                          {step.details.checklist.map((item, index) => (
                            <li key={index} className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="flex gap-2 pt-2">
                      {step.status !== 'completed' && (
                        <Button
                          size="sm"
                          onClick={() => onCompleteStep(step.id)}
                          className="flex items-center gap-2"
                        >
                          <Play className="h-4 w-4" />
                          {step.details.automated ? '자동 실행' : '단계 완료'}
                        </Button>
                      )}
                      {!step.required && step.status !== 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onSkipStep(step.id)}
                        >
                          건너뛰기
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                도움말 및 가이드
              </CardTitle>
              <CardDescription>
                온보딩 과정에 도움이 되는 문서와 가이드
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-medium">시작 가이드</h4>
                  <div className="space-y-2 text-sm">
                    <a href="#" className="block p-2 border rounded hover:bg-gray-50">
                      📋 파트너 온보딩 체크리스트
                    </a>
                    <a href="#" className="block p-2 border rounded hover:bg-gray-50">
                      🔐 보안 설정 가이드
                    </a>
                    <a href="#" className="block p-2 border rounded hover:bg-gray-50">
                      🔌 API 연동 가이드
                    </a>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-medium">비디오 튜토리얼</h4>
                  <div className="space-y-2 text-sm">
                    <a href="#" className="block p-2 border rounded hover:bg-gray-50">
                      🎥 계정 설정 방법
                    </a>
                    <a href="#" className="block p-2 border rounded hover:bg-gray-50">
                      🎥 KYC 인증 프로세스
                    </a>
                    <a href="#" className="block p-2 border rounded hover:bg-gray-50">
                      🎥 지갑 연동 데모
                    </a>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
