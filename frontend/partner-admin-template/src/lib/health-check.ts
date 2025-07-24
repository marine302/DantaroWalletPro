/**
 * 백엔드 연결 상태 확인 유틸리티
 */

export interface HealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'error';
  message: string;
  timestamp: string;
  responseTime?: number;
  version?: string;
}

/**
 * 백엔드 서버 헬스 체크
 */
export async function checkBackendHealth(): Promise<HealthCheckResult> {
  const startTime = Date.now();
  
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // 5초 타임아웃
      signal: AbortSignal.timeout(5000),
    });

    const responseTime = Date.now() - startTime;

    if (response.ok) {
      const data = await response.json();
      return {
        status: 'healthy',
        message: 'Backend server is running',
        timestamp: new Date().toISOString(),
        responseTime,
        version: data.version || 'unknown',
      };
    } else {
      return {
        status: 'unhealthy',
        message: `Server responded with status ${response.status}`,
        timestamp: new Date().toISOString(),
        responseTime,
      };
    }
  } catch (error) {
    const responseTime = Date.now() - startTime;
    
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
      responseTime,
    };
  }
}

/**
 * API 엔드포인트별 연결 테스트
 */
export async function testApiEndpoints() {
  const endpoints = [
    { name: 'Authentication', path: '/auth/me' },
    { name: 'Partners', path: '/partners' },
    { name: 'Wallets', path: '/tronlink/wallets' },
    { name: 'Withdrawals', path: '/withdrawals' },
  ];

  const results = [];

  for (const endpoint of endpoints) {
    try {
      const startTime = Date.now();
      
      // GET 요청으로 엔드포인트 테스트 (인증 토큰 없이)
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${process.env.NEXT_PUBLIC_API_VERSION}${endpoint.path}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(3000),
        }
      );

      const responseTime = Date.now() - startTime;

      results.push({
        name: endpoint.name,
        path: endpoint.path,
        status: response.status,
        ok: response.ok || response.status === 401, // 401은 인증 오류이므로 엔드포인트 자체는 동작
        responseTime,
        message: response.ok ? 'OK' : `HTTP ${response.status}`,
      });
    } catch (error) {
      results.push({
        name: endpoint.name,
        path: endpoint.path,
        status: 0,
        ok: false,
        responseTime: 0,
        message: error instanceof Error ? error.message : 'Network error',
      });
    }
  }

  return results;
}

/**
 * 환경 변수 검증
 */
export function validateEnvironmentVariables() {
  const required = [
    'NEXT_PUBLIC_API_URL',
    'NEXT_PUBLIC_API_VERSION',
  ];

  const optional = [
    'NEXT_PUBLIC_ENV',
    'NEXT_PUBLIC_TRON_NETWORK',
    'NEXT_PUBLIC_TRON_API_KEY',
    'NEXT_PUBLIC_WS_URL',
    'NEXT_PUBLIC_LOG_LEVEL',
  ];

  const missing = required.filter(key => !process.env[key]);
  const present = required.filter(key => process.env[key]);
  const optionalPresent = optional.filter(key => process.env[key]);

  return {
    valid: missing.length === 0,
    missing,
    present,
    optionalPresent,
    values: {
      apiUrl: process.env.NEXT_PUBLIC_API_URL,
      apiVersion: process.env.NEXT_PUBLIC_API_VERSION,
      environment: process.env.NEXT_PUBLIC_ENV,
      tronNetwork: process.env.NEXT_PUBLIC_TRON_NETWORK,
      logLevel: process.env.NEXT_PUBLIC_LOG_LEVEL,
    },
  };
}
