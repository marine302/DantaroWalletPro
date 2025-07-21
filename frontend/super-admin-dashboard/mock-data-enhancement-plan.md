# Mock 데이터 개선 계획

## 현재 상황
- Mock 서버: 완전히 독립적인 랜덤 데이터 생성
- 백엔드 API: 실제 DB 기반, 현재 최적화 작업 중
- Fallback 시스템: Backend → Mock → Default 순서로 자동 전환

## 개선 방안

### 1. Hybrid Mock 데이터 (권장)
```javascript
// 실제 DB 스키마를 기반으로 한 더 현실적인 Mock 데이터
const REALISTIC_MOCK_DATA = {
  // 실제 백엔드 스키마와 동일한 구조
  users: [
    { id: 1, email: "admin@dantaro.com", role: "super-admin", ... },
    // 실제 시나리오를 반영한 테스트 데이터
  ],
  
  // 일관된 관계성 유지
  transactions: [
    { id: "tx_001", userId: 1, partnerId: 1, ... },
    // 실제 비즈니스 로직 반영
  ]
};
```

### 2. 실제 백엔드 DB Snapshot 기반 (선택사항)
```javascript
// 주기적으로 백엔드 DB에서 익명화된 데이터 가져오기
async function syncMockDataFromBackend() {
  try {
    const snapshot = await fetch('/api/admin/mock-data-snapshot');
    // 개인정보 제거 후 Mock 데이터로 활용
  } catch (error) {
    // 기존 정적 Mock 데이터 사용
  }
}
```

### 3. 환경별 Mock 전략
```javascript
const MOCK_STRATEGIES = {
  development: 'realistic-static',  // 일관된 테스트 데이터
  testing: 'randomized',           // 현재 방식 유지
  staging: 'backend-snapshot',     // 실제 데이터 기반
  production: 'backend-only'       // Mock 비활성화
};
```

## 권장사항

현재 백엔드 최적화 중이므로:

1. **단기**: 현재 Mock 시스템 유지 (안정성 우선)
2. **중기**: 백엔드 최적화 완료 후 Realistic Mock 데이터로 개선
3. **장기**: 실제 DB 스키마 기반 Mock 데이터 자동 생성 시스템 구축

이렇게 하면 백엔드 최적화 작업에 영향을 주지 않으면서도, 향후 더 현실적인 테스트 환경을 구축할 수 있습니다.
