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
  fee_currency: 'USDT' | 'TRX'  // 수수료 통화
  energy_consumed?: number      // 소모된 에너지
  energy_cost?: number          // 에너지 비용 (TRX)
  profit_margin?: number        // 수익 마진 (수수료 - 에너지 비용)
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

// Energy Rental Types
export interface EnergyRentalPlan {
  id: string
  name: string
  description: string
  type: 'basic' | 'premium' | 'enterprise'
  energy_amount: number
  duration_hours: number
  cost_per_hour: number
  total_cost: number
  availability?: {
    is_available: boolean
    remaining_slots?: number
  }
  features?: string[]
  created_at: string
  updated_at: string
}

export interface EnergyRental {
  id: string
  partner_id: string
  plan_id: string
  energy_amount: number
  duration_hours: number
  remaining_hours: number
  start_time: string
  end_time: string
  cost_per_hour: number
  total_cost: number
  status: 'active' | 'expired' | 'cancelled' | 'pending'
  created_at: string
  updated_at: string
}

export interface EnergyUsageStats {
  partner_id: string
  total_energy_used: number
  daily_usage: number
  daily_limit: number
  monthly_usage: number
  monthly_limit: number
  cost_today: number
  cost_month: number
  efficiency_score: number
  peak_usage_time?: string
  average_daily_usage: number
  usage_trend: number
  last_updated: string
}

export interface EnergyBilling {
  id: string
  partner_id: string
  rental_id: string
  period_start: string
  period_end: string
  energy_consumed: number
  base_cost: number
  additional_fees: number
  total_amount: number
  currency: 'TRX' | 'USDT'
  status: 'pending' | 'paid' | 'overdue' | 'cancelled'
  payment_method?: string
  paid_at?: string
  due_date: string
  created_at: string
}

export interface EnergySupplyStatus {
  total_capacity: number
  available_capacity: number
  reserved_capacity: number
  utilization_rate: number
  current_price: number
  price_trend?: number
  estimated_refill_time?: string
  maintenance_window?: {
    start: string
    end: string
    description: string
  }
  last_updated: string
}

export interface EnergyUsagePrediction {
  partner_id: string
  forecast_period: string
  predicted_usage: {
    daily: number[]
    weekly_total: number
    monthly_total: number
  }
  cost_projection: {
    daily: number[]
    weekly_total: number
    monthly_total: number
  }
  recommendations: {
    optimal_plan?: string
    cost_savings?: number
    usage_optimization?: string[]
  }
  confidence_score: number
  generated_at: string
}
