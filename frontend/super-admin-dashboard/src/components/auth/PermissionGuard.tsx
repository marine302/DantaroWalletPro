'use client';

import { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Permission } from '@/types/auth';

interface PermissionGuardProps {
  permission: Permission;
  children: ReactNode;
  fallback?: ReactNode;
  hideIfNoAccess?: boolean;
}

/**
 * Component that conditionally renders children based on user permissions
 */
export function PermissionGuard({
  permission,
  children,
  fallback = null,
  hideIfNoAccess = false
}: PermissionGuardProps) {
  const { hasPermission } = useAuth();

  if (!hasPermission(permission)) {
    if (hideIfNoAccess) {
      return null;
    }
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface RoleGuardProps {
  roles: string[];
  children: ReactNode;
  fallback?: ReactNode;
  hideIfNoAccess?: boolean;
}

/**
 * Component that conditionally renders children based on user role
 */
export function RoleGuard({
  roles,
  children,
  fallback = null,
  hideIfNoAccess = false
}: RoleGuardProps) {
  const { user } = useAuth();

  const _hasRole = user && roles.includes(user.role);

  if (!hasRole) {
    if (hideIfNoAccess) {
      return null;
    }
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface RouteGuardProps {
  route: string;
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Component that conditionally renders children based on route access
 */
export function RouteGuard({ route, children, fallback = null }: RouteGuardProps) {
  const { canAccessRoute } = useAuth();

  if (!canAccessRoute(route)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
