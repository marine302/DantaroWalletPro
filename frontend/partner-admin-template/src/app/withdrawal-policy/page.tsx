'use client'

import React, { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { WithdrawalPolicyManagementSection } from '@/components/withdrawal-policy/WithdrawalPolicyManagementSection'

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
      condition: '출금 금액이 500 USDT 이하',
      threshold: 500,
      enabled: true,
      priority: 1
    },
    {
      id: 'verified_user',
      name: '인증 사용자 자동 승인',
      condition: 'KYC 완료 및 신뢰도 높은 사용자',
      threshold: 2000,
      enabled: true,
      priority: 2
    },
    {
      id: 'whitelist_address',
      name: '화이트리스트 주소 자동 승인',
      condition: '사전 등록된 출금 주소',
      threshold: 10000,
      enabled: true,
      priority: 3
    }
  ]

  const [policies, setPolicies] = useState(fallbackPolicies)
  const [rules, setRules] = useState(fallbackRules)

  const handleUpdatePolicy = (policyId: string, updates: Partial<WithdrawalPolicy>) => {
    setPolicies(prev => prev.map(policy => 
      policy.id === policyId ? { ...policy, ...updates } : policy
    ))
  }

  const handleUpdateRule = (ruleId: string, updates: Partial<AutoApprovalRule>) => {
    setRules(prev => prev.map(rule => 
      rule.id === ruleId ? { ...rule, ...updates } : rule
    ))
  }

  const handleSave = () => {
    console.log('정책 저장:', { policies, rules })
  }

  const handleRefresh = () => {
    console.log('정책 데이터 새로고침')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <WithdrawalPolicyManagementSection
          policies={policies}
          rules={rules}
          showAdvanced={showAdvanced}
          onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
          onUpdatePolicy={handleUpdatePolicy}
          onUpdateRule={handleUpdateRule}
          onSave={handleSave}
          onRefresh={handleRefresh}
        />
      </div>
    </Sidebar>
  )
}
