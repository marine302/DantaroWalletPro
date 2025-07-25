'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthState, LoginRequest, LoginResponse, Permission } from '@/types/auth';
import { hasPermission, canAccessRoute, getUserPermissions } from '@/lib/rbac';
import { logActivity } from '@/lib/activity-logger';

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: Permission) => boolean;
  canAccessRoute: (route: string) => boolean;
  refreshToken: () => Promise<void>;
  getUserPermissions: () => Permission[];
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true
  });

  // Mock user for development
  const mockUser: User = {
    id: '1',
    email: 'admin@dantaro.com',
    name: 'Super Admin',
    role: 'super_admin',
    isActive: true,
    createdAt: new Date().toISOString()
  };

  useEffect(() => {
    // Check for existing auth state
    const _initializeAuth = async () => {
      try {
        const _token = localStorage.getItem('authToken');
        const _userStr = localStorage.getItem('authUser');

        if (_token && _userStr) {
          const _user = JSON.parse(_userStr);
          setState({
            user: _user,
            token: _token,
            isAuthenticated: true,
            isLoading: false
          });
        } else {
          // For development, auto-login with mock user
          if (process.env.NODE_ENV === 'development') {
            const _mockToken = 'mock-jwt-token';
            localStorage.setItem('authToken', _mockToken);
            localStorage.setItem('authUser', JSON.stringify(mockUser));

            setState({
              user: mockUser,
              token: _mockToken,
              isAuthenticated: true,
              isLoading: false
            });
          } else {
            setState(prev => ({ ...prev, isLoading: false }));
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        setState(prev => ({ ...prev, isLoading: false }));
      }
    };

    _initializeAuth();
  }, []);

  const _login = async (credentials: LoginRequest): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // 실제 API 클라이언트를 사용한 슈퍼 어드민 로그인
      const { apiClient } = await import('@/lib/api');
      const _response = await apiClient.superAdminLogin(credentials);

      // Mock user 데이터 (실제로는 백엔드에서 사용자 정보를 받아와야 함)
      const _user = {
        ...mockUser,
        email: credentials.email
      };

      localStorage.setItem('authToken', _response.access_token);
      localStorage.setItem('authUser', JSON.stringify(_user));

      setState({
        user: _user,
        token: _response.access_token,
        isAuthenticated: true,
        isLoading: false
      });

      // Log login activity
      logActivity({
        user: _user,
        action: 'login',
        resource: 'dashboard',
        details: { loginMethod: 'super-admin' }
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const _logout = () => {
    // Log logout activity before clearing state
    if (state.user) {
      logActivity({
        user: state.user,
        action: 'logout',
        resource: 'dashboard'
      });
    }

    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');

    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false
    });
  };

  const _refreshToken = async (): Promise<void> => {
    try {
      const _currentToken = localStorage.getItem('authToken');
      if (!_currentToken) {
        throw new Error('No token available');
      }

      // Mock refresh for development
      if (process.env.NODE_ENV === 'development') {
        return;
      }

      // Real API refresh would go here
      const _response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${_currentToken}`
        }
      });

      if (!_response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: LoginResponse = await _response.json();

      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(data.user));

      setState(prev => ({
        ...prev,
        user: data.user,
        token: data.token
      }));
    } catch (error) {
      console.error('Token refresh error:', error);
      _logout();
    }
  };

  const contextValue: AuthContextType = {
    ...state,
    login: _login,
    logout: _logout,
    hasPermission: (permission: Permission) => hasPermission(state.user, permission),
    canAccessRoute: (route: string) => canAccessRoute(state.user, route),
    refreshToken: _refreshToken,
    getUserPermissions: () => getUserPermissions(state.user)
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// HOC for protecting routes
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-400 mb-4">Access Denied</h1>
            <p className="text-gray-400">You need to be authenticated to access this page.</p>
          </div>
        </div>
      );
    }

    return <Component {...props} />;
  };
}

// HOC for protecting routes with specific permissions
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  requiredPermission: string
) {
  return function PermissionProtectedComponent(props: P) {
    const { hasPermission: checkPermission, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!checkPermission(requiredPermission as Permission)) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-400 mb-4">Access Denied</h1>
            <p className="text-gray-400">
              You don't have permission to access this page.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Required permission: {requiredPermission}
            </p>
          </div>
        </div>
      );
    }

    return <Component {...props} />;
  };
}
