import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nProvider } from '@/contexts/I18nContext';

// Create a custom render function that includes providers
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        {children}
      </I18nProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Mock data generators
export const mockDashboardStats = {
  total_users: 1500,
  active_partners: 25,
  total_revenue: 1250000,
  available_energy: 850000,
  daily_volume: 125000,
  total_transactions_today: 450,
  active_wallets: 1200,
};

export const mockSystemHealth = {
  status: 'operational',
  uptime: 99.98,
  response_time: 245,
  error_rate: 0.02,
  cpu_usage: 45,
  memory_usage: 62,
  disk_usage: 78,
};

export const mockPartner = {
  id: '1',
  name: 'Test Partner',
  email: 'partner@test.com',
  status: 'active',
  created_at: '2023-01-01T00:00:00Z',
  total_transactions: 100,
  total_volume: 50000,
};

export const mockUser = {
  id: '1',
  email: 'admin@test.com',
  name: 'Test Admin',
  role: 'super_admin',
  created_at: '2023-01-01T00:00:00Z',
};

export const mockTransaction = {
  id: '1',
  from_address: 'TR123456789',
  to_address: 'TR987654321',
  amount: 1000,
  fee: 10,
  status: 'completed',
  timestamp: '2023-01-01T00:00:00Z',
  type: 'transfer',
};

// Test utilities
export const waitForLoadingToFinish = () => 
  new Promise(resolve => setTimeout(resolve, 0));

export const mockApiResponse = <T>(data: T) => ({
  success: true,
  data,
  message: 'Success',
});

export const mockApiError = (message: string) => ({
  success: false,
  data: null,
  message,
  error: message,
});
