export type Role = 'super_admin' | 'admin' | 'viewer' | 'auditor';

export type Permission = 
  // User Management
  | 'users.view'
  | 'users.create'
  | 'users.edit'
  | 'users.delete'
  | 'users.manage_roles'
  
  // Admin Management
  | 'admin.view'
  | 'admin.create'
  | 'admin.edit'
  | 'admin.delete'
  | 'admin.manage'
  
  // Partner Management
  | 'partners.view'
  | 'partners.create'
  | 'partners.edit'
  | 'partners.delete'
  | 'partners.approve'
  | 'partners.suspend'
  
  // Energy Market
  | 'energy.view'
  | 'energy.trade'
  | 'energy.manage_providers'
  | 'energy.set_prices'
  
  // Financial
  | 'finance.view'
  | 'finance.manage_fees'
  | 'finance.view_revenue'
  | 'finance.export_data'
  
  // System
  | 'system.view_logs'
  | 'system.manage_settings'
  | 'system.backup'
  | 'system.maintenance'
  
  // Audit & Compliance
  | 'audit.view'
  | 'audit.export'
  | 'audit.manage_compliance'
  | 'compliance.view'
  | 'compliance.manage'
  
  // Analytics
  | 'analytics.view'
  | 'analytics.advanced'
  | 'analytics.export';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  permissions?: Permission[];
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
  twoFactorCode?: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RolePermissions {
  [key: string]: Permission[];
}

// Default role permissions
export const ROLE_PERMISSIONS: RolePermissions = {
  super_admin: [
    // All permissions
    'users.view', 'users.create', 'users.edit', 'users.delete', 'users.manage_roles',
    'partners.view', 'partners.create', 'partners.edit', 'partners.delete', 'partners.approve', 'partners.suspend',
    'energy.view', 'energy.trade', 'energy.manage_providers', 'energy.set_prices',
    'finance.view', 'finance.manage_fees', 'finance.view_revenue', 'finance.export_data',
    'system.view_logs', 'system.manage_settings', 'system.backup', 'system.maintenance',
    'audit.view', 'audit.export', 'audit.manage_compliance',
    'analytics.view', 'analytics.advanced', 'analytics.export'
  ],
  
  admin: [
    // Most permissions except critical system operations
    'users.view', 'users.create', 'users.edit',
    'partners.view', 'partners.create', 'partners.edit', 'partners.approve', 'partners.suspend',
    'energy.view', 'energy.trade', 'energy.manage_providers',
    'finance.view', 'finance.view_revenue', 'finance.export_data',
    'system.view_logs', 'system.manage_settings',
    'audit.view', 'audit.export',
    'analytics.view', 'analytics.advanced', 'analytics.export'
  ],
  
  viewer: [
    // Read-only permissions
    'users.view',
    'partners.view',
    'energy.view',
    'finance.view',
    'system.view_logs',
    'audit.view',
    'analytics.view'
  ],
  
  auditor: [
    // Audit and compliance focused permissions
    'users.view',
    'partners.view',
    'energy.view',
    'finance.view', 'finance.view_revenue',
    'system.view_logs',
    'audit.view', 'audit.export', 'audit.manage_compliance',
    'analytics.view', 'analytics.export'
  ]
};
