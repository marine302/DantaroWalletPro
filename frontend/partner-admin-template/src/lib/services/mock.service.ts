// Mock 서비스 - 빌드용 스텁
export const MockService = {
  login: async (email: string, _password: string) => ({ 
    success: true,
    message: 'Login successful',
    data: { 
      access_token: 'mock_access_token', 
      refresh_token: 'mock_refresh_token',
      user: { 
        id: '1',
        email,
        username: email.split('@')[0],
        walletAddress: 'TXXXmockwalletaddress',
        balance: 1000,
        status: 'active' as const,
        kycStatus: 'approved' as const,
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
        totalTransactions: 0,
        totalVolume: 0
      },
      expires_in: 3600
    } 
  }),
  register: async (email: string, username: string, _password: string) => ({ 
    success: true,
    message: 'Registration successful', 
    data: { 
      access_token: 'mock_access_token', 
      refresh_token: 'mock_refresh_token',
      user: { 
        id: '1',
        email,
        username,
        walletAddress: 'TXXXmockwalletaddress',
        balance: 0,
        status: 'active' as const,
        kycStatus: 'not_started' as const,
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
        totalTransactions: 0,
        totalVolume: 0
      },
      expires_in: 3600
    } 
  }),
  getDashboardStats: () => ({
    totalUsers: 12847,
    totalBalance: 45672341.23,
    totalTransactions: 89234,
    totalRevenue: 567891.45,
    dailyGrowth: 3.2,
    weeklyGrowth: 12.8,
    monthlyGrowth: 28.4
  })
};

export const MOCK_DASHBOARD_STATS = MockService.getDashboardStats();

// auth.service.ts에서 필요한 exports
export const shouldUseMockData = () => true;
export const mockAuthService = MockService;

export const DEMO_PARTNER_ACCOUNT = {
  id: '1',
  email: 'demo@partner.com',
  username: 'demo_partner',
  walletAddress: 'TXXXmockwalletaddress',
  balance: 5000,
  status: 'active' as const,
  kycStatus: 'approved' as const,
  createdAt: new Date().toISOString(),
  lastLogin: new Date().toISOString(),
  totalTransactions: 150,
  totalVolume: 50000
};

export default MockService;
