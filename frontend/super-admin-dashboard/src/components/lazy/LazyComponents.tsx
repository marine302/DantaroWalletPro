import { lazy, Suspense } from 'react';
import { Loading } from '@/components/ui/Loading';

// Lazy load heavy components
export const _LazyDashboardCharts = lazy(() =>
  import('@/components/charts/DashboardCharts').then(module => ({
    default: module.DashboardCharts
  }))
);

export const _LazyRealtimeTransactionMonitor = lazy(() =>
  import('@/components/audit/RealtimeTransactionMonitor').then(module => ({
    default: module.RealtimeTransactionMonitor
  }))
);

export const _LazyEmergencyBlockingPanel = lazy(() =>
  import('@/components/audit/EmergencyBlockingPanel').then(module => ({
    default: module.EmergencyBlockingPanel
  }))
);

export const _LazyAuditLogSearch = lazy(() =>
  import('@/components/audit/AuditLogSearch').then(module => ({
    default: module.AuditLogSearch
  }))
);

export const _LazyRealtimeAlerts = lazy(() =>
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
export const _DashboardChartsLazy = withLazyLoading(LazyDashboardCharts);
export const _RealtimeTransactionMonitorLazy = withLazyLoading(LazyRealtimeTransactionMonitor);
export const _EmergencyBlockingPanelLazy = withLazyLoading(LazyEmergencyBlockingPanel);
export const _AuditLogSearchLazy = withLazyLoading(LazyAuditLogSearch);
export const _RealtimeAlertsLazy = withLazyLoading(LazyRealtimeAlerts);
