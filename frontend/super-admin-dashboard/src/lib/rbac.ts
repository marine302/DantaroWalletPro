import { User, Permission, ROLE_PERMISSIONS } from '@/types/auth';

/**
 * Check if a user has a specific permission
 */
export function hasPermission(user: User | null, permission: Permission): boolean {
  if (!user || !user.isActive) {
    return false;
  }

  // If user has explicit permissions, check those first
  if (user.permissions && user.permissions.length > 0) {
    return user.permissions.includes(permission);
  }

  // Otherwise, check role-based permissions
  const rolePermissions = ROLE_PERMISSIONS[user.role];
  return rolePermissions ? rolePermissions.includes(permission) : false;
}

/**
 * Check if a user has any of the specified permissions
 */
export function hasAnyPermission(user: User | null, permissions: Permission[]): boolean {
  return permissions.some(permission => hasPermission(user, permission));
}

/**
 * Check if a user has all of the specified permissions
 */
export function hasAllPermissions(user: User | null, permissions: Permission[]): boolean {
  return permissions.every(permission => hasPermission(user, permission));
}

/**
 * Get all permissions for a user
 */
export function getUserPermissions(user: User | null): Permission[] {
  if (!user || !user.isActive) {
    return [];
  }

  // If user has explicit permissions, return those
  if (user.permissions && user.permissions.length > 0) {
    return user.permissions;
  }

  // Otherwise, return role-based permissions
  return ROLE_PERMISSIONS[user.role] || [];
}

/**
 * Check if a role can access a specific page/route
 */
export function canAccessRoute(user: User | null, route: string): boolean {
  if (!user || !user.isActive) {
    return false;
  }

  // Route to permission mapping
  const routePermissions: Record<string, Permission[]> = {
    '/admins': ['users.view'],
    '/partners': ['partners.view'],
    '/energy': ['energy.view'],
    '/energy/auto-purchase': ['energy.view', 'energy.trade'],
    '/energy/external-market': ['energy.view', 'energy.manage_providers'],
    '/energy/purchase-history': ['energy.view'],
    '/fees': ['finance.view', 'finance.manage_fees'],
    '/analytics': ['analytics.view'],
    '/audit-compliance': ['audit.view'],
    '/settings': ['system.manage_settings'],
    '/integrated-dashboard': ['analytics.view', 'partners.view']
  };

  const requiredPermissions = routePermissions[route];
  if (!requiredPermissions) {
    // If route is not defined, assume it's accessible (like dashboard)
    return true;
  }

  // Check if user has at least one of the required permissions
  return hasAnyPermission(user, requiredPermissions);
}

/**
 * Filter menu items based on user permissions
 */
export interface MenuItem {
  label: string;
  href: string;
  icon?: any;
  requiredPermissions?: Permission[];
  children?: MenuItem[];
}

export function filterMenuItems(user: User | null, menuItems: MenuItem[]): MenuItem[] {
  if (!user) return [];

  return menuItems.filter(item => {
    // If no permissions required, show the item
    if (!item.requiredPermissions) {
      return true;
    }

    // Check if user has any of the required permissions
    const hasAccess = hasAnyPermission(user, item.requiredPermissions);
    
    // If item has children, filter them recursively
    if (item.children) {
      item.children = filterMenuItems(user, item.children);
      // Show parent if it has accessible children or user has direct access
      return hasAccess || item.children.length > 0;
    }

    return hasAccess;
  });
}

/**
 * Check if a user can perform a specific action on a resource
 */
export function canPerformAction(
  user: User | null, 
  action: 'create' | 'read' | 'update' | 'delete',
  resource: 'users' | 'partners' | 'energy' | 'finance' | 'system' | 'audit' | 'analytics'
): boolean {
  if (!user || !user.isActive) {
    return false;
  }

  const permissionMap: Record<string, Record<string, Permission>> = {
    users: {
      create: 'users.create',
      read: 'users.view',
      update: 'users.edit',
      delete: 'users.delete'
    },
    partners: {
      create: 'partners.create',
      read: 'partners.view',
      update: 'partners.edit',
      delete: 'partners.delete'
    },
    energy: {
      create: 'energy.trade',
      read: 'energy.view',
      update: 'energy.manage_providers',
      delete: 'energy.manage_providers'
    },
    finance: {
      create: 'finance.manage_fees',
      read: 'finance.view',
      update: 'finance.manage_fees',
      delete: 'finance.manage_fees'
    },
    system: {
      create: 'system.manage_settings',
      read: 'system.view_logs',
      update: 'system.manage_settings',
      delete: 'system.maintenance'
    },
    audit: {
      create: 'audit.manage_compliance',
      read: 'audit.view',
      update: 'audit.manage_compliance',
      delete: 'audit.manage_compliance'
    },
    analytics: {
      create: 'analytics.advanced',
      read: 'analytics.view',
      update: 'analytics.advanced',
      delete: 'analytics.advanced'
    }
  };

  const permission = permissionMap[resource]?.[action];
  return permission ? hasPermission(user, permission) : false;
}

/**
 * Get user-friendly role name
 */
export function getRoleName(role: string): string {
  const roleNames: Record<string, string> = {
    super_admin: 'Super Administrator',
    admin: 'Administrator',
    viewer: 'Viewer',
    auditor: 'Auditor'
  };
  
  return roleNames[role] || role;
}

/**
 * Get role color for UI
 */
export function getRoleColor(role: string): string {
  const roleColors: Record<string, string> = {
    super_admin: 'text-red-400 bg-red-900/30',
    admin: 'text-blue-400 bg-blue-900/30',
    viewer: 'text-green-400 bg-green-900/30',
    auditor: 'text-purple-400 bg-purple-900/30'
  };
  
  return roleColors[role] || 'text-gray-400 bg-gray-900/30';
}
