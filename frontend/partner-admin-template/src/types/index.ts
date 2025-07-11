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
