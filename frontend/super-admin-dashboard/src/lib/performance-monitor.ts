/**
 * Performance and User Behavior Monitoring System
 * Tracks key metrics and user interactions for optimization
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  url: string;
  userAgent: string;
}

interface UserAction {
  action: string;
  target: string;
  timestamp: number;
  url: string;
  userId?: string;
  metadata?: Record<string, any>;
}

interface ErrorLog {
  message: string;
  stack?: string;
  url: string;
  timestamp: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId?: string;
  context?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private userActions: UserAction[] = [];
  private errors: ErrorLog[] = [];
  private maxStoredItems = 100;

  constructor() {
    this.initializeMonitoring();
  }

  private initializeMonitoring() {
    if (typeof window === 'undefined') return;

    // Monitor page load performance
    window.addEventListener('load', () => {
      this.collectPageLoadMetrics();
    });

    // Monitor navigation performance
    this.observeNavigationTiming();

    // Monitor largest contentful paint
    this.observeLCP();

    // Monitor cumulative layout shift
    this.observeCLS();

    // Monitor first input delay
    this.observeFID();

    // Monitor unhandled errors
    this.observeErrors();

    // Send metrics periodically
    setInterval(() => {
      this.sendMetrics();
    }, 30000); // Send every 30 seconds
  }

  private collectPageLoadMetrics() {
    if (typeof window === 'undefined' || !window.performance) return;

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (!navigation) return;

    // Page load time
    this.addMetric('page_load_time', navigation.loadEventEnd - navigation.fetchStart);

    // DNS lookup time
    this.addMetric('dns_lookup_time', navigation.domainLookupEnd - navigation.domainLookupStart);

    // TCP connection time
    this.addMetric('tcp_connection_time', navigation.connectEnd - navigation.connectStart);

    // Time to first byte
    this.addMetric('time_to_first_byte', navigation.responseStart - navigation.fetchStart);

    // DOM content loaded
    this.addMetric('dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.fetchStart);

    // DOM interactive
    this.addMetric('dom_interactive', navigation.domInteractive - navigation.fetchStart);
  }

  private observeNavigationTiming() {
    if (typeof window === 'undefined' || !window.PerformanceObserver) return;

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming;
            this.addMetric('navigation_time', navEntry.duration);
          }
        }
      });

      observer.observe({ entryTypes: ['navigation'] });
    } catch (error) {
      console.warn('Navigation timing observer not supported:', error);
    }
  }

  private observeLCP() {
    if (typeof window === 'undefined' || !window.PerformanceObserver) return;

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.addMetric('largest_contentful_paint', lastEntry.startTime);
      });

      observer.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (error) {
      console.warn('LCP observer not supported:', error);
    }
  }

  private observeCLS() {
    if (typeof window === 'undefined' || !window.PerformanceObserver) return;

    try {
      let clsValue = 0;
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        this.addMetric('cumulative_layout_shift', clsValue);
      });

      observer.observe({ entryTypes: ['layout-shift'] });
    } catch (error) {
      console.warn('CLS observer not supported:', error);
    }
  }

  private observeFID() {
    if (typeof window === 'undefined' || !window.PerformanceObserver) return;

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.addMetric('first_input_delay', (entry as any).processingStart - entry.startTime);
        }
      });

      observer.observe({ entryTypes: ['first-input'] });
    } catch (error) {
      console.warn('FID observer not supported:', error);
    }
  }

  private observeErrors() {
    if (typeof window === 'undefined') return;

    // Unhandled JavaScript errors
    window.addEventListener('error', (event) => {
      this.logError({
        message: event.message,
        stack: event.error?.stack,
        url: window.location.href,
        timestamp: Date.now(),
        severity: 'high',
        context: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        message: `Unhandled promise rejection: ${event.reason}`,
        stack: event.reason?.stack,
        url: window.location.href,
        timestamp: Date.now(),
        severity: 'high',
        context: {
          reason: event.reason,
        },
      });
    });
  }

  private addMetric(name: string, value: number) {
    if (typeof window === 'undefined') return;

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    this.metrics.push(metric);

    // Keep only recent metrics
    if (this.metrics.length > this.maxStoredItems) {
      this.metrics = this.metrics.slice(-this.maxStoredItems);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`📊 Performance Metric: ${name} = ${value}ms`);
    }
  }

  public trackUserAction(action: string, target: string, metadata?: Record<string, any>) {
    if (typeof window === 'undefined') return;

    const userAction: UserAction = {
      action,
      target,
      timestamp: Date.now(),
      url: window.location.href,
      metadata,
    };

    // Add user ID if available
    const userId = localStorage.getItem('userId');
    if (userId) {
      userAction.userId = userId;
    }

    this.userActions.push(userAction);

    // Keep only recent actions
    if (this.userActions.length > this.maxStoredItems) {
      this.userActions = this.userActions.slice(-this.maxStoredItems);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`👤 User Action: ${action} on ${target}`);
    }
  }

  public logError(error: ErrorLog) {
    this.errors.push(error);

    // Keep only recent errors
    if (this.errors.length > this.maxStoredItems) {
      this.errors = this.errors.slice(-this.maxStoredItems);
    }

    // Log to console
    console.error(`🚨 Error [${error.severity}]: ${error.message}`, error);
  }

  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  public getUserActions(): UserAction[] {
    return [...this.userActions];
  }

  public getErrors(): ErrorLog[] {
    return [...this.errors];
  }

  private async sendMetrics() {
    if (this.metrics.length === 0 && this.userActions.length === 0 && this.errors.length === 0) {
      return;
    }

    const payload = {
      metrics: this.getMetrics(),
      userActions: this.getUserActions(),
      errors: this.getErrors(),
      session: {
        timestamp: Date.now(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
        connection: (navigator as any).connection ? {
          effectiveType: (navigator as any).connection.effectiveType,
          downlink: (navigator as any).connection.downlink,
        } : null,
      },
    };

    try {
      // In development, just log to console
      if (process.env.NODE_ENV === 'development') {
        console.log('📈 Performance Data:', payload);
        return;
      }

      // In production, send to analytics endpoint
      await fetch('/api/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // Clear sent data
      this.metrics = [];
      this.userActions = [];
      this.errors = [];
    } catch (error) {
      console.warn('Failed to send metrics:', error);
    }
  }

  public exportData(): string {
    const data = {
      metrics: this.getMetrics(),
      userActions: this.getUserActions(),
      errors: this.getErrors(),
      exportedAt: new Date().toISOString(),
    };

    return JSON.stringify(data, null, 2);
  }

  public clearData() {
    this.metrics = [];
    this.userActions = [];
    this.errors = [];
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const trackClick = (target: string, metadata?: Record<string, any>) => {
    performanceMonitor.trackUserAction('click', target, metadata);
  };

  const trackPageView = (page: string) => {
    performanceMonitor.trackUserAction('page_view', page);
  };

  const trackAPICall = (endpoint: string, duration: number, success: boolean) => {
    performanceMonitor.trackUserAction('api_call', endpoint, {
      duration,
      success,
    });
  };

  const trackError = (message: string, severity: ErrorLog['severity'], context?: Record<string, any>) => {
    performanceMonitor.logError({
      message,
      url: window.location.href,
      timestamp: Date.now(),
      severity,
      context,
    });
  };

  return {
    trackClick,
    trackPageView,
    trackAPICall,
    trackError,
    getMetrics: () => performanceMonitor.getMetrics(),
    getUserActions: () => performanceMonitor.getUserActions(),
    getErrors: () => performanceMonitor.getErrors(),
    exportData: () => performanceMonitor.exportData(),
    clearData: () => performanceMonitor.clearData(),
  };
}
