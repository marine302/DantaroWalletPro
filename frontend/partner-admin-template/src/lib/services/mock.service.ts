/**
 * 개발용 임시 데이터 및 Mock API 서비스
 * 실제 백엔드 연동 전까지 사용할 Mock 데이터
 */

import type { 
  AuthResponse, 
  AuthUser, 
  DashboardStats, 
  User, 
  WithdrawalRequest,
  TransactionHistory,
  EnergyPool
} from '../../types';

// 개발용 임시 파트너 계정 데이터
export const DEMO_PARTNER_ACCOUNT: AuthUser = {
  id: 'partner_001',
  email: 'partner@dantarowallet.com',
  username: 'dantaro_partner_admin',
  walletAddress: 'TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE',
  balance: 1250000,
  status: 'active',
  kycStatus: 'approved',
  createdAt: '2024-01-15T10:00:00Z',
  lastLogin: new Date().toISOString(),
  totalTransactions: 1543,
  totalVolume: 25000000,
  role: 'partner',
  permissions: [
    'dashboard.view',
    'users.view',
    'users.manage',
    'withdrawals.view',
    'withdrawals.approve',
    'analytics.view',
    'energy.view',
    'energy.manage',
    'notifications.view',
    'settings.manage'
  ],
  two_factor_enabled: true
};

// Mock 대시보드 통계 데이터
export const MOCK_DASHBOARD_STATS: DashboardStats = {
  totalUsers: 12847,
  totalBalance: 45672341.23,
  totalTransactions: 89234,
  totalRevenue: 567891.45,
  dailyGrowth: 3.2,
  weeklyGrowth: 12.8,
  monthlyGrowth: 28.4
};

// Mock 사용자 목록 데이터
export const MOCK_USERS: User[] = [
  {
    id: 'user_001',
    email: 'john.doe@example.com',
    username: 'johndoe',
    walletAddress: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    balance: 15780.50,
    status: 'active',
    kycStatus: 'approved',
    createdAt: '2024-07-01T09:30:00Z',
    lastLogin: '2024-07-21T14:25:00Z',
    totalTransactions: 89,
    totalVolume: 234567.89
  },
  {
    id: 'user_002',
    email: 'jane.smith@example.com',
    username: 'janesmith',
    walletAddress: 'TLyqzVGLV1srkB7dToTAEqgDSfPtXSRJZY',
    balance: 8942.15,
    status: 'active',
    kycStatus: 'pending',
    createdAt: '2024-07-15T16:45:00Z',
    lastLogin: '2024-07-21T10:15:00Z',
    totalTransactions: 23,
    totalVolume: 45892.34
  }
];

// Mock 출금 요청 데이터
export const MOCK_WITHDRAWAL_REQUESTS: WithdrawalRequest[] = [
  {
    id: 'wd_001',
    userId: 'user_001',
    amount: 5000,
    currency: 'USDT',
    address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    status: 'pending',
    requestedAt: '2024-07-21T08:30:00Z'
  },
  {
    id: 'wd_002',
    userId: 'user_002',
    amount: 2500,
    currency: 'TRX',
    address: 'TLyqzVGLV1srkB7dToTAEqgDSfPtXSRJZY',
    status: 'approved',
    requestedAt: '2024-07-20T15:20:00Z',
    processedAt: '2024-07-21T09:15:00Z',
    approvedBy: 'partner_001'
  }
];

// Mock 거래 내역 데이터
export const MOCK_TRANSACTIONS: TransactionHistory[] = [
  {
    id: 'tx_001',
    type: 'deposit',
    amount: 10000,
    currency: 'USDT',
    from: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    to: 'TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE',
    status: 'completed',
    timestamp: '2024-07-21T12:00:00Z',
    txHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
  },
  {
    id: 'tx_002',
    type: 'withdrawal',
    amount: 5000,
    currency: 'USDT',
    from: 'TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE',
    to: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    status: 'pending',
    timestamp: '2024-07-21T08:30:00Z'
  }
];

// Mock 에너지 풀 데이터
export const MOCK_ENERGY_POOL: EnergyPool = {
  totalEnergy: 500000,
  availableEnergy: 325000,
  stakeAmount: 1000000,
  freezeAmount: 750000,
  dailyConsumption: 15000,
  efficiency: 95.5,
  status: 'active'
};

/**
 * Mock 인증 서비스 (실제 백엔드 연동 전까지 사용)
 */
export const mockAuthService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    // 개발용 계정 정보와 비교
    if (
      email === DEMO_PARTNER_ACCOUNT.email && 
      password === process.env.NEXT_PUBLIC_DEMO_PASSWORD
    ) {
      return {
        success: true,
        message: 'Login successful',
        data: {
          access_token: 'mock_jwt_token_' + Date.now(),
          refresh_token: 'mock_refresh_token_' + Date.now(),
          user: DEMO_PARTNER_ACCOUNT,
          expires_in: 86400 // 24시간
        }
      };
    } else {
      return {
        success: false,
        message: 'Invalid credentials',
        data: {
          access_token: '',
          refresh_token: '',
          user: {} as AuthUser,
          expires_in: 0
        }
      };
    }
  },

  async register(email: string, username: string): Promise<AuthResponse> {
    // Mock 회원가입 성공 응답
    const newUser: AuthUser = {
      ...DEMO_PARTNER_ACCOUNT,
      id: 'partner_' + Date.now(),
      email,
      username,
      createdAt: new Date().toISOString(),
      lastLogin: new Date().toISOString()
    };

    return {
      success: true,
      message: 'Registration successful',
      data: {
        access_token: 'mock_jwt_token_' + Date.now(),
        refresh_token: 'mock_refresh_token_' + Date.now(),
        user: newUser,
        expires_in: 86400
      }
    };
  }
};

/**
 * 개발 환경에서 Mock 데이터 사용 여부 확인
 */
export const shouldUseMockData = (): boolean => {
  return process.env.NEXT_PUBLIC_ENV === 'development' && 
         process.env.NEXT_PUBLIC_USE_MOCK_DATA !== 'false';
};
