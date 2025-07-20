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
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('authToken');
        const userStr = localStorage.getItem('authUser');
        
        if (token && userStr) {
          const user = JSON.parse(userStr);
          setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false
          });
        } else {
          // For development, auto-login with mock user
          if (process.env.NODE_ENV === 'development') {
            const mockToken = 'mock-jwt-token';
            localStorage.setItem('authToken', mockToken);
            localStorage.setItem('authUser', JSON.stringify(mockUser));
            
            setState({
              user: mockUser,
              token: mockToken,
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

    initializeAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true }));
    
    try {
      // Mock login for development
      if (process.env.NODE_ENV === 'development') {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const token = 'mock-jwt-token';
        const user = mockUser;
        
        localStorage.setItem('authToken', token);
        localStorage.setItem('authUser', JSON.stringify(user));
        
        setState({
          user,
          token,
          isAuthenticated: true,
          isLoading: false
        });
        
        // Log login activity
        logActivity({
          user,
          action: 'login',
          resource: 'dashboard',
          details: { loginMethod: 'email' }
        });
        
        return;
      }

      // Real API login would go here
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data: LoginResponse = await response.json();
      
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(data.user));
      
      setState({
        user: data.user,
        token: data.token,
        isAuthenticated: true,
        isLoading: false
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const logout = () => {
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
      isLoading: false
    });
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const currentToken = localStorage.getItem('authToken');
      if (!currentToken) {
        throw new Error('No token available');
      }

      // Mock refresh for development
      if (process.env.NODE_ENV === 'development') {
        return;
      }

      // Real API refresh would go here
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`
        }
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: LoginResponse = await response.json();
      
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(data.user));
      
      setState(prev => ({
        ...prev,
        user: data.user,
        token: data.token
      }));
    } catch (error) {
      console.error('Token refresh error:', error);
      logout();
    }
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    logout,
    hasPermission: (permission: Permission) => hasPermission(state.user, permission),
    canAccessRoute: (route: string) => canAccessRoute(state.user, route),
    refreshToken,
    getUserPermissions: () => getUserPermissions(state.user)
  };
    refreshToken
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

    if (!checkPermission(requiredPermission)) {
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
