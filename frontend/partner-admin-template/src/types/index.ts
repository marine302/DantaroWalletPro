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

export interface EnergyPool {
  totalEnergy: number
  availableEnergy: number
  stakeAmount: number
  freezeAmount: number
  dailyConsumption: number
  efficiency: number
  status: 'active' | 'inactive' | 'warning'
}

export interface TransactionHistory {
  id: string
  type: 'deposit' | 'withdrawal' | 'transfer' | 'energy'
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
  userId: string
  amount: number
  currency: string
  address: string
  status: 'pending' | 'approved' | 'rejected' | 'processing' | 'completed'
  requestedAt: string
  processedAt?: string
  approvedBy?: string
  batchId?: string
}

export interface User {
  id: string
  email: string
  username: string
  walletAddress: string
  balance: number
  status: 'active' | 'inactive' | 'suspended'
  kycStatus: 'pending' | 'approved' | 'rejected' | 'not_started'
  createdAt: string
  lastLogin: string
  totalTransactions: number
  totalVolume: number
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
  energyUsage: number
}

export interface AlertSetting {
  id: string
  type: 'balance' | 'energy' | 'transaction' | 'user'
  threshold: number
  enabled: boolean
  notifyEmail: boolean
  notifyApp: boolean
}

// 에너지 관리 타입
export interface EnergyPoolInfo {
  id: string
  name: string
  total_capacity: number
  available_capacity: number
  used_capacity: number
  price_per_unit: number
  status: 'active' | 'maintenance' | 'depleted'
  created_at: string
  last_updated: string
  rental_count: number
  revenue: number
}

export interface EnergyStats {
  total_pools: number
  total_capacity: number
  total_used: number
  total_available: number
  utilization_rate: number
  total_revenue: number
  active_rentals: number
  avg_price_per_unit: number
}

export interface EnergyTransaction {
  id: string
  user_id: string
  user_name: string
  pool_id: string
  pool_name: string
  amount: number
  price: number
  total_cost: number
  duration_hours: number
  status: 'active' | 'completed' | 'expired'
  created_at: string
  expires_at: string
}

export interface EnergySettings {
  default_price_per_unit: number
  max_rental_hours: number
  auto_refill_enabled: boolean
  dynamic_pricing_enabled: boolean
  auto_maintenance_enabled: boolean
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
