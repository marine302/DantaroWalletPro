import { NextRequest, NextResponse } from 'next/server';
import { Permission } from '@/types/auth';

// 페이지별 필요한 권한 매핑
export const ROUTE_PERMISSIONS: Record<string, Permission[]> = {
  // Dashboard - 기본 뷰 권한
  '/': ['analytics.view'],
  
  // User Management
  '/admins': ['users.view'],
  
  // Partner Management
  '/partners': ['partners.view'],
  '/partner-onboarding': ['partners.create', 'partners.edit'],
  
  // Energy Market
  '/energy': ['energy.view'],
  '/energy/auto-purchase': ['energy.trade'],
  '/energy/external-market': ['energy.view'],
  '/energy/external-market/purchase': ['energy.trade'],
  '/energy/purchase-history': ['energy.view'],
  '/energy-market': ['energy.view', 'energy.manage_providers'],
  
  // Financial
  '/fees': ['finance.view', 'finance.manage_fees'],
  
  // Analytics
  '/analytics': ['analytics.view'],
  '/integrated-dashboard': ['analytics.view'],
  
  // Audit & Compliance
  '/audit-compliance': ['audit.view'],
  
  // Settings
  '/settings': ['system.manage_settings'],
};

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Skip middleware for API routes and static files
  if (
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon.ico') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Allow login page without authentication
  if (pathname === '/login') {
    return NextResponse.next();
  }

  // Check if user is authenticated
  const token = request.cookies.get('auth-token')?.value;
  
  if (!token) {
    // Redirect to login if not authenticated
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // TODO: Validate token and get user permissions
  // For now, we'll handle permission checks in the page components
  // In a real implementation, you would:
  // 1. Decode/validate the JWT token
  // 2. Get user permissions from the token or database
  // 3. Check if user has required permissions for the route
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
