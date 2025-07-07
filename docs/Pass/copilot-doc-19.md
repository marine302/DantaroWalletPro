# Copilot 문서 #19: 파트너 관리자 UI 템플릿

## 목표
파트너사가 자체 사용자들을 관리할 수 있는 완전한 관리자 대시보드 템플릿을 제공합니다. 화이트라벨링을 통해 각 파트너사의 브랜딩을 적용하고, 커스터마이징 가능한 모듈식 구조로 구현합니다.

## 전제 조건
- Copilot 문서 #15-18이 완료되어 있어야 합니다.
- 파트너사 관리 시스템이 구현되어 있어야 합니다.
- 온보딩 자동화 시스템이 구축되어 있어야 합니다.
- React/TypeScript 프론트엔드 환경이 준비되어 있어야 합니다.

## 🎯 파트너 관리자 UI 구조

### 📊 대시보드 레이아웃
```
Partner Admin Dashboard
├── 🏠 메인 대시보드
│   ├── 실시간 통계 위젯
│   ├── 최근 거래 활동
│   ├── 시스템 상태 모니터링
│   └── 빠른 액션 버튼
├── 👥 사용자 관리
│   ├── 사용자 목록 및 검색
│   ├── 사용자 상세 정보
│   ├── 지갑 상태 관리
│   └── 사용자별 거래 이력
├── 💰 지갑 및 거래 관리
│   ├── 지갑 잔액 모니터링
│   ├── 입출금 요청 관리
│   ├── 거래 승인/거부
│   └── 수수료 설정 관리
├── 📊 분석 및 리포트
│   ├── 거래량 분석
│   ├── 수익 분석
│   ├── 사용자 활동 분석
│   └── 커스텀 리포트 생성
├── ⚙️ 시스템 설정
│   ├── 파트너 정보 관리
│   ├── API 키 관리
│   ├── 웹훅 설정
│   └── 브랜딩 커스터마이징
└── 🔧 지원 및 도구
    ├── 기술 지원 요청
    ├── 시스템 로그 조회
    ├── 백업/복원 관리
    └── 사용 가이드
```

## 🛠️ 구현 단계

### Phase 1: 기본 프레임워크 구축 (2일)

#### 1.1 파트너 대시보드 프로젝트 구조
```bash
# 파트너 대시보드 생성
npx create-next-app@latest partner-admin-template --typescript --tailwind --eslint
cd partner-admin-template

# 필요한 패키지 설치
npm install @reduxjs/toolkit react-redux
npm install @headlessui/react @heroicons/react
npm install recharts date-fns
npm install react-hook-form @hookform/resolvers yup
npm install react-hot-toast
npm install next-themes
npm install @tanstack/react-query
```

#### 1.2 프로젝트 구조 설정
```
partner-admin-template/
├── src/
│   ├── components/
│   │   ├── common/           # 공통 컴포넌트
│   │   ├── dashboard/        # 대시보드 컴포넌트
│   │   ├── users/           # 사용자 관리
│   │   ├── wallets/         # 지갑 관리
│   │   ├── analytics/       # 분석 컴포넌트
│   │   ├── settings/        # 설정 컴포넌트
│   │   └── layout/          # 레이아웃 컴포넌트
│   ├── pages/
│   │   ├── api/             # API 라우트
│   │   ├── dashboard/       # 대시보드 페이지
│   │   ├── users/           # 사용자 관리 페이지
│   │   ├── wallets/         # 지갑 관리 페이지
│   │   ├── analytics/       # 분석 페이지
│   │   └── settings/        # 설정 페이지
│   ├── store/               # Redux store
│   ├── services/            # API 서비스
│   ├── hooks/               # 커스텀 훅
│   ├── types/               # TypeScript 타입
│   ├── utils/               # 유틸리티
│   └── styles/              # 스타일
├── public/
│   ├── themes/              # 브랜드별 테마
│   └── assets/              # 정적 자산
└── docs/                    # 사용 가이드
```

#### 1.3 메인 레이아웃 컴포넌트
```typescript
// src/components/layout/MainLayout.tsx
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { 
  HomeIcon, 
  UsersIcon, 
  CurrencyDollarIcon,
  ChartBarIcon,
  CogIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import Sidebar from './Sidebar';
import Header from './Header';
import { usePartnerConfig } from '@/hooks/usePartnerConfig';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { partnerConfig, loading } = usePartnerConfig();
  const router = useRouter();

  const navigation = [
    { name: '대시보드', href: '/dashboard', icon: HomeIcon },
    { name: '사용자 관리', href: '/users', icon: UsersIcon },
    { name: '지갑 관리', href: '/wallets', icon: CurrencyDollarIcon },
    { name: '분석', href: '/analytics', icon: ChartBarIcon },
    { name: '설정', href: '/settings', icon: CogIcon },
    { name: '지원', href: '/support', icon: QuestionMarkCircleIcon },
  ];

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
    </div>;
  }

  return (
    <div className="min-h-screen bg-gray-50" style={{ 
      '--primary-color': partnerConfig?.primary_color || '#3B82F6',
      '--secondary-color': partnerConfig?.secondary_color || '#1F2937'
    } as React.CSSProperties}>
      <Sidebar 
        navigation={navigation}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        partnerConfig={partnerConfig}
      />
      
      <div className="flex-1 md:pl-64">
        <Header 
          setSidebarOpen={setSidebarOpen}
          partnerConfig={partnerConfig}
        />
        
        <main className="py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
```

#### 1.4 사이드바 컴포넌트
```typescript
// src/components/layout/Sidebar.tsx
import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/router';
import Image from 'next/image';
import { PartnerConfig } from '@/types/partner';

interface SidebarProps {
  navigation: Array<{
    name: string;
    href: string;
    icon: React.ComponentType<any>;
  }>;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  partnerConfig: PartnerConfig | null;
}

const Sidebar: React.FC<SidebarProps> = ({
  navigation,
  sidebarOpen,
  setSidebarOpen,
  partnerConfig
}) => {
  const router = useRouter();

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* 로고 영역 */}
      <div className="flex items-center h-16 px-6 bg-white border-b border-gray-200">
        {partnerConfig?.logo_url ? (
          <Image
            src={partnerConfig.logo_url}
            alt={partnerConfig.company_name}
            width={120}
            height={40}
            className="h-8 w-auto"
          />
        ) : (
          <span className="text-xl font-bold text-gray-900">
            {partnerConfig?.company_name || 'DantaroWallet'}
          </span>
        )}
      </div>

      {/* 네비게이션 메뉴 */}
      <nav className="flex-1 px-4 py-6 space-y-1 bg-white">
        {navigation.map((item) => {
          const isActive = router.pathname.startsWith(item.href);
          return (
            <a
              key={item.name}
              href={item.href}
              className={`${
                isActive
                  ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              } group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200`}
              style={{
                backgroundColor: isActive ? `${partnerConfig?.primary_color}10` : undefined,
                color: isActive ? partnerConfig?.primary_color : undefined,
                borderRightColor: isActive ? partnerConfig?.primary_color : undefined
              }}
            >
              <item.icon
                className={`${
                  isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                } mr-3 flex-shrink-0 h-5 w-5`}
                style={{ color: isActive ? partnerConfig?.primary_color : undefined }}
              />
              {item.name}
            </a>
          );
        })}
      </nav>

      {/* 하단 정보 */}
      <div className="px-4 py-4 bg-gray-50 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Version 2.0.1 | {partnerConfig?.company_name}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* 모바일 사이드바 */}
      <Transition.Root show={sidebarOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50 md:hidden" onClose={setSidebarOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                  <button
                    type="button"
                    className="-m-2.5 p-2.5"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <XMarkIcon className="h-6 w-6 text-white" />
                  </button>
                </div>
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white">
                  <SidebarContent />
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* 데스크톱 사이드바 */}
      <div className="hidden md:fixed md:inset-y-0 md:z-50 md:flex md:w-64 md:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white">
          <SidebarContent />
        </div>
      </div>
    </>
  );
};

export default Sidebar;
```

### Phase 2: 대시보드 컴포넌트 구현 (2일)

#### 2.1 메인 대시보드
```typescript
// src/components/dashboard/MainDashboard.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import StatsCards from './StatsCards';
import RecentTransactions from './RecentTransactions';
import ActiveUsersChart from './ActiveUsersChart';
import RevenueChart from './RevenueChart';
import SystemStatus from './SystemStatus';
import QuickActions from './QuickActions';
import { dashboardService } from '@/services/dashboardService';

const MainDashboard: React.FC = () => {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getDashboardStats,
    refetchInterval: 30000, // 30초마다 업데이트
  });

  if (isLoading) {
    return <div className="animate-pulse space-y-6">
      {/* 로딩 스켈레톤 */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-gray-200 rounded-lg h-24"></div>
        ))}
      </div>
    </div>;
  }

  return (
    <div className="space-y-6">
      {/* 상단 통계 카드 */}
      <StatsCards stats={dashboardData?.stats} />

      {/* 빠른 액션 */}
      <QuickActions />

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ActiveUsersChart data={dashboardData?.userActivity} />
        <RevenueChart data={dashboardData?.revenue} />
      </div>

      {/* 하단 영역 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentTransactions transactions={dashboardData?.recentTransactions} />
        </div>
        <div>
          <SystemStatus status={dashboardData?.systemStatus} />
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
```

#### 2.2 통계 카드 컴포넌트
```typescript
// src/components/dashboard/StatsCards.tsx
import React from 'react';
import { 
  UsersIcon, 
  CurrencyDollarIcon, 
  ArrowTrendingUpIcon,
  BanknotesIcon 
} from '@heroicons/react/24/outline';
import { formatCurrency, formatNumber } from '@/utils/formatters';

interface Stats {
  totalUsers: number;
  activeUsers: number;
  totalRevenue: number;
  monthlyRevenue: number;
  totalTransactions: number;
  pendingTransactions: number;
  walletBalance: number;
  energyBalance: number;
}

interface StatsCardsProps {
  stats: Stats | undefined;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  const cards = [
    {
      name: '총 사용자',
      stat: stats?.totalUsers || 0,
      change: '+4.75%',
      changeType: 'positive',
      icon: UsersIcon,
      color: 'blue'
    },
    {
      name: '이번 달 수익',
      stat: formatCurrency(stats?.monthlyRevenue || 0),
      change: '+54.02%',
      changeType: 'positive',
      icon: CurrencyDollarIcon,
      color: 'green'
    },
    {
      name: '총 거래',
      stat: formatNumber(stats?.totalTransactions || 0),
      change: '-1.39%',
      changeType: 'negative',
      icon: ArrowTrendingUpIcon,
      color: 'purple'
    },
    {
      name: '지갑 잔액',
      stat: formatCurrency(stats?.walletBalance || 0),
      change: '+10.18%',
      changeType: 'positive',
      icon: BanknotesIcon,
      color: 'yellow'
    }
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-600 bg-blue-50',
      green: 'bg-green-500 text-green-600 bg-green-50',
      purple: 'bg-purple-500 text-purple-600 bg-purple-50',
      yellow: 'bg-yellow-500 text-yellow-600 bg-yellow-50'
    };
    return colors[color as keyof typeof colors];
  };

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const colorClasses = getColorClasses(card.color).split(' ');
        return (
          <div
            key={card.name}
            className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-200"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 ${colorClasses[2]} rounded-md flex items-center justify-center`}>
                    <card.icon className={`w-5 h-5 ${colorClasses[1]}`} />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {card.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {card.stat}
                      </div>
                      <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                        card.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {card.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatsCards;
```

### Phase 3: 사용자 관리 시스템 (1일)

#### 3.1 사용자 목록 컴포넌트
```typescript
// src/components/users/UserList.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon,
  EllipsisVerticalIcon 
} from '@heroicons/react/24/outline';
import { userService } from '@/services/userService';
import UserModal from './UserModal';
import UserFilters from './UserFilters';
import { formatDate, formatCurrency } from '@/utils/formatters';

const UserList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({});
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ['users', searchTerm, filters],
    queryFn: () => userService.getUsers({ search: searchTerm, ...filters }),
  });

  const updateUserMutation = useMutation({
    mutationFn: userService.updateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
    },
  });

  const handleUserClick = (user: any) => {
    setSelectedUser(user);
    setShowModal(true);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">사용자 관리</h1>
          <p className="mt-2 text-sm text-gray-700">
            총 {users?.total || 0}명의 사용자가 등록되어 있습니다.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:w-auto"
          >
            사용자 추가
          </button>
        </div>
      </div>

      {/* 검색 및 필터 */}
      <div className="bg-white shadow rounded-lg">
        <div className="p-6 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0 sm:space-x-4">
            {/* 검색 */}
            <div className="flex-1 min-w-0">
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
                  placeholder="사용자 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            
            {/* 필터 버튼 */}
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <FunnelIcon className="h-5 w-5 mr-2" />
              필터
            </button>
          </div>

          {/* 필터 패널 */}
          {showFilters && (
            <div className="mt-4">
              <UserFilters filters={filters} onFiltersChange={setFilters} />
            </div>
          )}
        </div>

        {/* 사용자 테이블 */}
        <div className="overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  사용자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  지갑 잔액
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  가입일
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">액션</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users?.data?.map((user: any) => (
                <tr 
                  key={user.id} 
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleUserClick(user)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {user.username?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {user.username}
                        </div>
                        <div className="text-sm text-gray-500">
                          {user.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(user.wallet_balance || 0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? '활성' : '비활성'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-gray-400 hover:text-gray-500">
                      <EllipsisVerticalIcon className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 사용자 상세 모달 */}
      {showModal && selectedUser && (
        <UserModal
          user={selectedUser}
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          onUpdate={(data) => updateUserMutation.mutate({ id: selectedUser.id, ...data })}
        />
      )}
    </div>
  );
};

export default UserList;
```

### Phase 4: 브랜딩 및 테마 시스템 (1일)

#### 4.1 테마 구성 시스템
```typescript
// src/hooks/usePartnerConfig.ts
import { useQuery } from '@tanstack/react-query';
import { partnerService } from '@/services/partnerService';

export interface PartnerConfig {
  id: number;
  company_name: string;
  logo_url: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  custom_css: string;
  domain: string;
  favicon_url: string;
  background_image: string;
  theme_mode: 'light' | 'dark' | 'auto';
}

export const usePartnerConfig = () => {
  const { data: partnerConfig, isLoading, error } = useQuery({
    queryKey: ['partner-config'],
    queryFn: partnerService.getPartnerConfig,
    staleTime: 5 * 60 * 1000, // 5분간 캐시
  });

  return {
    partnerConfig,
    loading: isLoading,
    error
  };
};
```

#### 4.2 동적 테마 적용
```typescript
// src/components/common/ThemeProvider.tsx
import React, { useEffect } from 'react';
import { usePartnerConfig } from '@/hooks/usePartnerConfig';

interface ThemeProviderProps {
  children: React.ReactNode;
}

const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const { partnerConfig } = usePartnerConfig();

  useEffect(() => {
    if (partnerConfig) {
      const root = document.documentElement;
      
      // CSS 변수 설정
      root.style.setProperty('--primary-color', partnerConfig.primary_color);
      root.style.setProperty('--secondary-color', partnerConfig.secondary_color);
      root.style.setProperty('--accent-color', partnerConfig.accent_color);
      
      // 폰트 적용
      if (partnerConfig.font_family) {
        root.style.setProperty('--font-family', partnerConfig.font_family);
      }
      
      // 파비콘 업데이트
      if (partnerConfig.favicon_url) {
        const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
        if (favicon) {
          favicon.href = partnerConfig.favicon_url;
        }
      }
      
      // 페이지 타이틀 업데이트
      document.title = `${partnerConfig.company_name} - 관리자 대시보드`;
      
      // 커스텀 CSS 적용
      if (partnerConfig.custom_css) {
        const styleElement = document.createElement('style');
        styleElement.textContent = partnerConfig.custom_css;
        document.head.appendChild(styleElement);
        
        return () => {
          document.head.removeChild(styleElement);
        };
      }
    }
  }, [partnerConfig]);

  return <>{children}</>;
};

export default ThemeProvider;
```

### Phase 5: 배포 및 커스터마이징 가이드 (1일)

#### 5.1 환경별 설정 파일
```typescript
// src/config/environment.ts
export interface Environment {
  API_BASE_URL: string;
  PARTNER_ID: string;
  WEBSOCKET_URL: string;
  TRON_NETWORK: 'mainnet' | 'testnet';
  ENABLE_ANALYTICS: boolean;
  ENABLE_NOTIFICATIONS: boolean;
  THEME_CUSTOMIZATION_ENABLED: boolean;
}

const environments: Record<string, Environment> = {
  development: {
    API_BASE_URL: 'http://localhost:8000/api/v1',
    PARTNER_ID: process.env.NEXT_PUBLIC_PARTNER_ID || '',
    WEBSOCKET_URL: 'ws://localhost:8000/ws',
    TRON_NETWORK: 'testnet',
    ENABLE_ANALYTICS: true,
    ENABLE_NOTIFICATIONS: true,
    THEME_CUSTOMIZATION_ENABLED: true,
  },
  production: {
    API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || '',
    PARTNER_ID: process.env.NEXT_PUBLIC_PARTNER_ID || '',
    WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL || '',
    TRON_NETWORK: 'mainnet',
    ENABLE_ANALYTICS: true,
    ENABLE_NOTIFICATIONS: true,
    THEME_CUSTOMIZATION_ENABLED: false,
  }
};

export const getEnvironment = (): Environment => {
  const env = process.env.NODE_ENV || 'development';
  return environments[env] || environments.development;
};
```

#### 5.2 자동 배포 스크립트
```bash
#!/bin/bash
# scripts/deploy-partner-template.sh

set -e

PARTNER_ID=$1
PARTNER_DOMAIN=$2
PARTNER_CONFIG=$3

if [ -z "$PARTNER_ID" ] || [ -z "$PARTNER_DOMAIN" ] || [ -z "$PARTNER_CONFIG" ]; then
    echo "사용법: $0 <PARTNER_ID> <PARTNER_DOMAIN> <PARTNER_CONFIG_JSON>"
    exit 1
fi

echo "파트너 템플릿 배포 시작: $PARTNER_ID"

# 1. 새 디렉토리 생성
DEPLOY_DIR="/var/www/partners/$PARTNER_ID"
mkdir -p $DEPLOY_DIR

# 2. 템플릿 복사
cp -r partner-admin-template/* $DEPLOY_DIR/

# 3. 환경 설정 파일 생성
cat > $DEPLOY_DIR/.env.local << EOF
NEXT_PUBLIC_PARTNER_ID=$PARTNER_ID
NEXT_PUBLIC_API_BASE_URL=https://api.dantarowallet.com/api/v1
NEXT_PUBLIC_WEBSOCKET_URL=wss://api.dantarowallet.com/ws
NODE_ENV=production
EOF

# 4. 파트너별 커스터마이징 적용
echo $PARTNER_CONFIG > $DEPLOY_DIR/partner-config.json

# 5. 의존성 설치 및 빌드
cd $DEPLOY_DIR
npm ci
npm run build

# 6. PM2로 서비스 시작
pm2 start ecosystem.config.js --name "partner-$PARTNER_ID"

# 7. Nginx 설정 생성
cat > /etc/nginx/sites-available/partner-$PARTNER_ID << EOF
server {
    listen 80;
    server_name $PARTNER_DOMAIN;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 8. Nginx 설정 활성화
ln -sf /etc/nginx/sites-available/partner-$PARTNER_ID /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 9. SSL 인증서 설정 (Let's Encrypt)
certbot --nginx -d $PARTNER_DOMAIN --non-interactive --agree-tos --email admin@dantarowallet.com

echo "파트너 템플릿 배포 완료: https://$PARTNER_DOMAIN"
```

## 📚 커스터마이징 가이드

### 브랜딩 커스터마이징
```markdown
# 파트너 브랜딩 가이드

## 1. 로고 및 색상 설정

### 로고 업로드
- 권장 크기: 200x60px (SVG 또는 PNG)
- 배경: 투명 권장
- 파일 크기: 500KB 이하

### 색상 팔레트
- 주 색상 (Primary): 버튼, 링크, 강조 요소
- 보조 색상 (Secondary): 헤더, 사이드바
- 액센트 색상 (Accent): 알림, 상태 표시

## 2. 폰트 커스터마이징

### 지원 폰트
- Google Fonts 전체 지원
- 웹 안전 폰트 지원
- 커스텀 폰트 업로드 가능

### 설정 방법
```json
{
  "font_family": "Inter, system-ui, sans-serif",
  "font_weights": ["400", "500", "600", "700"]
}
```

## 3. 레이아웃 커스터마이징

### 사이드바 설정
- 메뉴 항목 추가/제거
- 아이콘 변경
- 순서 조정

### 대시보드 위젯
- 표시할 위젯 선택
- 위젯 순서 조정
- 커스텀 위젯 추가
```

## ✅ 검증 체크리스트

### 기능 테스트
- [ ] 모든 페이지 정상 렌더링
- [ ] 사용자 관리 CRUD 동작
- [ ] 지갑 관리 기능 동작
- [ ] 실시간 데이터 업데이트
- [ ] 브랜딩 적용 확인
- [ ] 반응형 디자인 동작
- [ ] 접근성 준수
- [ ] 다국어 지원 (선택사항)

### 성능 테스트
- [ ] 페이지 로딩 시간 < 3초
- [ ] 대용량 데이터 처리 성능
- [ ] 메모리 사용량 최적화
- [ ] 번들 크기 최적화

### 보안 검증
- [ ] XSS 방지
- [ ] CSRF 방지
- [ ] 인증/인가 구현
- [ ] 민감 정보 보호

## 📈 예상 효과

### 파트너사 관점
- **브랜드 일관성**: 자사 브랜딩으로 통일된 경험
- **운영 효율성**: 직관적인 관리 인터페이스
- **사용자 관리**: 체계적인 사용자 데이터 관리
- **비즈니스 인사이트**: 실시간 분석 및 리포트

### 본사 관점
- **표준화**: 일관된 파트너 경험 제공
- **확장성**: 쉬운 파트너 온보딩
- **유지보수**: 중앙화된 템플릿 관리
- **품질 보장**: 검증된 UI/UX 제공

이 파트너 관리자 UI 템플릿은 각 파트너사가 자신만의 브랜드 아이덴티티를 유지하면서도 강력한 관리 기능을 제공받을 수 있도록 설계되었습니다.
