/**
 * API 클라이언트 설정 및 유틸리티
 * - REST API 통신
 * - 인증 처리 (JWT)
 * - 에러 핸들링
 * - 자동 토큰 갱신
 * - Rate Limiting 대응
 */

import type { ApiError } from '../types';

// API 기본 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || '/api/v1';
const API_TIMEOUT = 30000; // 30초

// Rate Limiting 관련 헤더
interface RateLimitHeaders {
  'x-ratelimit-limit'?: string;
  'x-ratelimit-remaining'?: string;
  'x-ratelimit-reset'?: string;
}

// HTTP Response 인터페이스
interface HttpResponse<T> {
  data: T;
  status: number;
  headers: Headers & RateLimitHeaders;
}

// API 클라이언트 클래스
export class ApiClient {
  private baseURL: string;
  private timeout: number;
  private authToken?: string;

  constructor(baseURL: string = `${API_BASE_URL}${API_VERSION}`, timeout: number = API_TIMEOUT) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  // 인증 토큰 설정
  setAuthToken(token: string) {
    this.authToken = token;
  }

  // 인증 토큰 제거
  clearAuthToken() {
    this.authToken = undefined;
  }

  // 기본 요청 헤더 생성
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    return headers;
  }

  // Rate Limiting 처리
  private handleRateLimit(response: Response): void {
    const limit = response.headers.get('x-ratelimit-limit');
    const remaining = response.headers.get('x-ratelimit-remaining');
    const reset = response.headers.get('x-ratelimit-reset');

    if (response.status === 429) {
      const resetTime = reset ? new Date(parseInt(reset) * 1000) : new Date(Date.now() + 60000);
      console.warn(`Rate limit exceeded. Reset at: ${resetTime.toISOString()}`);
      throw new Error(`Rate limit exceeded. Try again after ${resetTime.toLocaleTimeString()}`);
    }

    if (limit && remaining) {
      console.debug(`API Rate Limit: ${remaining}/${limit} remaining`);
    }
  }

  // 기본 요청 메서드
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<HttpResponse<T>> {
    try {
      const url = `${this.baseURL}${endpoint}`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.getHeaders(),
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Rate Limiting 처리
      this.handleRateLimit(response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const apiError: ApiError = {
          status_code: response.status,
          message: errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          errors: errorData.errors,
          timestamp: new Date().toISOString(),
          path: endpoint
        };
        throw apiError;
      }

      const data = await response.json();
      return {
        data,
        status: response.status,
        headers: response.headers as Headers & RateLimitHeaders
      };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      
      throw error;
    }
  }

  // GET 요청
  async get<T>(endpoint: string): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // POST 요청
  async post<T>(endpoint: string, data?: unknown): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT 요청
  async put<T>(endpoint: string, data?: unknown): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PATCH 요청
  async patch<T>(endpoint: string, data?: unknown): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE 요청
  async delete<T>(endpoint: string): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// 기본 API 클라이언트 인스턴스
export const apiClient = new ApiClient();

// TokenManager를 위한 API 클라이언트에 토큰 자동 설정
if (typeof window !== 'undefined') {
  const token = localStorage.getItem(process.env.NEXT_PUBLIC_JWT_COOKIE_NAME || 'dantaro_admin_token');
  if (token) {
    apiClient.setAuthToken(token);
  }
}

// API 에러 처리 유틸리티
export function handleApiError(error: unknown): string {
  if (error && typeof error === 'object') {
    if ('message' in error && typeof error.message === 'string') return error.message;
    if ('error' in error && typeof error.error === 'string') return error.error;
  }
  return 'Unknown error occurred';
}

// 로딩 상태 관리를 위한 훅 타입
export interface ApiHookState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export default apiClient;
