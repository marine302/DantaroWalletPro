# Copilot 문서 #42: 본사 슈퍼어드민 대시보드 - 프론트엔드

## 목표

본사가 모든 파트너사와 에너지 풀을 통합 관리할 수 있는 슈퍼어드민 대시보드를 Next.js로 구축합니다. 실시간 모니터링, 에너지 관리, 수익 분석 등 핵심 기능을 제공합니다.

## 전제 조건

- Copilot 문서 #40, #41 (백엔드 API)이 완료되어 있어야 합니다
- Next.js 14 (App Router) 환경이 설정되어 있어야 합니다
- TailwindCSS가 설정되어 있어야 합니다
- 백엔드 API와 통신 가능해야 합니다

## 🎯 대시보드 구조

### 주요 섹션

1. **Overview**: 전체 시스템 현황
2. **Energy Pool**: 에너지 공급원 관리
3. **Partners**: 파트너사 관리
4. **Staking**: 자체 스테이킹 관리
5. **Revenue**: 수익 분석
6. **Monitoring**: 실시간 모니터링

## 🛠️ 구현 단계

### Phase 1: 프로젝트 구조 설정

### 1.1 디렉토리 구조

```
app/
├── (superadmin)/
│   ├── layout.tsx          # 슈퍼어드민 레이아웃
│   ├── dashboard/
│   │   └── page.tsx        # 대시보드 메인
│   ├── energy-pool/
│   │   ├── page.tsx        # 에너지 풀 관리
│   │   └── [id]/page.tsx   # 공급원 상세
│   ├── partners/
│   │   ├── page.tsx        # 파트너사 목록
│   │   └── [id]/page.tsx   # 파트너사 상세
│   ├── staking/
│   │   └── page.tsx        # 스테이킹 관리
│   └── revenue/
│       └── page.tsx        # 수익 분석
├── components/
│   └── superadmin/
│       ├── dashboard/      # 대시보드 컴포넌트
│       ├── energy/         # 에너지 관련
│       ├── partners/       # 파트너 관련
│       └── charts/         # 차트 컴포넌트
└── lib/
    ├── api/               # API 클라이언트
    └── hooks/             # 커스텀 훅

```

### Phase 2: 레이아웃 및 네비게이션

### 2.1 슈퍼어드민 레이아웃

```tsx
// app/(superadmin)/layout.tsx
import { ReactNode } from 'react'
import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import SuperAdminSidebar from '@/components/superadmin/SuperAdminSidebar'
import SuperAdminHeader from '@/components/superadmin/SuperAdminHeader'

export default async function SuperAdminLayout({
  children
}: {
  children: ReactNode
}) {
  const session = await getServerSession(authOptions)

  // 슈퍼어드민 권한 체크
  if (!session || session.user.role !== 'SUPERADMIN') {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <SuperAdminSidebar />
      <div className="lg:pl-64">
        <SuperAdminHeader />
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

```

### 2.2 사이드바 컴포넌트

```tsx
// components/superadmin/SuperAdminSidebar.tsx
'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  HomeIcon,
  BoltIcon,
  UsersIcon,
  CircleStackIcon,
  ChartBarIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Energy Pool', href: '/energy-pool', icon: BoltIcon },
  { name: 'Partners', href: '/partners', icon: UsersIcon },
  { name: 'Staking', href: '/staking', icon: CircleStackIcon },
  { name: 'Revenue', href: '/revenue', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export default function SuperAdminSidebar() {
  const pathname = usePathname()

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-900 px-6 pb-4">
        <div className="flex h-16 shrink-0 items-center">
          <h1 className="text-white text-xl font-bold">
            DantaroWallet Admin
          </h1>
        </div>
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
                {navigation.map((item) => {
                  const isActive = pathname.startsWith(item.href)
                  return (
                    <li key={item.name}>
                      <Link
                        href={item.href}
                        className={`
                          group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold
                          ${isActive
                            ? 'bg-gray-800 text-white'
                            : 'text-gray-400 hover:text-white hover:bg-gray-800'
                          }
                        `}
                      >
                        <item.icon
                          className={`h-6 w-6 shrink-0 ${
                            isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'
                          }`}
                          aria-hidden="true"
                        />
                        {item.name}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  )
}

```