export interface DashboardStats {
  totalUsers: number
  totalBalance: number
  totalTransactions: number
  totalRevenue: number
  dailyGrowth: number
  weeklyGrowth: number
  monthlyGrowth: number
}

export interface AssetBalance {
  symbol: string
  balance: number
  value: number
  change24h: number
}

export interface TransactionHistory {
  id: string
  type: 'deposit' | 'withdrawal' | 'transfer'
  amount: number
  currency: string
  from: string
  to: string
  status: 'pending' | 'completed' | 'failed'
  timestamp: string
  txHash?: string
}

export interface WithdrawalRequest {
  id: string
  user_id: string
  user_name: string
  amount: number
  currency: string
  destination_address: string
  status: 'pending' | 'approved' | 'rejected' | 'processing' | 'completed' | 'failed'
  request_time: string
  processed_time?: string
  transaction_hash?: string
  fee: number
  fee_currency: 'USDT' | 'TRX'
  approved_by?: string
  batch_id?: string
  // Legacy field aliases for backward compatibility
  userId?: string
  address?: string
  requestedAt?: string
  processedAt?: string
  batchId?: string
}

export interface User {
  id: string
  email: string
  username: string
  walletAddress: string
  wallet_address?: string // alias for walletAddress
  balance: number
  status: 'active' | 'inactive' | 'suspended' | 'pending'
  kycStatus: 'pending' | 'approved' | 'rejected' | 'not_started' | 'none'
  kyc_status?: 'pending' | 'approved' | 'rejected' | 'none' // alias for kycStatus
  createdAt: string
  created_at?: string // alias for createdAt
  lastLogin: string
  last_login?: string // alias for lastLogin
  totalTransactions: number
  totalVolume: number
  phone?: string
  tier?: 'basic' | 'premium' | 'vip'
  referral_code?: string
  referred_by?: string
}

export interface KYCDocument {
  id: string
  userId: string
  type: 'identity' | 'address' | 'selfie'
  status: 'pending' | 'approved' | 'rejected'
  fileUrl: string
  submittedAt: string
  reviewedAt?: string
  reviewedBy?: string
  notes?: string
}

export interface PartnerInfo {
  id: string
  name: string
  email: string
  walletAddress: string
  apiKey: string
  apiSecret: string
  permissions: string[]
  createdAt: string
  lastActive: string
  status: 'active' | 'inactive'
}

export interface Notification {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  read: boolean
  actionUrl?: string
}

export interface WalletConnection {
  address: string
  connected: boolean
  network: string
  balance: number
  provider: 'tronlink' | 'walletconnect'
}

export interface BatchOperation {
  id: string
  type: 'withdrawal' | 'distribution'
  status: 'pending' | 'ready' | 'processing' | 'completed' | 'failed'
  totalAmount: number
  totalCount: number
  createdAt: string
  processedAt?: string
  transactions: TransactionHistory[]
}

export interface AnalyticsData {
  period: string
  revenue: number
  expenses: number
  profit: number
  userGrowth: number
  transactionVolume: number
}

export interface AlertSetting {
  id: string
  type: 'balance' | 'transaction' | 'user'
  threshold: number
  enabled: boolean
  notifyEmail: boolean
  notifyApp: boolean
}

// 인증 관련 타입
export interface LoginCredentials {
  email: string
  password: string
  remember_me?: boolean
}

export interface RegisterData {
  email: string
  username: string
  password: string
  password_confirmation: string
  terms_accepted: boolean
  privacy_accepted: boolean
}

export interface AuthResponse {
  success: boolean
  message: string
  data: {
    access_token: string
    refresh_token: string
    user: User
    expires_in: number
  }
}

export interface AuthUser extends User {
  role: 'admin' | 'partner' | 'user'
  permissions: string[]
  last_password_change?: string
  two_factor_enabled: boolean
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  new_password_confirmation: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  password: string
  password_confirmation: string
}

// API 응답 공통 타입
export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T
  status_code: number
  errors?: Record<string, string[]>
  pagination?: {
    current_page: number
    total_pages: number
    total_count: number
    per_page: number
  }
}

// 에러 관련 타입
export interface ApiError {
  status_code: number
  message: string
  errors?: Record<string, string[]>
  timestamp: string
  path: string
}

export interface ValidationError {
  field: string
  message: string
}

// 대시보드 전용 인터페이스
export interface ChartData {
  name: string
  value: number
  date?: string
  label?: string
}
