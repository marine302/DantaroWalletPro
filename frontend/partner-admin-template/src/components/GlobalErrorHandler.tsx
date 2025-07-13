'use client';

import { useEffect } from 'react';

interface ErrorEvent extends Event {
  message: string;
  filename: string;
  lineno: number;
  colno: number;
  error: Error;
}

interface UnhandledRejectionEvent extends Event {
  reason: unknown;
  promise: Promise<unknown>;
}

export default function GlobalErrorHandler() {
  useEffect(() => {
    // Handle JavaScript errors
    const handleError = (event: ErrorEvent) => {
      const errorData = {
        type: 'JavaScript Error',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };
      
      console.error('🚨 Global JavaScript Error:', errorData);
      
      // Store in sessionStorage for debugging
      const errors = JSON.parse(sessionStorage.getItem('globalErrors') || '[]');
      errors.push(errorData);
      sessionStorage.setItem('globalErrors', JSON.stringify(errors.slice(-10))); // Keep last 10 errors
      
      // Send to API endpoint for logging (optional)
      fetch('/api/log-error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorData),
      }).catch(err => console.error('Failed to log error to API:', err));
    };
    
    // Handle unhandled promise rejections
    const handleUnhandledRejection = (event: UnhandledRejectionEvent) => {
      const errorData = {
        type: 'Unhandled Promise Rejection',
        reason: event.reason?.toString() || 'Unknown reason',
        stack: (event.reason instanceof Error) ? event.reason.stack : undefined,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };
      
      console.error('🚨 Unhandled Promise Rejection:', errorData);
      
      // Store in sessionStorage for debugging
      const errors = JSON.parse(sessionStorage.getItem('globalErrors') || '[]');
      errors.push(errorData);
      sessionStorage.setItem('globalErrors', JSON.stringify(errors.slice(-10))); // Keep last 10 errors
      
      // Send to API endpoint for logging (optional)
      fetch('/api/log-error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorData),
      }).catch(err => console.error('Failed to log error to API:', err));
    };
    
    // Add event listeners
    window.addEventListener('error', handleError as EventListener);
    window.addEventListener('unhandledrejection', handleUnhandledRejection as EventListener);
    
    // Cleanup function
    return () => {
      window.removeEventListener('error', handleError as EventListener);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection as EventListener);
    };
  }, []);
  
  return null; // This component doesn't render anything
}

// Helper function to get stored errors
export function getStoredErrors() {
  if (typeof window !== 'undefined') {
    return JSON.parse(sessionStorage.getItem('globalErrors') || '[]');
  }
  return [];
}

// Helper function to clear stored errors
export function clearStoredErrors() {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem('globalErrors');
  }
}
