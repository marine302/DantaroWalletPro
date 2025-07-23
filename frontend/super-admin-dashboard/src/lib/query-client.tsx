'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Performance-optimized caching strategy
            staleTime: 5 * 60 * 1000, // 5 minutes - data considered fresh
            cacheTime: 10 * 60 * 1000, // 10 minutes - keep in cache when unused

            // Network optimizations
            refetchOnWindowFocus: false,
            refetchOnMount: true,
            refetchOnReconnect: 'always',

            // Error handling and retry logic
            retry: (failureCount, error) => {
              // Don't retry on auth errors (401/403)
              if (error && typeof error === 'object' && 'response' in error) {
                const _status = (error as { response: { status: number } }).response?.status;
                if (status === 401 || status === 403) {
                  return false;
                }
              }
              // Don't retry client errors (4xx)
              if (error && typeof error === 'object' && 'response' in error) {
                const _status = (error as { response: { status: number } }).response?.status;
                if (status >= 400 && status < 500) {
                  return false;
                }
              }
              return failureCount < 2; // Reduced retry count for better performance
            },
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

            // Background refetch optimization
            refetchInterval: false, // Disable automatic background refetch
          },
          mutations: {
            retry: false,
            // Add default mutation options for consistency
            onError: (error) => {
              console.error('Mutation error:', error);
            },
          },
        },
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
