'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { checkBackendHealth, testApiEndpoints, validateEnvironmentVariables, type HealthCheckResult } from '@/lib/health-check';

export default function HealthCheckPage() {
  const [healthStatus, setHealthStatus] = useState<HealthCheckResult | null>(null);
  const [apiTests, setApiTests] = useState<Array<{
    name: string;
    path: string;
    status: number;
    ok: boolean;
    responseTime: number;
    message: string;
  }>>([]);
  const [envValidation, setEnvValidation] = useState<{
    valid: boolean;
    missing: string[];
    present: string[];
    optionalPresent: string[];
    values: Record<string, string | undefined>;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 페이지 로드시 환경 변수 검증
    setEnvValidation(validateEnvironmentVariables());
  }, []);

  const runHealthCheck = async () => {
    setIsLoading(true);
    try {
      const health = await checkBackendHealth();
      setHealthStatus(health);
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runApiTests = async () => {
    setIsLoading(true);
    try {
      const tests = await testApiEndpoints();
      setApiTests(tests);
    } catch (error) {
      console.error('API tests failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runAllTests = async () => {
    setIsLoading(true);
    try {
      const [health, tests] = await Promise.all([
        checkBackendHealth(),
        testApiEndpoints(),
      ]);
      setHealthStatus(health);
      setApiTests(tests);
    } catch (error) {
      console.error('Tests failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string, ok?: boolean) => {
    if (status === 'healthy' || ok) {
      return <Badge className="bg-green-100 text-green-800">정상</Badge>;
    } else if (status === 'unhealthy') {
      return <Badge className="bg-yellow-100 text-yellow-800">불안정</Badge>;
    } else {
      return <Badge className="bg-red-100 text-red-800">오류</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">백엔드 연결 상태 확인</h1>
          <p className="text-gray-600 mt-2">백엔드 서버와의 연결 상태를 확인합니다.</p>
        </div>
        <div className="space-x-2">
          <Button onClick={runHealthCheck} disabled={isLoading}>
            헬스 체크
          </Button>
          <Button onClick={runApiTests} disabled={isLoading}>
            API 테스트
          </Button>
          <Button onClick={runAllTests} disabled={isLoading} variant="default">
            전체 테스트
          </Button>
        </div>
      </div>

      {/* 환경 변수 검증 */}
      {envValidation && (
        <Card>
          <CardHeader>
            <CardTitle>환경 변수 검증</CardTitle>
            <CardDescription>필수 환경 변수가 올바르게 설정되었는지 확인합니다.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">필수 변수</h4>
                {envValidation.present.map((key: string) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Badge className="bg-green-100 text-green-800">✓</Badge>
                    <span className="text-sm">{key}</span>
                  </div>
                ))}
                {envValidation.missing.map((key: string) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Badge className="bg-red-100 text-red-800">✗</Badge>
                    <span className="text-sm">{key}</span>
                  </div>
                ))}
              </div>
              <div>
                <h4 className="font-semibold mb-2">현재 설정값</h4>
                <div className="text-sm space-y-1">
                  <div>API URL: <code className="bg-gray-100 px-2 py-1 rounded">{envValidation.values.apiUrl || '미설정'}</code></div>
                  <div>API Version: <code className="bg-gray-100 px-2 py-1 rounded">{envValidation.values.apiVersion || '미설정'}</code></div>
                  <div>Environment: <code className="bg-gray-100 px-2 py-1 rounded">{envValidation.values.environment || '미설정'}</code></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 헬스 체크 결과 */}
      {healthStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <span>백엔드 서버 상태</span>
              {getStatusBadge(healthStatus.status)}
            </CardTitle>
            <CardDescription>백엔드 서버의 전반적인 상태를 확인합니다.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h4 className="font-semibold">상태</h4>
                <p className="text-sm text-gray-600">{healthStatus.message}</p>
              </div>
              <div>
                <h4 className="font-semibold">응답 시간</h4>
                <p className="text-sm text-gray-600">{healthStatus.responseTime}ms</p>
              </div>
              <div>
                <h4 className="font-semibold">확인 시간</h4>
                <p className="text-sm text-gray-600">
                  {new Date(healthStatus.timestamp).toLocaleString('ko-KR')}
                </p>
              </div>
            </div>
            {healthStatus.version && (
              <div className="mt-4">
                <h4 className="font-semibold">서버 버전</h4>
                <p className="text-sm text-gray-600">{healthStatus.version}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* API 엔드포인트 테스트 결과 */}
      {apiTests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>API 엔드포인트 테스트</CardTitle>
            <CardDescription>각 API 엔드포인트의 연결 상태를 확인합니다.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {apiTests.map((test, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusBadge('', test.ok)}
                    <div>
                      <h4 className="font-medium">{test.name}</h4>
                      <p className="text-sm text-gray-600">{test.path}</p>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <div>상태: {test.message}</div>
                    <div className="text-gray-500">{test.responseTime}ms</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 도움말 */}
      <Card>
        <CardHeader>
          <CardTitle>문제 해결 가이드</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-semibold text-red-600">❌ 백엔드 서버에 연결할 수 없는 경우:</h4>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>백엔드 서버가 실행 중인지 확인하세요</li>
                <li>NEXT_PUBLIC_API_URL 환경 변수가 올바른지 확인하세요</li>
                <li>방화벽이나 네트워크 설정을 확인하세요</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-yellow-600">⚠️ API 엔드포인트 오류 (401):</h4>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>인증 토큰이 필요한 엔드포인트입니다 (정상적인 응답)</li>
                <li>로그인 후 다시 테스트해보세요</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-green-600">✅ 모든 테스트가 성공한 경우:</h4>
              <p className="ml-4">백엔드와의 연결이 정상적으로 작동하고 있습니다!</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
