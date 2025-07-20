'use client';

import { useEffect, useState } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section } from '@/components/ui/DarkThemeComponents';

export default function DebugPage() {
  const [errors, setErrors] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    // 기존 console.error 래핑
    const originalError = console.error;
    const originalLog = console.log;
    const originalWarn = console.warn;

    console.error = (...args) => {
      setErrors(prev => [...prev, args.map(arg => String(arg)).join(' ')]);
      originalError(...args);
    };

    console.log = (...args) => {
      setLogs(prev => [...prev, `LOG: ${args.map(arg => String(arg)).join(' ')}`]);
      originalLog(...args);
    };

    console.warn = (...args) => {
      setLogs(prev => [...prev, `WARN: ${args.map(arg => String(arg)).join(' ')}`]);
      originalWarn(...args);
    };

    // 글로벌 에러 핸들러
    const handleError = (event: ErrorEvent) => {
      setErrors(prev => [...prev, `Global Error: ${event.message} at ${event.filename}:${event.lineno}`]);
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      setErrors(prev => [...prev, `Unhandled Promise Rejection: ${event.reason}`]);
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    // 환경 변수 로그
    console.log('Environment Variables:');
    console.log('NEXT_PUBLIC_WS_URL:', process.env.NEXT_PUBLIC_WS_URL);
    console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
    console.log('NEXT_PUBLIC_USE_MOCK_DATA:', process.env.NEXT_PUBLIC_USE_MOCK_DATA);

    // WebSocket 테스트
    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3002';
      console.log('Testing WebSocket connection to:', wsUrl);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        ws.close();
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket connection failed:', error);
      };
      
      ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
      };
    } catch (error) {
      console.error('❌ WebSocket test failed:', error);
    }

    return () => {
      console.error = originalError;
      console.log = originalLog;
      console.warn = originalWarn;
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return (
    <BasePage
      title="Debug Information"
      description="실시간 에러 모니터링 및 환경 정보 확인"
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Section title={`Errors (${errors.length})`}>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {errors.length === 0 ? (
                <p className="text-green-400">No errors detected</p>
              ) : (
                errors.map((error, index) => (
                  <div key={index} className="text-red-300 text-sm font-mono bg-red-900/20 p-2 rounded">
                    {error}
                  </div>
                ))
              )}
            </div>
          </Section>

          <Section title={`Console Logs (${logs.length})`}>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {logs.length === 0 ? (
                <p className="text-gray-400">No logs yet</p>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="text-blue-300 text-sm font-mono bg-blue-900/20 p-2 rounded">
                    {log}
                  </div>
                ))
              )}
            </div>
          </Section>
        </div>

        <Section title="Environment Check">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-semibold">WebSocket URL</h3>
              <p className="text-sm text-gray-300">{process.env.NEXT_PUBLIC_WS_URL || 'Not set'}</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-semibold">API URL</h3>
              <p className="text-sm text-gray-300">{process.env.NEXT_PUBLIC_API_URL || 'Not set'}</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-semibold">Mock Data</h3>
              <p className="text-sm text-gray-300">{process.env.NEXT_PUBLIC_USE_MOCK_DATA || 'Not set'}</p>
            </div>
          </div>
        </Section>

        <Section title="Actions">
          <div className="flex gap-4">
            <Button
              onClick={() => {
                setErrors([]);
                setLogs([]);
              }}
              variant="primary"
            >
              Clear Logs
            </Button>
            
            <Button
              onClick={() => {
                window.location.reload();
              }}
              variant="outline"
            >
              Reload Page
            </Button>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
