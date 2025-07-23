/**
 * 백엔드 연결을 위한 환경 설정
 */

// 환경별 API URL 설정
const API_URLS = {
  development: 'http://localhost:8000',
  production: process.env.NEXT_PUBLIC_API_URL || 'https://api.dantarowallet.com',
  staging: 'https://staging-api.dantarowallet.com'
} as const;

// 현재 환경
const ENVIRONMENT = (process.env.NEXT_PUBLIC_ENV || 'development') as keyof typeof API_URLS;

// API 기본 설정
export const API_CONFIG = {
  BASE_URL: API_URLS[ENVIRONMENT],
  VERSION: process.env.NEXT_PUBLIC_API_VERSION || '/api/v1',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// 인증 관련 설정
export const AUTH_CONFIG = {
  TOKEN_KEY: process.env.NEXT_PUBLIC_JWT_COOKIE_NAME || 'dantaro_admin_token',
  REFRESH_TOKEN_KEY: 'dantaro_refresh_token',
  TOKEN_EXPIRY_BUFFER: 5 * 60 * 1000, // 5분 전 갱신
} as const;

// 에너지 렌탈 관련 설정
export const ENERGY_RENTAL_CONFIG = {
  ENDPOINTS: {
    PLANS: '/energy-rental/plans',
    PARTNER_USAGE: '/energy-rental/partner/:partnerId/usage',
    PARTNER_BILLING: '/energy-rental/partner/:partnerId/billing',
    PARTNER_ALLOCATION: '/energy-rental/partner/:partnerId/allocation',
    POOLS_STATUS: '/energy-rental/pools/status',
    SYSTEM_STATUS: '/energy-rental/system/status',
    RENT_ENERGY: '/energy-rental/rent',
    EXTEND_RENTAL: '/energy-rental/extend',
    CANCEL_RENTAL: '/energy-rental/cancel',
    USAGE_PREDICTION: '/energy-rental/predict-usage'
  },
  POLL_INTERVALS: {
    USAGE_STATS: 30000, // 30초
    BILLING_STATUS: 60000, // 1분
    SYSTEM_STATUS: 10000, // 10초
  }
} as const;

// 로깅 설정
export const LOG_CONFIG = {
  LEVEL: process.env.NEXT_PUBLIC_LOG_LEVEL || 'info',
  ENABLE_API_LOGS: ENVIRONMENT === 'development',
  ENABLE_ERROR_REPORTING: ENVIRONMENT === 'production',
} as const;

// 개발 환경 여부
export const IS_DEVELOPMENT = ENVIRONMENT === 'development';
export const IS_PRODUCTION = ENVIRONMENT === 'production';

// API 오류 메시지
export const API_ERROR_MESSAGES = {
  NETWORK_ERROR: '네트워크 연결을 확인해주세요',
  TIMEOUT_ERROR: '요청 시간이 초과되었습니다',
  UNAUTHORIZED: '인증이 필요합니다',
  FORBIDDEN: '접근 권한이 없습니다',
  NOT_FOUND: '요청한 리소스를 찾을 수 없습니다',
  INTERNAL_ERROR: '서버 내부 오류가 발생했습니다',
  BAD_REQUEST: '잘못된 요청입니다',
} as const;
