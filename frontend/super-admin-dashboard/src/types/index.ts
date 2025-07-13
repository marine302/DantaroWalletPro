// Common types
export type ExtraData = Record<string, string | number | boolean | null>;

// Partner related types
export interface Partner {
  id: number;
  name: string;
  slug: string;
  domain: string;
  api_key: string;
  webhook_url?: string;
  contact_email?: string;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at: string;
  extra_data?: ExtraData;
}

export interface PartnerConfig {
  id: number;
  partner_id: number;
  fee_percentage: number;
  min_withdrawal_amount: number;
  max_withdrawal_amount: number;
  daily_withdrawal_limit: number;
  energy_allocation: number;
  extra_data?: ExtraData;
  created_at: string;
  updated_at: string;
}

export interface PartnerDailyStatistics {
  id: number;
  partner_id: number;
  date: string;
  total_transactions: number;
  total_volume: number;
  total_fees: number;
  new_wallets: number;
  active_wallets: number;
  extra_data?: ExtraData;
}

// Energy Pool types
export interface EnergyPool {
  id: number;
  total_energy: number;
  available_energy: number;
  reserved_energy: number;
  tron_balance: number;
  last_updated: string;
  auto_recharge_enabled: boolean;
  min_energy_threshold: number;
  recharge_amount: number;
  extra_data?: ExtraData;
}

export interface EnergyTransaction {
  id: number;
  transaction_type: 'recharge' | 'allocation' | 'consumption' | 'return';
  amount: number;
  partner_id?: number;
  transaction_hash?: string;
  status: 'pending' | 'confirmed' | 'failed';
  created_at: string;
  extra_data?: ExtraData;
}

// Fee Configuration types
export interface FeeConfig {
  id: number;
  operation_type: string;
  fee_type: 'percentage' | 'fixed';
  fee_value: number;
  min_fee?: number;
  max_fee?: number;
  is_active: boolean;
  valid_from: string;
  valid_until?: string;
  extra_data?: ExtraData;
}

export interface FeeRevenue {
  id: number;
  partner_id?: number;
  operation_type: string;
  fee_amount: number;
  original_amount: number;
  currency: string;
  transaction_hash?: string;
  created_at: string;
  extra_data?: ExtraData;
}

// System Admin types
export interface SystemAdmin {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'super_admin' | 'admin' | 'operator';
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

// Dashboard statistics types
export interface DashboardStats {
  total_partners: number;
  active_partners: number;
  total_revenue: number;
  daily_volume: number;
  total_energy_consumed: number;
  available_energy: number;
  total_transactions_today: number;
  active_wallets: number;
}

// System monitoring types
export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  database_status: 'connected' | 'disconnected';
  tron_network_status: 'connected' | 'disconnected';
  last_check: string;
  uptime: number;
  errors_count: number;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Form types
export interface CreatePartnerRequest {
  name: string;
  slug: string;
  domain: string;
  webhook_url?: string;
  fee_percentage: number;
  min_withdrawal_amount: number;
  max_withdrawal_amount: number;
  daily_withdrawal_limit: number;
  energy_allocation: number;
}

export interface UpdatePartnerRequest extends Partial<CreatePartnerRequest> {
  status?: 'active' | 'inactive' | 'suspended';
}

export interface CreateFeeConfigRequest {
  operation_type: string;
  fee_type: 'percentage' | 'fixed';
  fee_value: number;
  min_fee?: number;
  max_fee?: number;
  valid_from: string;
  valid_until?: string;
}
