/**
 * 사용자 관련 통합 타입 정의
 */

// 기본 사용자 타입
export interface User {
  id: string
  username: string
  email: string
  phone?: string
  walletAddress: string
  balance: number
  status: 'active' | 'inactive' | 'suspended' | 'pending'
  kycStatus: 'none' | 'pending' | 'approved' | 'rejected'
  tier: 'basic' | 'premium' | 'vip'
  createdAt: string
  lastLogin?: string
  totalTransactions: number
  totalVolume: number
  referralCode?: string
  referredBy?: string
  
  // 백엔드 호환성을 위한 선택적 필드들
  wallet_address?: string
  created_at?: string
  last_login?: string
  kyc_status?: 'none' | 'pending' | 'approved' | 'rejected'
  referral_code?: string
  referred_by?: string
}

// 사용자 생성 요청
export interface CreateUserRequest {
  username: string
  email: string
  phone?: string
  tier?: 'basic' | 'premium' | 'vip'
  send_welcome_email?: boolean
}

// 사용자 업데이트 요청
export interface UpdateUserRequest {
  username?: string
  email?: string
  phone?: string
  status?: 'active' | 'inactive' | 'suspended' | 'pending'
  tier?: 'basic' | 'premium' | 'vip'
  kyc_status?: 'none' | 'pending' | 'approved' | 'rejected'
}

// 사용자 필터
export interface UserFilters {
  search?: string
  status?: 'active' | 'inactive' | 'suspended' | 'pending'
  kycStatus?: 'none' | 'pending' | 'approved' | 'rejected'
  tier?: 'basic' | 'premium' | 'vip'
  dateFrom?: string
  dateTo?: string
}

// 사용자 목록 응답
export interface UserListResponse {
  users: User[]
  total: number
  page: number
  limit: number
  totalPages: number
}

// 사용자 통계
export interface UserStats {
  total_users: number
  active_users: number
  new_users_today: number
  total_balance: number
  average_balance: number
  kyc_approved: number
  kyc_pending: number
}
