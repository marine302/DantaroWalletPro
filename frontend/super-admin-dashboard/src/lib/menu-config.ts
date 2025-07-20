import { 
  BarChart3, 
  Settings, 
  Users, 
  Zap, 
  DollarSign, 
  Shield, 
  UserPlus,
  TrendingUp,
  Activity,
  Target,
  FileText,
  Bell
} from 'lucide-react';

export interface MenuItem {
  id: string;
  labelKey: string; // 언어팩 키로 변경
  icon: any;
  href: string;
  badge?: string;
  children?: MenuItem[];
  requiredPermissions?: string[];
  description?: string;
}

// 다국어 지원을 위한 메뉴 설정 함수
export const getMenuConfig = (t: any): MenuItem[] => [
  {
    id: 'dashboard',
    labelKey: 'nav.dashboard',
    icon: BarChart3,
    href: '/',
    description: t.nav.dashboardDesc || '통합 대시보드 및 실시간 현황'
  },
  {
    id: 'integrated-dashboard',
    labelKey: 'nav.integratedDashboard',
    icon: Target,
    href: '/integrated-dashboard',
    description: t.nav.integratedDashboardDesc || '통합 운영 대시보드'
  },
  {
    id: 'analytics',
    labelKey: 'nav.analytics',
    icon: TrendingUp,
    href: '/analytics',
    description: t.nav.analyticsDesc || '데이터 분석 및 리포트'
  },
  {
    id: 'energy',
    labelKey: 'nav.energy',
    icon: Zap,
    href: '/energy',
    description: t.nav.energyDesc || '에너지 거래 및 관리',
    children: [
      {
        id: 'energy-overview',
        labelKey: 'nav.energyOverview',
        icon: Activity,
        href: '/energy',
        description: t.nav.energyOverviewDesc || '에너지 거래 현황'
      },
      {
        id: 'energy-market',
        labelKey: 'nav.energyMarket',
        icon: TrendingUp,
        href: '/energy-market',
        description: t.nav.energyMarketDesc || '에너지 마켓 현황'
      },
      {
        id: 'external-market',
        labelKey: 'nav.externalMarket',
        icon: Target,
        href: '/energy/external-market',
        description: t.nav.externalMarketDesc || '외부 마켓 연동'
      },
      {
        id: 'auto-purchase',
        labelKey: 'nav.autoPurchase',
        icon: Zap,
        href: '/energy/auto-purchase',
        description: t.nav.autoPurchaseDesc || '자동 구매 설정'
      },
      {
        id: 'purchase-history',
        labelKey: 'nav.purchaseHistory',
        icon: FileText,
        href: '/energy/purchase-history',
        description: t.nav.purchaseHistoryDesc || '구매 이력 조회'
      }
    ]
  },
  {
    id: 'partners',
    labelKey: 'nav.partners',
    icon: Users,
    href: '/partners',
    description: t.nav.partnersDesc || '파트너 관리'
  },
  {
    id: 'partner-onboarding',
    labelKey: 'nav.partnerOnboarding',
    icon: UserPlus,
    href: '/partner-onboarding',
    description: t.nav.partnerOnboardingDesc || '파트너 온보딩 관리'
  },
  {
    id: 'admins',
    labelKey: 'nav.admins',
    icon: Shield,
    href: '/admins',
    description: t.nav.adminsDesc || '관리자 계정 관리',
    requiredPermissions: ['admin.manage']
  },
  {
    id: 'fees',
    labelKey: 'nav.fees',
    icon: DollarSign,
    href: '/fees',
    description: t.nav.feesDesc || '수수료 관리'
  },
  {
    id: 'audit-compliance',
    labelKey: 'nav.auditCompliance',
    icon: FileText,
    href: '/audit-compliance',
    description: t.nav.auditComplianceDesc || '감사 및 컴플라이언스'
  },
  {
    id: 'settings',
    labelKey: 'nav.settings',
    icon: Settings,
    href: '/settings',
    description: t.nav.settingsDesc || '시스템 설정'
  },
  // 개발/테스트 메뉴 (개발 환경에서만 표시)
  ...(process.env.NODE_ENV === 'development' ? [
    {
      id: 'dev-tools',
      labelKey: 'nav.devTools',
      icon: Activity,
      href: '#',
      description: t.nav.devToolsDesc || '개발 도구',
      children: [
        {
          id: 'notification-test',
          labelKey: 'nav.notificationTest',
          icon: Bell,
          href: '/notification-test',
          description: t.nav.notificationTestDesc || '알림 시스템 테스트'
        },
        {
          id: 'websocket-test',
          labelKey: 'nav.websocketTest',
          icon: Activity,
          href: '/websocket-test',
          description: t.nav.websocketTestDesc || 'WebSocket 연결 테스트'
        },
        {
          id: 'debug',
          labelKey: 'nav.debug',
          icon: FileText,
          href: '/debug',
          description: t.nav.debugDesc || '디버그 정보 및 로그'
        }
      ]
    }
  ] : [])
];

export function getMenuItemById(id: string, menuItems: MenuItem[]): MenuItem | undefined {
  function findItem(items: MenuItem[]): MenuItem | undefined {
    for (const item of items) {
      if (item.id === id) return item;
      if (item.children) {
        const found = findItem(item.children);
        if (found) return found;
      }
    }
    return undefined;
  }
  return findItem(menuItems);
}

export function getMenuPath(id: string, menuItems: MenuItem[]): MenuItem[] {
  function findPath(items: MenuItem[], targetId: string, currentPath: MenuItem[] = []): MenuItem[] | null {
    for (const item of items) {
      const newPath = [...currentPath, item];
      if (item.id === targetId) return newPath;
      
      if (item.children) {
        const found = findPath(item.children, targetId, newPath);
        if (found) return found;
      }
    }
    return null;
  }
  return findPath(menuItems, id) || [];
}

export function filterMenuByPermissions(items: MenuItem[], userPermissions: string[]): MenuItem[] {
  return items.filter(item => {
    // 권한이 필요하지 않거나, 사용자가 필요한 권한을 가지고 있는 경우
    const hasPermission = !item.requiredPermissions || 
      item.requiredPermissions.some(permission => userPermissions.includes(permission));
    
    if (!hasPermission) return false;
    
    // 자식 메뉴가 있는 경우 재귀적으로 필터링
    if (item.children) {
      item.children = filterMenuByPermissions(item.children, userPermissions);
    }
    
    return true;
  });
}
