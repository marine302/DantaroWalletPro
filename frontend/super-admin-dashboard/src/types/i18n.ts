// 다국어 지원을 위한 타입 정의
export type Locale = 'ko' | 'en';

export interface TranslationMessages {
  // 공통
  common: {
    loading: string;
    error: string;
    retry: string;
    save: string;
    cancel: string;
    delete: string;
    edit: string;
    add: string;
    search: string;
    filter: string;
    actions: string;
    status: string;
    created: string;
    updated: string;
    name: string;
    email: string;
    domain: string;
    refresh: string;
    viewAll: string;
    viewDetails: string;
    configure: string;
    manage: string;
    overview: string;
    statistics: string;
    history: string;
    reports: string;
    notifications: string;
    profile: string;
    security: string;
    language: string;
    close: string;
    submit: string;
    confirm: string;
    yes: string;
    no: string;
    back: string;
    next: string;
    previous: string;
    success: string;
    warning: string;
    info: string;
  };
  
  // 네비게이션
  nav: {
    dashboard: string;
    dashboardDesc: string;
    partners: string;
    partnersDesc: string;
    settings: string;
    settingsDesc: string;
    energy: string;
    energyDesc: string;
    energyOverview: string;
    energyOverviewDesc: string;
    analytics: string;
    analyticsDesc: string;
    admins: string;
    adminsDesc: string;
    fees: string;
    feesDesc: string;
    auditCompliance: string;
    auditComplianceDesc: string;
    energyMarket: string;
    energyMarketDesc: string;
    partnerOnboarding: string;
    partnerOnboardingDesc: string;
    integratedDashboard: string;
    integratedDashboardDesc: string;
    externalMarket: string;
    externalMarketDesc: string;
    autoPurchase: string;
    autoPurchaseDesc: string;
    purchaseHistory: string;
    purchaseHistoryDesc: string;
    devTools: string;
    devToolsDesc: string;
    notificationTest: string;
    notificationTestDesc: string;
    websocketTest: string;
    websocketTestDesc: string;
    debug: string;
    debugDesc: string;
    logout: string;
  };
    partnerOnboarding: string;
    integratedDashboard: string;
    logout: string;
  };
  
  // 파트너 관리
  partners: {
    title: string;
    description: string;
    addPartner: string;
    partnerList: string;
    noPartnersFound: string;
    loadingPartners: string;
    failedToLoad: string;
    partner: string;
    totalTransactions: string;
    totalVolume: string;
    feeRate: string;
    lastActivity: string;
    active: string;
    pending: string;
    suspended: string;
    totalPartners: string;
    activePartners: string;
    pendingApproval: string;
    monthlyRevenue: string;
  };
  
  // 대시보드
  dashboard: {
    title: string;
    description: string;
    welcomeBack: string;
    totalRevenue: string;
    activePartners: string;
    totalTransactions: string;
    systemHealth: string;
    recentActivity: string;
    quickActions: string;
    totalPartners: string;
    availableEnergy: string;
    dailyVolume: string;
    totalEnergy: string;
    transactionsToday: string;
    activeWallets: string;
    recentPartners: string;
    noPartnersFound: string;
    addPartner: string;
    healthy: string;
    critical: string;
  };
  
  // 에너지 관리
  energy: {
    title: string;
    description: string;
    currentPool: string;
    totalEnergy: string;
    availableEnergy: string;
    reservedEnergy: string;
    usageRate: string;
    quickActions: string;
    autoPurchase: string;
    externalMarket: string;
    recentTransactions: string;
    purchaseHistory: string;
    energyDistribution: string;
    alerts: string;
    configure: string;
    autoEnergyPurchasing: string;
    externalEnergyMarket: string;
    purchaseEnergyExternal: string;
  };
  
  // 수수료 관리
  fees: {
    title: string;
    description: string;
    currentRates: string;
    totalRevenue: string;
    monthlyRevenue: string;
    partnerCommission: string;
    systemFee: string;
    configurations: string;
    history: string;
    reports: string;
    updateRates: string;
    addConfig: string;
    feeConfiguration: string;
    revenueOverview: string;
    recentTransactions: string;
  };
  
  // 분석
  analytics: {
    title: string;
    description: string;
    transactionVolume: string;
    userGrowth: string;
    revenueAnalysis: string;
    partnerPerformance: string;
    systemMetrics: string;
    realTimeData: string;
    trends: string;
    insights: string;
    downloadReport: string;
    transactionAnalytics: string;
    performanceMetrics: string;
    recentActivity: string;
  };
  
  // 관리자 관리
  admins: {
    title: string;
    description: string;
    addAdministrator: string;
    superAdmins: string;
    systemAdmins: string;
    supportStaff: string;
    administratorList: string;
    rolePermissions: string;
    recentActivity: string;
    administrator: string;
    role: string;
    status: string;
    lastLogin: string;
    actions: string;
    active: string;
    suspended: string;
    enable: string;
    disable: string;
    recentAdminActivity: string;
  };
  
  // 통합 대시보드
  integratedDashboard: {
    title: string;
    description: string;
    partnerId: string;
    fetchError: string;
    noData: string;
    sections: {
      walletOverview: string;
      transactionFlow: string;
      energyStatus: string;
      walletDistribution: string;
      userAnalytics: string;
      revenueMetrics: string;
    };
    walletOverview: {
      totalBalance: string;
      walletCount: string;
      securityScore: string;
      diversificationIndex: string;
    };
    transactionFlow: {
      dailyTransactions: string;
      totalVolume: string;
      avgAmount: string;
      trend: string;
    };
    energyStatus: {
      totalEnergy: string;
      availableEnergy: string;
      usageRate: string;
      efficiency: string;
    };
    walletDistribution: {
      hotWallet: string;
      warmWallet: string;
      coldWallet: string;
    };
    userAnalytics: {
      totalUsers: string;
      activeUsers: string;
      newUsers: string;
      retentionRate: string;
    };
    revenueMetrics: {
      totalRevenue: string;
      commissionEarned: string;
      profitMargin: string;
      growthRate: string;
    };
  };
  
  // 감사 및 컴플라이언스
  auditCompliance: {
    title: string;
    description: string;
    auditLog: string;
    suspiciousActivities: string;
    complianceCheck: string;
    reports: string;
    alerts: string;
    investigations: string;
    complianceMetrics: string;
    auditTrail: string;
    securityIncidents: string;
  };
  
  // 파트너 온보딩
  partnerOnboarding: {
    title: string;
    description: string;
    newApplication: string;
    pendingReview: string;
    documentation: string;
    testing: string;
    approval: string;
    completed: string;
    onboardingProcess: string;
    partnerApplication: string;
    reviewStatus: string;
  };
  
  // 에너지 마켓
  energyMarket: {
    title: string;
    description: string;
    marketplace: string;
    trading: string;
    priceChart: string;
    orderBook: string;
    tradeHistory: string;
    buyEnergy: string;
    sellEnergy: string;
    marketOverview: string;
    tradingInterface: string;
    marketData: string;
  };
  
  // 설정
  settings: {
    title: string;
    description: string;
    language: string;
    theme: string;
    notifications: string;
    security: string;
    selectLanguage: string;
    general: string;
    integrations: string;
    backup: string;
    maintenance: string;
    systemConfig: string;
    userPreferences: string;
    apiSettings: string;
    updateSettings: string;
    systemSettings: string;
    advancedSettings: string;
  };
}

// i18n 컨텍스트 타입
export interface I18nContextType {
  language: Locale;
  setLanguage: (language: Locale) => void;
  t: TranslationMessages;
}
