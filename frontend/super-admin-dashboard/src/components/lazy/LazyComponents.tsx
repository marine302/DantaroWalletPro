import { lazy, Suspense } from 'react';
import { Loading } from '@/components/ui/Loading';

// Lazy load heavy components
export const LazyDashboardCharts = lazy(() =>
  import('@/components/charts/DashboardCharts').then(module => ({
    default: module.DashboardCharts
  }))
);

export const LazyRealtimeTransactionMonitor = lazy(() =>
  import('@/components/audit/RealtimeTransactionMonitor').then(module => ({
    default: module.RealtimeTransactionMonitor
  }))
);

export const LazyEmergencyBlockingPanel = lazy(() =>
  import('@/components/audit/EmergencyBlockingPanel').then(module => ({
    default: module.EmergencyBlockingPanel
  }))
);

export const LazyAuditLogSearch = lazy(() =>
  import('@/components/audit/AuditLogSearch').then(module => ({
    default: module.AuditLogSearch
  }))
);

export const LazyRealtimeAlerts = lazy(() =>
  import('@/components/realtime/RealtimeAlerts').then(module => ({
    default: module.RealtimeAlerts
  }))
);

// HOC for wrapping lazy components with Suspense
export function withLazyLoading<T extends object>(
  LazyComponent: React.LazyExoticComponent<React.ComponentType<T>>,
  fallback?: React.ReactNode
) {
  return function WrappedComponent(props: T) {
    return (
      <Suspense fallback={fallback || <Loading />}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

// Pre-configured lazy components with loading states
export const DashboardChartsLazy = withLazyLoading(LazyDashboardCharts);
export const RealtimeTransactionMonitorLazy = withLazyLoading(LazyRealtimeTransactionMonitor);
export const EmergencyBlockingPanelLazy = withLazyLoading(LazyEmergencyBlockingPanel);
export const AuditLogSearchLazy = withLazyLoading(LazyAuditLogSearch);
export const RealtimeAlertsLazy = withLazyLoading(LazyRealtimeAlerts);
