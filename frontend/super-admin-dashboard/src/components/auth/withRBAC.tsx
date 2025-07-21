'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Permission } from '@/types/auth';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';

// Route permissions mapping (moved from deleted middleware.ts)
const ROUTE_PERMISSIONS: Record<string, Permission[]> = {
  '/': ['analytics.view'],
  '/admins': ['users.view'],
  '/partners': ['partners.view'],
  '/partner-onboarding': ['partners.create', 'partners.edit'],
  '/energy': ['energy.view'],
  '/energy/auto-purchase': ['energy.trade'],
  '/energy/external-market': ['energy.view'],
  '/energy/external-market/purchase': ['energy.trade'],
  '/energy/purchase-history': ['energy.view'],
  '/energy-market': ['energy.view', 'energy.manage_providers'],
  '/fees': ['finance.view', 'finance.manage_fees'],
  '/analytics': ['analytics.view'],
  '/integrated-dashboard': ['analytics.view'],
  '/audit-compliance': ['audit.view'],
  '/settings': ['system.manage_settings'],
};

interface WithRBACProps {
  requiredPermissions?: Permission[];
  fallback?: React.ComponentType;
}

export function withRBAC<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithRBACProps = {}
) {
  const { requiredPermissions, fallback: Fallback } = options;

  const ComponentWithRBAC = (props: P) => {
    const { user, isLoading, hasPermission } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
      if (!isLoading && !user) {
        router.push('/login');
        return;
      }

      // Check route-based permissions
      const routePermissions = ROUTE_PERMISSIONS[pathname];
      if (routePermissions && user) {
        const hasRouteAccess = routePermissions.some((permission: Permission) => 
          hasPermission(permission)
        );
        
        if (!hasRouteAccess) {
          // Redirect to dashboard with error message
          router.push('/?error=access_denied');
          return;
        }
      }

      // Check component-specific permissions
      if (requiredPermissions && user) {
        const hasComponentAccess = requiredPermissions.some(permission => 
          hasPermission(permission)
        );
        
        if (!hasComponentAccess && Fallback) {
          return;
        }
      }
    }, [user, isLoading, pathname, router]);

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!user) {
      return null; // Will redirect to login
    }

    // Check component-specific permissions
    if (requiredPermissions) {
      const hasAccess = requiredPermissions.some(permission => 
        hasPermission(permission)
      );
      
      if (!hasAccess) {
        if (Fallback) {
          return <Fallback />;
        }
        
        return (
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                액세스 거부됨
              </h2>
              <p className="text-gray-600">
                이 페이지에 접근할 권한이 없습니다.
              </p>
            </div>
          </div>
        );
      }
    }

    return <WrappedComponent {...props} />;
  };

  ComponentWithRBAC.displayName = `withRBAC(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return ComponentWithRBAC;
}

// Convenience wrapper for pages
export function ProtectedPage<P extends object>(
  Component: React.ComponentType<P>,
  requiredPermissions?: Permission[]
) {
  return withRBAC(Component, { requiredPermissions });
}
