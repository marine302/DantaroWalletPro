# Copilot 문서 #43: 파트너 어드민 출금 관리 - 프론트엔드

## 목표

파트너사가 출금 요청을 효율적으로 관리하고 처리할 수 있는 어드민 인터페이스를 Next.js로 구축합니다. 출금 큐 관리, 배치 처리, 에너지 요청 등의 핵심 기능을 제공합니다.

## 전제 조건

- Copilot 문서 #41 (출금 처리 백엔드 API)이 완료되어 있어야 합니다
- Next.js 14 (App Router) 환경이 설정되어 있어야 합니다
- 파트너 어드민 기본 레이아웃이 구현되어 있어야 합니다

## 🎯 출금 관리 구조

### 주요 기능

1. **출금 대기열**: 실시간 출금 요청 모니터링
2. **배치 관리**: 출금 그룹핑 및 최적화
3. **에너지 관리**: 에너지 요청 및 상태 확인
4. **지갑 관리**: 핫/콜드 월렛 자금 관리
5. **트랜잭션 서명**: TronLink 연동 서명 인터페이스

## 🛠️ 구현 단계

### Phase 1: 프로젝트 구조

### 1.1 디렉토리 구조

```
app/
├── (partner)/
│   ├── withdrawals/
│   │   ├── page.tsx           # 출금 대기열
│   │   ├── queue/page.tsx     # 상세 큐 관리
│   │   ├── batch/page.tsx     # 배치 처리
│   │   └── history/page.tsx   # 출금 이력
│   └── wallets/
│       └── page.tsx           # 지갑 관리
├── components/
│   └── partner/
│       ├── withdrawals/       # 출금 관련 컴포넌트
│       ├── wallets/          # 지갑 관련 컴포넌트
│       └── energy/           # 에너지 관련 컴포넌트
└── lib/
    ├── hooks/
    │   ├── useWithdrawals.ts
    │   └── useWallets.ts
    └── services/
        └── tronlink.ts       # TronLink 연동

```

### Phase 2: 출금 대기열 메인 페이지

### 2.1 출금 대시보드

```tsx
// app/(partner)/withdrawals/page.tsx
'use client'

import { useState } from 'react'
import WithdrawalStats from '@/components/partner/withdrawals/WithdrawalStats'
import WithdrawalQueue from '@/components/partner/withdrawals/WithdrawalQueue'
import EnergyStatusCard from '@/components/partner/energy/EnergyStatusCard'
import QuickActions from '@/components/partner/withdrawals/QuickActions'

export default function WithdrawalsPage() {
  const [refreshKey, setRefreshKey] = useState(0)

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">출금 관리</h2>
          <p className="mt-1 text-sm text-gray-600">
            출금 요청을 관리하고 처리 상태를 모니터링하세요
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={handleRefresh}
            className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            새로고침
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      <WithdrawalStats key={`stats-${refreshKey}`} />

      {/* 에너지 상태 및 빠른 작업 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <EnergyStatusCard />
        </div>
        <div>
          <QuickActions />
        </div>
      </div>

      {/* 출금 대기열 */}
      <WithdrawalQueue key={`queue-${refreshKey}`} />
    </div>
  )
}

```

### 2.2 출금 통계 컴포넌트

```tsx
// components/partner/withdrawals/WithdrawalStats.tsx
'use client'

import { useEffect, useState } from 'react'
import { fetchWithdrawalStats } from '@/lib/api/partner'
import {
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'

interface WithdrawalStats {
  pending: number
  processing: number
  completed: number
  failed: number
  totalAmount: number
  todayAmount: number
}

export default function WithdrawalStats() {
  const [stats, setStats] = useState<WithdrawalStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await fetchWithdrawalStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="animate-pulse">Loading stats...</div>
  }

  if (!stats) {
    return null
  }

  const cards = [
    {
      name: '대기 중',
      value: stats.pending,
      icon: ClockIcon,
      color: 'text-yellow-600 bg-yellow-100'
    },
    {
      name: '처리 중',
      value: stats.processing,
      icon: ClockIcon,
      color: 'text-blue-600 bg-blue-100'
    },
    {
      name: '완료',
      value: stats.completed,
      icon: CheckCircleIcon,
      color: 'text-green-600 bg-green-100'
    },
    {
      name: '실패',
      value: stats.failed,
      icon: XCircleIcon,
      color: 'text-red-600 bg-red-100'
    },
    {
      name: '오늘 출금액',
      value: `${stats.todayAmount.toLocaleString()} USDT`,
      icon: CurrencyDollarIcon,
      color: 'text-indigo-600 bg-indigo-100'
    }
  ]

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map((card) => (
        <div
          key={card.name}
          className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:px-6"
        >
          <dt>
            <div className={`absolute rounded-md p-3 ${card.color}`}>
              <card.icon className="h-6 w-6" aria-hidden="true" />
            </div>
            <p className="ml-16 truncate text-sm font-medium text-gray-500">
              {card.name}
            </p>
          </dt>
          <dd className="ml-16 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
          </dd>
        </div>
      ))}
    </div>
  )
}

```

### 2.3 출금 대기열 컴포넌트

```tsx
// components/partner/withdrawals/WithdrawalQueue.tsx
'use client'

import { useState, useEffect } from 'react'
import { fetchPendingWithdrawals } from '@/lib/api/partner'
import WithdrawalQueueItem from './WithdrawalQueueItem'
import BatchActionBar from './BatchActionBar'

interface Withdrawal {
  id: number
  withdrawalId: string
  userId: number
  userName: string
  amount: number
  toAddress: string
  type: 'immediate' | 'regular' | 'scheduled'
  status: string
  priority: number
  energyRequired: number
  createdAt: string
}

export default function WithdrawalQueue() {
  const [withdrawals, setWithdrawals] = useState<Withdrawal[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'immediate' | 'regular' | 'scheduled'>('all')

  useEffect(() => {
    loadWithdrawals()
  }, [filter])

  const loadWithdrawals = async () => {
    try {
      const data = await fetchPendingWithdrawals({ type: filter })
      setWithdrawals(data)
    } catch (error) {
      console.error('Failed to load withdrawals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(withdrawals.map(w => w.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id])
    } else {
      setSelectedIds(selectedIds.filter(selectedId => selectedId !== id))
    }
  }

  const filteredWithdrawals = filter === 'all'
    ? withdrawals
    : withdrawals.filter(w => w.type === filter)

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium leading-6 text-gray-900">
            출금 대기열
          </h3>
          <div className="flex space-x-2">
            {['all', 'immediate', 'regular', 'scheduled'].map((type) => (
              <button
                key={type}
                onClick={() => setFilter(type as any)}
                className={`
                  px-3 py-1 text-sm font-medium rounded-md
                  ${filter === type
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                  }
                `}
              >
                {type === 'all' ? '전체' :
                 type === 'immediate' ? '즉시' :
                 type === 'regular' ? '일반' : '정기'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {selectedIds.length > 0 && (
        <BatchActionBar
          selectedCount={selectedIds.length}
          selectedIds={selectedIds}
          onClearSelection={() => setSelectedIds([])}
          onRefresh={loadWithdrawals}
        />
      )}

      <div className="overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="relative px-6 py-3">
                <input
                  type="checkbox"
                  className="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  checked={selectedIds.length === filteredWithdrawals.length && filteredWithdrawals.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                사용자
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                금액
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                수신 주소
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                유형
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                에너지
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                상태
              </th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredWithdrawals.map((withdrawal) => (
              <WithdrawalQueueItem
                key={withdrawal.id}
                withdrawal={withdrawal}
                isSelected={selectedIds.includes(withdrawal.id)}
                onSelect={(checked) => handleSelectOne(withdrawal.id, checked)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

```

### Phase 3: 배치 처리 인터페이스

### 3.1 배치 생성 모달

```tsx
// components/partner/withdrawals/CreateBatchModal.tsx
'use client'

import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { createWithdrawalBatch } from '@/lib/api/partner'

interface CreateBatchModalProps {
  isOpen: boolean
  onClose: () => void
  selectedIds: number[]
  onSuccess: () => void
}

export default function CreateBatchModal({
  isOpen,
  onClose,
  selectedIds,
  onSuccess
}: CreateBatchModalProps) {
  const [loading, setLoading] = useState(false)
  const [optimization, setOptimization] = useState<any>(null)

  const handleCreateBatch = async () => {
    setLoading(true)
    try {
      const result = await createWithdrawalBatch({
        withdrawalIds: selectedIds
      })

      setOptimization(result.optimization)

      // 2초 후 성공 처리
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 2000)
    } catch (error) {
      console.error('Failed to create batch:', error)
      setLoading(false)
    }
  }

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="absolute top-0 right-0 hidden pt-4 pr-4 sm:block">
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                    <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                      배치 생성
                    </Dialog.Title>

                    <div className="mt-4">
                      <p className="text-sm text-gray-500">
                        선택한 {selectedIds.length}개의 출금 요청을 배치로 처리합니다.
                      </p>

                      {optimization && (
                        <div className="mt-4 rounded-md bg-green-50 p-4">
                          <h4 className="text-sm font-medium text-green-800">
                            배치 최적화 결과
                          </h4>
                          <div className="mt-2 text-sm text-green-700">
                            <p>원본 에너지: {optimization.originalEnergy.toLocaleString()}</p>
                            <p>최적화 에너지: {optimization.optimizedEnergy.toLocaleString()}</p>
                            <p>절약된 에너지: {optimization.savedEnergy.toLocaleString()}</p>
                            <p className="font-medium">
                              절약률: {optimization.savedPercentage.toFixed(1)}%
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                  <button
                    type="button"
                    className="inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm"
                    onClick={handleCreateBatch}
                    disabled={loading}
                  >
                    {loading ? '처리 중...' : '배치 생성'}
                  </button>
                  <button
                    type="button"
                    className="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:mt-0 sm:w-auto sm:text-sm"
                    onClick={onClose}
                    disabled={loading}
                  >
                    취소
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}

```

### Phase 4: 에너지 관리 인터페이스

### 4.1 에너지 상태 카드

```tsx
// components/partner/energy/EnergyStatusCard.tsx
'use client'

import { useEffect, useState } from 'react'
import { fetchEnergyStatus } from '@/lib/api/partner'
import { BoltIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { formatNumber } from '@/lib/utils'

interface EnergyStatus {
  availableEnergy: number
  totalEnergy: number
  usedToday: number
  estimatedHoursRemaining: number
  warningLevel: 'normal' | 'warning' | 'critical'
  autoRechargeEnabled: boolean
  nextRechargeAmount?: number
}

export default function EnergyStatusCard() {
  const [status, setStatus] = useState<EnergyStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const interval = setInterval(loadEnergyStatus, 30000) // 30초마다 갱신
    loadEnergyStatus()
    return () => clearInterval(interval)
  }, [])

  const loadEnergyStatus = async () => {
    try {
      const data = await fetchEnergyStatus()
      setStatus(data)
    } catch (error) {
      console.error('Failed to load energy status:', error)
    } finally {
      setLoading(false)
    }
  }

  const getWarningColor = (level: string) => {
    switch (level) {
      case 'critical': return 'red'
      case 'warning': return 'yellow'
      default: return 'green'
    }
  }

  const energyPercentage = status
    ? (status.availableEnergy / status.totalEnergy) * 100
    : 0

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BoltIcon className="h-8 w-8 text-yellow-500 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">에너지 상태</h3>
              <p className="text-sm text-gray-500">실시간 모니터링</p>
            </div>
          </div>
          {status?.warningLevel !== 'normal' && (
            <ExclamationTriangleIcon
              className={`h-6 w-6 text-${getWarningColor(status.warningLevel)}-500`}
            />
          )}
        </div>

        {loading ? (
          <div className="mt-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ) : status && (
          <>
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>사용 가능 에너지</span>
                <span>{formatNumber(status.availableEnergy)} / {formatNumber(status.totalEnergy)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full bg-${getWarningColor(status.warningLevel)}-500`}
                  style={{ width: `${energyPercentage}%` }}
                ></div>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">오늘 사용량</span>
                <span className="font-medium">{formatNumber(status.usedToday)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">예상 잔여 시간</span>
                <span className="font-medium">{status.estimatedHoursRemaining}시간</span>
              </div>
              {status.autoRechargeEnabled && status.nextRechargeAmount && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">다음 충전 예정</span>
                <span className="font-medium">{formatNumber(status.nextRechargeAmount)}</span>
              </div>
              )}
            </div>

            {status.warningLevel !== 'normal' && (
              <div className={`mt-4 p-3 rounded-md bg-${getWarningColor(status.warningLevel)}-50`}>
                <p className={`text-sm text-${getWarningColor(status.warningLevel)}-800`}>
                  {status.warningLevel === 'critical'
                    ? '에너지가 부족합니다. 즉시 충전이 필요합니다.'
                    : '에너지가 곧 부족해질 예정입니다.'}
                </p>
                <button
                  onClick={() => window.location.href = '/energy/recharge'}
                  className={`mt-2 text-sm font-medium text-${getWarningColor(status.warningLevel)}-600 hover:text-${getWarningColor(status.warningLevel)}-700`}
                >
                  에너지 충전하기 →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

```

### 4.2 에너지 요청 모달

```tsx
// components/partner/energy/EnergyRequestModal.tsx
'use client'

import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, BoltIcon } from '@heroicons/react/24/outline'
import { calculateEnergyRequired, requestEnergy } from '@/lib/api/partner'
import { formatNumber, formatTRX } from '@/lib/utils'

interface EnergyRequestModalProps {
  isOpen: boolean
  onClose: () => void
  withdrawalIds: string[]
  totalAmount: number
  onSuccess: () => void
}

export default function EnergyRequestModal({
  isOpen,
  onClose,
  withdrawalIds,
  totalAmount,
  onSuccess
}: EnergyRequestModalProps) {
  const [loading, setLoading] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [energyDetails, setEnergyDetails] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen && withdrawalIds.length > 0) {
      calculateEnergy()
    }
  }, [isOpen, withdrawalIds])

  const calculateEnergy = async () => {
    setCalculating(true)
    setError('')

    try {
      const details = await calculateEnergyRequired({
        withdrawal_ids: withdrawalIds,
        batch_mode: withdrawalIds.length > 1
      })
      setEnergyDetails(details)
    } catch (error) {
      setError('에너지 계산 중 오류가 발생했습니다.')
      console.error('Failed to calculate energy:', error)
    } finally {
      setCalculating(false)
    }
  }

  const handleRequestEnergy = async () => {
    if (!energyDetails) return

    setLoading(true)
    setError('')

    try {
      await requestEnergy({
        withdrawal_ids: withdrawalIds,
        energy_amount: energyDetails.total_energy_required,
        payment_amount: energyDetails.total_cost_trx
      })

      onSuccess()
      onClose()
    } catch (error: any) {
      setError(error.message || '에너지 요청 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="absolute top-0 right-0 hidden pt-4 pr-4 sm:block">
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10">
                    <BoltIcon className="h-6 w-6 text-yellow-600" />
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                      에너지 요청
                    </Dialog.Title>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        선택한 {withdrawalIds.length}개 출금 처리에 필요한 에너지를 요청합니다.
                      </p>
                    </div>

                    {calculating ? (
                      <div className="mt-4 space-y-3">
                        <div className="animate-pulse">
                          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                        </div>
                      </div>
                    ) : energyDetails && (
                      <div className="mt-4 bg-gray-50 rounded-lg p-4">
                        <div className="space-y-3">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-500">출금 건수</span>
                            <span className="font-medium">{withdrawalIds.length}건</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-500">총 출금액</span>
                            <span className="font-medium">{formatNumber(totalAmount)} USDT</span>
                          </div>
                          <div className="border-t pt-3">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-500">필요 에너지</span>
                              <span className="font-medium">{formatNumber(energyDetails.total_energy_required)}</span>
                            </div>
                            <div className="flex justify-between text-sm mt-2">
                              <span className="text-gray-500">에너지 비용</span>
                              <span className="font-medium">{formatTRX(energyDetails.base_cost_trx)}</span>
                            </div>
                            <div className="flex justify-between text-sm mt-2">
                              <span className="text-gray-500">서비스 수수료</span>
                              <span className="font-medium">{formatTRX(energyDetails.saas_fee_trx)}</span>
                            </div>
                            <div className="flex justify-between text-base font-medium mt-3 pt-3 border-t">
                              <span>총 비용</span>
                              <span className="text-blue-600">{formatTRX(energyDetails.total_cost_trx)}</span>
                            </div>
                          </div>
                        </div>

                        {energyDetails.fallback_burn_trx && (
                          <div className="mt-3 p-3 bg-yellow-50 rounded-md">
                            <p className="text-xs text-yellow-800">
                              <strong>폴백 모드:</strong> 에너지 공급 실패 시 약 {formatTRX(energyDetails.fallback_burn_trx)}가 직접 소각됩니다.
                            </p>
                          </div>
                        )}

                        <div className="mt-3 text-xs text-gray-500">
                          유효기간: {new Date(energyDetails.valid_until).toLocaleString()}
                        </div>
                      </div>
                    )}

                    {error && (
                      <div className="mt-4 p-3 bg-red-50 rounded-md">
                        <p className="text-sm text-red-800">{error}</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                  <button
                    type="button"
                    disabled={loading || calculating || !energyDetails}
                    onClick={handleRequestEnergy}
                    className="inline-flex w-full justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '요청 중...' : `${formatTRX(energyDetails?.total_cost_trx || 0)} 결제하기`}
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    className="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:mt-0 sm:w-auto sm:text-sm"
                  >
                    취소
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}

```

### Phase 5: TronLink 연동 인터페이스

### 5.1 TronLink 서비스

```tsx
// lib/services/tronlink.ts
import { TronWeb } from 'tronweb'

interface TronLinkWindow extends Window {
  tronWeb?: any
  tronLink?: any
}

declare const window: TronLinkWindow

export class TronLinkService {
  private tronWeb: any = null
  private connected: boolean = false

  async connect(): Promise<string> {
    if (!this.isTronLinkAvailable()) {
      throw new Error('TronLink가 설치되어 있지 않습니다.')
    }

    try {
      const response = await window.tronLink.request({ method: 'tron_requestAccounts' })

      if (response.code === 200) {
        this.tronWeb = window.tronWeb
        this.connected = true
        return this.tronWeb.defaultAddress.base58
      } else {
        throw new Error('TronLink 연결이 거부되었습니다.')
      }
    } catch (error) {
      console.error('TronLink connection error:', error)
      throw error
    }
  }

  async disconnect() {
    this.connected = false
    this.tronWeb = null
  }

  isTronLinkAvailable(): boolean {
    return typeof window !== 'undefined' && !!window.tronLink
  }

  isConnected(): boolean {
    return this.connected && !!this.tronWeb && !!this.tronWeb.defaultAddress
  }

  async getBalance(): Promise<{ trx: number; usdt: number }> {
    if (!this.isConnected()) {
      throw new Error('TronLink가 연결되어 있지 않습니다.')
    }

    try {
      // TRX 잔액
      const trxBalance = await this.tronWeb.trx.getBalance(this.tronWeb.defaultAddress.base58)

      // USDT 잔액 (TRC20)
      const usdtContract = await this.tronWeb.contract().at('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
      const usdtBalance = await usdtContract.balanceOf(this.tronWeb.defaultAddress.base58).call()

      return {
        trx: this.tronWeb.fromSun(trxBalance),
        usdt: usdtBalance.toNumber() / 1e6
      }
    } catch (error) {
      console.error('Balance fetch error:', error)
      throw error
    }
  }

  async signTransaction(transaction: any): Promise<any> {
    if (!this.isConnected()) {
      throw new Error('TronLink가 연결되어 있지 않습니다.')
    }

    try {
      const signedTransaction = await this.tronWeb.trx.sign(transaction)
      return signedTransaction
    } catch (error) {
      console.error('Transaction signing error:', error)
      throw error
    }
  }

  async sendTransaction(signedTransaction: any): Promise<string> {
    if (!this.isConnected()) {
      throw new Error('TronLink가 연결되어 있지 않습니다.')
    }

    try {
      const result = await this.tronWeb.trx.sendRawTransaction(signedTransaction)

      if (result.result) {
        return result.txid
      } else {
        throw new Error(result.message || '트랜잭션 전송 실패')
      }
    } catch (error) {
      console.error('Transaction send error:', error)
      throw error
    }
  }

  getAddress(): string | null {
    if (!this.isConnected()) {
      return null
    }
    return this.tronWeb.defaultAddress.base58
  }

  // 주소 변경 감지
  onAccountChanged(callback: (address: string) => void) {
    if (window.tronLink) {
      window.addEventListener('message', (event) => {
        if (event.data.message && event.data.message.action === 'accountsChanged') {
          callback(event.data.message.data.address)
        }
      })
    }
  }
}

export const tronLinkService = new TronLinkService()

```

### 5.2 TronLink 연결 컴포넌트

```tsx
// components/partner/wallets/TronLinkConnect.tsx
'use client'

import { useState, useEffect } from 'react'
import { tronLinkService } from '@/lib/services/tronlink'
import { WalletIcon, LinkIcon } from '@heroicons/react/24/outline'
import { formatAddress, formatTRX } from '@/lib/utils'

export default function TronLinkConnect() {
  const [connected, setConnected] = useState(false)
  const [address, setAddress] = useState<string | null>(null)
  const [balance, setBalance] = useState<{ trx: number; usdt: number } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    checkConnection()

    // 계정 변경 감지
    tronLinkService.onAccountChanged((newAddress) => {
      setAddress(newAddress)
      loadBalance()
    })
  }, [])

  const checkConnection = async () => {
    if (tronLinkService.isConnected()) {
      const addr = tronLinkService.getAddress()
      setAddress(addr)
      setConnected(true)
      await loadBalance()
    }
  }

  const loadBalance = async () => {
    try {
      const bal = await tronLinkService.getBalance()
      setBalance(bal)
    } catch (error) {
      console.error('Failed to load balance:', error)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    setError('')

    try {
      const addr = await tronLinkService.connect()
      setAddress(addr)
      setConnected(true)
      await loadBalance()

      // 서버에 지갑 주소 등록
      await registerWallet(addr)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    await tronLinkService.disconnect()
    setConnected(false)
    setAddress(null)
    setBalance(null)
  }

  const registerWallet = async (walletAddress: string) => {
    try {
      await fetch('/api/partner/wallets/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_type: 'tronlink',
          wallet_address: walletAddress,
          purpose: 'withdrawal_signing'
        })
      })
    } catch (error) {
      console.error('Failed to register wallet:', error)
    }
  }

  if (!tronLinkService.isTronLinkAvailable()) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">TronLink 필요</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>출금 서명을 위해 TronLink 브라우저 확장 프로그램이 필요합니다.</p>
              <a
                href="https://www.tronlink.org/"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block font-medium text-yellow-600 hover:text-yellow-500"
              >
                TronLink 설치하기 →
              </a>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <WalletIcon className="h-8 w-8 text-blue-500 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">TronLink 지갑</h3>
              <p className="text-sm text-gray-500">출금 서명용 외부 지갑</p>
            </div>
          </div>
          {connected && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-1.5"></span>
              연결됨
            </span>
          )}
        </div>

        {!connected ? (
          <div className="text-center py-8">
            <LinkIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">지갑 연결 필요</h3>
            <p className="mt-1 text-sm text-gray-500">
              출금 트랜잭션 서명을 위해 TronLink를 연결해주세요.
            </p>
            <div className="mt-6">
              <button
                onClick={handleConnect}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? '연결 중...' : 'TronLink 연결'}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-500">지갑 주소</label>
                  <p className="text-sm font-mono">{formatAddress(address!)}</p>
                </div>
                {balance && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-gray-500">TRX 잔액</label>
                        <p className="text-sm font-medium">{formatTRX(balance.trx)}</p>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">USDT 잔액</label>
                        <p className="text-sm font-medium">{formatNumber(balance.usdt)} USDT</p>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={loadBalance}
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                잔액 새로고침
              </button>
              <button
                onClick={handleDisconnect}
                className="text-sm text-red-600 hover:text-red-500"
              >
                연결 해제
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}

```

### Phase 6: 출금 서명 프로세스

### 6.1 출금 서명 인터페이스

```tsx
// components/partner/withdrawals/WithdrawalSignature.tsx
'use client'

import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { KeyIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
import { tronLinkService } from '@/lib/services/tronlink'
import { signWithdrawalBatch } from '@/lib/api/partner'

interface WithdrawalSignatureProps {
  batchId: string
  transactions: Array<{
    id: string
    to: string
    amount: number
    unsigned_tx: any
  }>
  onSuccess: () => void
  onCancel: () => void
}

export default function WithdrawalSignature({
  batchId,
  transactions,
  onSuccess,
  onCancel
}: WithdrawalSignatureProps) {
  const [signing, setSigning] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [signedTxs, setSignedTxs] = useState<any[]>([])
  const [error, setError] = useState('')

  const signNextTransaction = async () => {
    if (currentIndex >= transactions.length) {
      await submitSignedBatch()
      return
    }

    setSigning(true)
    setError('')

    try {
      const tx = transactions[currentIndex]
      const signedTx = await tronLinkService.signTransaction(tx.unsigned_tx)

      setSignedTxs([...signedTxs, {
        transaction_id: tx.id,
        signed_tx: signedTx
      }])

      setCurrentIndex(currentIndex + 1)

      // 다음 트랜잭션 자동 진행
      if (currentIndex + 1 < transactions.length) {
        setTimeout(() => signNextTransaction(), 1000)
      } else {
        await submitSignedBatch()
      }
    } catch (error: any) {
      setError(`서명 실패: ${error.message}`)
      setSigning(false)
    }
  }

  const submitSignedBatch = async () => {
    try {
      await signWithdrawalBatch({
        batch_id: batchId,
        signed_transactions: signedTxs
      })

      onSuccess()
    } catch (error: any) {
      setError(`제출 실패: ${error.message}`)
    } finally {
      setSigning(false)
    }
  }

  const progress = (currentIndex / transactions.length) * 100

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
          <div>
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
              <KeyIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="mt-3 text-center sm:mt-5">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                출금 트랜잭션 서명
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  TronLink에서 {transactions.length}개의 트랜잭션을 순차적으로 서명해주세요.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-5">
            {/* 진행 상태 */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>진행 상황</span>
                <span>{currentIndex} / {transactions.length}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* 현재 트랜잭션 정보 */}
            {currentIndex < transactions.length && (
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  트랜잭션 #{currentIndex + 1}
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">수신 주소</span>
                    <span className="font-mono text-xs">
                      {formatAddress(transactions[currentIndex].to)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">금액</span>
                    <span className="font-medium">
                      {formatNumber(transactions[currentIndex].amount)} USDT
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* 서명 완료 목록 */}
            {signedTxs.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  서명 완료
                </h4>
                <div className="space-y-1">
                  {signedTxs.map((tx, index) => (
                    <div key={tx.transaction_id} className="flex items-center text-sm">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                      <span className="text-gray-600">
                        트랜잭션 #{index + 1}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-50 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
          </div>

          <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
            <button
              type="button"
              disabled={signing}
              onClick={currentIndex === 0 ? signNextTransaction : undefined}
              className="inline-flex w-full justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:col-start-2 sm:text-sm disabled:opacity-50"
            >
              {signing ? '서명 중...' : currentIndex === 0 ? '서명 시작' : '진행 중'}
            </button>
            <button
              type="button"
              disabled={signing}
              onClick={onCancel}
              className="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:col-start-1 sm:mt-0 sm:text-sm disabled:opacity-50"
            >
              취소
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

```

### Phase 7: API 클라이언트 구현

### 7.1 파트너 API 클라이언트

```tsx
// lib/api/partner.ts
import { apiClient } from './client'

// 출금 관련 API
export const fetchWithdrawalStats = async () => {
  const response = await apiClient.get('/partner/withdrawals/stats')
  return response.data
}

export const fetchWithdrawalQueue = async (params: {
  status?: string
  page?: number
  limit?: number
}) => {
  const response = await apiClient.get('/partner/withdrawals/queue', { params })
  return response.data
}

export const approveWithdrawals = async (withdrawalIds: string[]) => {
  const response = await apiClient.post('/partner/withdrawals/approve', {
    withdrawal_ids: withdrawalIds
  })
  return response.data
}

export const createWithdrawalBatch = async (data: {
  withdrawal_ids: string[]
  batch_type: string
}) => {
  const response = await apiClient.post('/partner/withdrawals/batch', data)
  return response.data
}

// 에너지 관련 API
export const fetchEnergyStatus = async () => {
  const response = await apiClient.get('/partner/energy/status')
  return response.data
}

export const calculateEnergyRequired = async (data: {
  withdrawal_ids: string[]
  batch_mode: boolean
}) => {
  const response = await apiClient.post('/partner/energy/calculate', data)
  return response.data
}

export const requestEnergy = async (data: {
  withdrawal_ids: string[]
  energy_amount: number
  payment_amount: number
}) => {
  const response = await apiClient.post('/partner/energy/request', data)
  return response.data
}

// 지갑 관련 API
export const fetchWalletBalances = async () => {
  const response = await apiClient.get('/partner/wallets/balances')
  return response.data
}

export const transferFunds = async (data: {
  from_wallet: string
  to_wallet: string
  amount: number
  token: string
}) => {
  const response = await apiClient.post('/partner/wallets/transfer', data)
  return response.data
}

// 트랜잭션 서명 API
export const getUnsignedTransactions = async (batchId: string) => {
  const response = await apiClient.get(`/partner/withdrawals/batch/${batchId}/unsigned`)
  return response.data
}

export const signWithdrawalBatch = async (data: {
  batch_id: string
  signed_transactions: Array<{
    transaction_id: string
    signed_tx: any
  }>
}) => {
  const response = await apiClient.post('/partner/withdrawals/sign', data)
  return response.data
}

```

### 7.2 Custom Hooks

```tsx
// lib/hooks/useWithdrawals.ts
import { useState, useEffect } from 'react'
import { fetchWithdrawalQueue } from '@/lib/api/partner'

export function useWithdrawalQueue(status?: string) {
  const [withdrawals, setWithdrawals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    loadWithdrawals()
  }, [status, page])

  const loadWithdrawals = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await fetchWithdrawalQueue({
        status,
        page,
        limit: 20
      })

      setWithdrawals(data.withdrawals)
      setTotalPages(data.total_pages)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const refresh = () => {
    loadWithdrawals()
  }

  return {
    withdrawals,
    loading,
    error,
    page,
    totalPages,
    setPage,
    refresh
  }
}

// lib/hooks/useEnergyStatus.ts
import { useState, useEffect } from 'react'
import { fetchEnergyStatus } from '@/lib/api/partner'

export function useEnergyStatus(refreshInterval = 30000) {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStatus()

    const interval = setInterval(loadStatus, refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  const loadStatus = async () => {
    try {
      const data = await fetchEnergyStatus()
      setStatus(data)
      setError(null)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return { status, loading, error, refresh: loadStatus }
}

```

## 🧪 테스트 및 검증

### 1. 출금 플로우 테스트

```tsx
// tests/withdrawals.test.ts
describe('출금 관리 시스템', () => {
  test('출금 큐 조회가 정상 작동하는가', async () => {
    // 구현
  })

  test('배치 생성이 올바르게 동작하는가', async () => {
    // 구현
  })

  test('에너지 계산이 정확한가', async () => {
    // 구현
  })
})

```

### 2. TronLink 연동 테스트

```tsx
describe('TronLink 연동', () => {
  test('지갑 연결이 정상 작동하는가', async () => {
    // 구현
  })

  test('트랜잭션 서명이 완료되는가', async () => {
    // 구현
  })
})

```

## 📋 체크리스트

### 기능 구현

- [ ]  출금 대기열 UI 구현
- [ ]  출금 통계 대시보드
- [ ]  배치 생성 인터페이스
- [ ]  에너지 상태 모니터링
- [ ]  에너지 요청 프로세스
- [ ]  TronLink 연동
- [ ]  트랜잭션 서명 UI
- [ ]  지갑 잔액 관리

### 사용자 경험

- [ ]  실시간 상태 업데이트
- [ ]  직관적인 워크플로우
- [ ]  명확한 에러 메시지
- [ ]  로딩 상태 표시
- [ ]  반응형 디자인

### 보안

- [ ]  출금 한도 검증
- [ ]  트랜잭션 서명 검증
- [ ]  API 권한 체크
- [ ]  CSRF 보호

## 🎉 기대 효과

1. **효율적인 출금 관리**: 배치 처리로 가스비 절감
2. **투명한 비용 구조**: 에너지 비용 사전 확인
3. **안전한 서명 프로세스**: TronLink 통합
4. **실시간 모니터링**: 상태 즉시 확인
5. **자동화된 워크플로우**: 수동 작업 최소화

이 시스템을 통해 파트너사는 효율적이고 안전하게 출금 요청을 관리할 수 있습니다!