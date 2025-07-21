/**
 * 공통 타입 정의
 * - API 응답 타입
 * - 유틸리티 타입
 * - 재사용 가능한 인터페이스
 */

// API 응답 기본 구조
export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
  timestamp?: string;
}

// 페이지네이션 응답
export interface PaginatedApiResponse<T = unknown> extends ApiResponse<T[]> {
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// 에러 응답
export interface ApiError {
  success: false;
  error: string;
  message: string;
  statusCode?: number;
  timestamp: string;
}

// 로딩 상태
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

// 연결 상태
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

// 공급자 상태
export type ProviderStatus = 'online' | 'offline' | 'maintenance' | 'error';

// 알림 우선순위
export type AlertPriority = 'low' | 'medium' | 'high' | 'critical';

// 거래 상태
export type TransactionStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

// 거래 타입
export type TransactionType = 'energy_purchase' | 'energy_transfer' | 'fee_payment' | 'withdrawal';

// 기본 엔티티
export interface BaseEntity {
  id: string | number;
  createdAt: string;
  updatedAt: string;
}

// 타임스탬프 유틸리티
export interface WithTimestamp {
  timestamp: string;
}

// 이름이 있는 엔티티
export interface NamedEntity {
  name: string;
  description?: string;
}

// 상태가 있는 엔티티
export interface StatusEntity {
  status: string;
  isActive?: boolean;
}

// 가격 정보
export interface PriceInfo {
  pricePerEnergy: number;
  currency: string;
  lastUpdated: string;
}

// 통계 정보
export interface Statistics {
  totalCount: number;
  activeCount: number;
  inactiveCount: number;
  percentage?: number;
}

// Unknown 타입 대신 사용할 안전한 타입들
export type SafeRecord = Record<string, unknown>;
export type SafeData = unknown;
export type SafeValue = string | number | boolean | null | undefined;
