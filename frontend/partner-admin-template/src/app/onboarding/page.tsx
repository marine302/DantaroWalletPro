'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { OnboardingManagementSection } from '@/components/onboarding/OnboardingManagementSection'

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
        checklist: ['신분증 업로드', '사업자등록증 제출', '주소 확인 서류'],
        resources: [
          { title: 'KYC 인증 가이드', url: '/docs/kyc', type: 'doc' },
          { title: 'KYC 인증 비디오', url: '/videos/kyc', type: 'video' }
        ],
        automated: false
      }
    },
    {
      id: 'api_integration',
      title: 'API 연동',
      description: 'DantaroWallet API 키 발급 및 연동 테스트',
      status: 'pending',
      progress: 25,
      estimated_time: '30분',
      required: true,
      category: 'integration',
      details: {
        checklist: ['API 키 발급', '연동 테스트', '웹훅 설정'],
        resources: [
          { title: 'API 문서', url: '/docs/api', type: 'doc' },
          { title: 'API 연동 가이드', url: '/docs/api-integration', type: 'guide' }
        ],
        automated: true
      }
    }
  ]

  const handleCompleteStep = (stepId: string) => {
    console.log('단계 완료:', stepId)
  }

  const handleSkipStep = (stepId: string) => {
    console.log('단계 건너뛰기:', stepId)
  }

  const handleRefresh = () => {
    console.log('온보딩 데이터 새로고침')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <OnboardingManagementSection
          progress={fallbackProgress}
          steps={fallbackSteps}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
          onCompleteStep={handleCompleteStep}
          onSkipStep={handleSkipStep}
          onRefresh={handleRefresh}
        />
      </div>
    </Sidebar>
  )
}