/**
 * 백엔드 API 상태 모니터링 컴포넌트
 * 백엔드 API 서버 상태를 실시간으로 체크하고 사용자에게 알림
 */

'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface BackendStatusProps {
  className?: string;
}

export default function BackendStatusMonitor({ className = '' }: BackendStatusProps) {
  const [backendStatus, setBackendStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [useBackendAPI, setUseBackendAPI] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  useEffect(() => {
    // 환경변수에서 백엔드 API 사용 여부 확인
    setUseBackendAPI(process.env.NEXT_PUBLIC_USE_BACKEND_API === 'true');
    
    // 백엔드 API 사용이 활성화된 경우에만 상태 체크
    if (process.env.NEXT_PUBLIC_USE_BACKEND_API === 'true') {
      checkBackendStatus();
      
      // 30초마다 백엔드 상태 체크
      const interval = setInterval(checkBackendStatus, 30000);
      return () => clearInterval(interval);
    }
  }, []);

  const checkBackendStatus = async () => {
    setBackendStatus('checking');
    try {
      const isHealthy = await apiClient.checkBackendHealth();
      setBackendStatus(isHealthy ? 'healthy' : 'unhealthy');
      setLastCheck(new Date());
    } catch (error) {
      setBackendStatus('unhealthy');
      setLastCheck(new Date());
    }
  };

  // 백엔드 API를 사용하지 않는 경우 표시하지 않음
  if (!useBackendAPI) {
    return null;
  }

  const getStatusColor = () => {
    switch (backendStatus) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'checking':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    switch (backendStatus) {
      case 'healthy':
        return '🟢';
      case 'unhealthy':
        return '🔴';
      case 'checking':
        return '🟡';
      default:
        return '⚪';
    }
  };

  const getStatusText = () => {
    switch (backendStatus) {
      case 'healthy':
        return '백엔드 API 연결됨';
      case 'unhealthy':
        return '백엔드 API 연결 실패 (Mock 사용 중)';
      case 'checking':
        return '백엔드 API 상태 확인 중...';
      default:
        return '상태 알 수 없음';
    }
  };

  return (
    <div className={`flex items-center space-x-2 px-3 py-1 rounded-lg border text-sm ${getStatusColor()} ${className}`}>
      <span className="text-lg">{getStatusIcon()}</span>
      <span className="font-medium">{getStatusText()}</span>
      {lastCheck && (
        <span className="text-xs opacity-75">
          (마지막 확인: {lastCheck.toLocaleTimeString()})
        </span>
      )}
      <button
        onClick={checkBackendStatus}
        className="ml-2 px-2 py-1 text-xs rounded bg-gray-700 bg-opacity-50 hover:bg-opacity-75 transition-colors"
        disabled={backendStatus === 'checking'}
      >
        새로고침
      </button>
    </div>
  );
}

/**
 * 백엔드 API 전환 토글 컴포넌트
 */
export function BackendAPIToggle({ className = '' }: { className?: string }) {
  const [useBackendAPI, setUseBackendAPI] = useState(false);

  useEffect(() => {
    setUseBackendAPI(process.env.NEXT_PUBLIC_USE_BACKEND_API === 'true');
  }, []);

  const toggleBackendAPI = () => {
    const newValue = !useBackendAPI;
    setUseBackendAPI(newValue);
    
    // 환경변수 업데이트 (개발 환경에서만)
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      // 브라우저에서는 환경변수를 직접 변경할 수 없으므로 localStorage 사용
      localStorage.setItem('useBackendAPI', newValue.toString());
      
      // 페이지 새로고침하여 설정 적용
      window.location.reload();
    }
  };

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <span className="text-sm font-medium text-gray-300">백엔드 API 사용:</span>
      <button
        onClick={toggleBackendAPI}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          useBackendAPI ? 'bg-blue-600' : 'bg-gray-300'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-gray-200 transition-transform ${
            useBackendAPI ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      <span className="text-xs text-gray-400">
        {useBackendAPI ? '백엔드 API (Fallback: Mock)' : 'Mock API만 사용'}
      </span>
    </div>
  );
}
