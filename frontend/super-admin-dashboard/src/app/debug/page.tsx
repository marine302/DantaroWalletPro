'use client';

import { useEffect, useState } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import BackendStatusMonitor, { BackendAPIToggle } from '@/components/ui/BackendStatusMonitor';
import { apiClient } from '@/lib/api';

export default function DebugPage() {
  const [errors, setErrors] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [apiTestResults, setApiTestResults] = useState<Record<string, unknown>[]>([]);

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

  // 백엔드 API 테스트 함수들
  const testBackendAPIs = async () => {
    const testResults = [];
    
    try {
      console.log('🧪 Testing Backend APIs...');
      
      // 1. 백엔드 헬스 체크
      try {
        const healthResult = await apiClient.checkBackendHealth();
        testResults.push({
          api: 'Backend Health Check',
          status: healthResult ? 'Success' : 'Failed',
          data: healthResult
        });
      } catch (error) {
        testResults.push({
          api: 'Backend Health Check',
          status: 'Error',
          error: (error as Error).message || String(error)
        });
      }

      // 2. 대시보드 통계 API 테스트
      try {
        const dashboardStats = await apiClient.getDashboardStats();
        testResults.push({
          api: 'Dashboard Stats',
          status: 'Success',
          data: dashboardStats
        });
      } catch (error) {
        testResults.push({
          api: 'Dashboard Stats',
          status: 'Error',
          error: (error as Error).message || String(error)
        });
      }

      // 3. 시스템 헬스 API 테스트
      try {
        const systemHealth = await apiClient.getSystemHealth();
        testResults.push({
          api: 'System Health',
          status: 'Success',
          data: systemHealth
        });
      } catch (error) {
        testResults.push({
          api: 'System Health',
          status: 'Error',
          error: (error as Error).message || String(error)
        });
      }

      // 4. 파트너 목록 API 테스트
      try {
        const partners = await apiClient.getPartners(1, 5);
        testResults.push({
          api: 'Partners List',
          status: 'Success',
          data: partners
        });
      } catch (error) {
        testResults.push({
          api: 'Partners List',
          status: 'Error',
          error: (error as Error).message || String(error)
        });
      }

      setApiTestResults(testResults);
      console.log('✅ API Test Results:', testResults);
      
    } catch (error) {
      console.error('❌ API Test Failed:', error);
      setApiTestResults([{
        api: 'All Tests',
        status: 'Critical Error',
        error: (error as Error).message || String(error)
      }]);
    }
  };

  const clearApiTestResults = () => {
    setApiTestResults([]);
  };

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

        <Section title="API Test Results">
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {apiTestResults.length === 0 ? (
              <p className="text-gray-400">No API tests performed yet</p>
            ) : (
              apiTestResults.map((result, index) => (
                <div key={index} className={`text-sm font-mono p-2 rounded ${result.status === 'Success' ? 'bg-green-900/20' : 'bg-red-900/20'}`}>
                  <div className="font-semibold">{result.api}</div>
                  <div className="text-xs">
                    Status: {result.status}
                    {result.data && <pre className="whitespace-pre-wrap">{JSON.stringify(result.data, null, 2)}</pre>}
                    {result.error && <div className="text-red-300">Error: {result.error}</div>}
                  </div>
                </div>
              ))
            )}
          </div>
        </Section>

        {/* 백엔드 API 관리 섹션 */}
        <Section title="🔧 Backend API Management">
          <div className="space-y-4">
            {/* 백엔드 상태 모니터 */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">API Status</h4>
              <BackendStatusMonitor />
            </div>
            
            {/* 백엔드 API 토글 */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">API Configuration</h4>
              <BackendAPIToggle />
            </div>

            {/* API 환경변수 정보 */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">Environment Variables</h4>
              <div className="bg-gray-800 p-3 rounded text-sm font-mono space-y-1">
                <div><span className="text-blue-300">NEXT_PUBLIC_USE_BACKEND_API:</span> {process.env.NEXT_PUBLIC_USE_BACKEND_API || 'false'}</div>
                <div><span className="text-blue-300">NEXT_PUBLIC_BACKEND_API_URL:</span> {process.env.NEXT_PUBLIC_BACKEND_API_URL || 'Not set'}</div>
                <div><span className="text-blue-300">NEXT_PUBLIC_API_URL:</span> {process.env.NEXT_PUBLIC_API_URL || 'Not set'}</div>
                <div><span className="text-blue-300">NEXT_PUBLIC_MOCK_API_URL:</span> {process.env.NEXT_PUBLIC_MOCK_API_URL || 'Not set'}</div>
              </div>
            </div>
          </div>
        </Section>

        {/* API 테스트 결과 섹션 */}
        {apiTestResults.length > 0 && (
          <Section title={`🧪 API Test Results (${apiTestResults.length})`}>
            <div className="space-y-3">
              {apiTestResults.map((result, index) => (
                <div 
                  key={index} 
                  className={`p-3 rounded border ${
                    result.status === 'Success' 
                      ? 'bg-green-900/20 border-green-500' 
                      : 'bg-red-900/20 border-red-500'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-200">{result.api}</h4>
                    <span 
                      className={`px-2 py-1 text-xs rounded ${
                        result.status === 'Success' 
                          ? 'bg-green-600 text-white' 
                          : 'bg-red-600 text-white'
                      }`}
                    >
                      {result.status}
                    </span>
                  </div>
                  {result.error && (
                    <div className="text-red-300 text-sm font-mono mb-2">
                      Error: {result.error}
                    </div>
                  )}
                  {result.data && (
                    <div className="text-gray-300 text-sm">
                      <details>
                        <summary className="cursor-pointer text-blue-300 hover:text-blue-200">
                          View Response Data
                        </summary>
                        <pre className="mt-2 bg-gray-800 p-2 rounded text-xs overflow-auto">
                          {JSON.stringify(result.data, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        <Section title="Actions">
          <div className="flex gap-4">
            <Button
              onClick={() => {
                setErrors([]);
                setLogs([]);
                clearApiTestResults();
              }}
              variant="primary"
            >
              Clear Logs & Results
            </Button>
            
            <Button
              onClick={() => {
                window.location.reload();
              }}
              variant="outline"
            >
              Reload Page
            </Button>

            <Button
              onClick={testBackendAPIs}
              variant="secondary"
            >
              Test Backend APIs
            </Button>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
