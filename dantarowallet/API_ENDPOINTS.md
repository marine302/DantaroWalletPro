# DantaroWallet API 엔드포인트 목록

## 기본 정보
- **서버 주소**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc 문서**: http://localhost:8000/redoc

## 1. 기본 API

### 헬스체크
- `GET /health` - 서버 상태 확인
  ```bash
  curl -X GET "http://localhost:8000/health"
  ```

### API 테스트
- `GET /api/v1/test` - API v1 작동 테스트
  ```bash
  curl -X GET "http://localhost:8000/api/v1/test"
  ```

## 2. 에너지 풀 관리 API (문서 #40 기반)

**Base URL**: `/api/v1/admin/energy-pool`

### 통계 및 모니터링
- `GET /api/v1/admin/energy-pool/summary` - 에너지 풀 요약 정보
- `GET /api/v1/admin/energy-pool/statistics` - 에너지 풀 통계
- `GET /api/v1/admin/energy-pool/monitoring` - 실시간 모니터링

### 에너지 공급원 관리
- `GET /api/v1/admin/energy-pool/suppliers` - 에너지 공급원 목록
- `POST /api/v1/admin/energy-pool/suppliers` - 새 에너지 공급원 등록
- `PUT /api/v1/admin/energy-pool/suppliers/{supplier_id}` - 에너지 공급원 수정
- `DELETE /api/v1/admin/energy-pool/suppliers/{supplier_id}` - 에너지 공급원 삭제

### 에너지 할당 관리
- `POST /api/v1/admin/energy-pool/allocate` - 에너지 할당 요청
- `GET /api/v1/admin/energy-pool/allocations` - 할당 내역 조회
- `POST /api/v1/admin/energy-pool/cost-calculation` - 비용 계산

## 3. 파트너 에너지 API (문서 #41 기반)

**Base URL**: `/api/v1/partner/energy`

### 에너지 계산 및 요청
- `POST /api/v1/partner/energy/calculate` - 에너지 비용 계산
  ```json
  {
    "amount_usdt": 100,
    "withdrawal_requests": [
      {
        "to_address": "TRX123456789",
        "amount_usdt": 50
      }
    ],
    "batch_mode": true
  }
  ```

- `POST /api/v1/partner/energy/charge` - 에너지 충전 요청
- `POST /api/v1/partner/energy/batch` - 배치 출금 요청

### 모니터링 및 이력
- `GET /api/v1/partner/energy/monitoring` - 에너지 사용량 모니터링
- `GET /api/v1/partner/energy/history` - 에너지 사용 이력
- `GET /api/v1/partner/energy/fees` - 수수료 정책 조회

## 4. 인증 필요 API

대부분의 admin 및 partner API는 인증이 필요합니다:
- **Admin APIs**: Bearer 토큰 또는 관리자 인증 필요
- **Partner APIs**: 파트너 인증 필요

## 5. 테스트 명령어 예시

### 기본 테스트
```bash
# 헬스체크
curl -X GET "http://localhost:8000/health"

# API 테스트
curl -X GET "http://localhost:8000/api/v1/test"
```

### 에너지 API 테스트 (인증 없이는 에러 발생)
```bash
# 에너지 풀 요약 (관리자 인증 필요)
curl -X GET "http://localhost:8000/api/v1/admin/energy-pool/summary"

# 에너지 비용 계산 (파트너 인증 필요)
curl -X POST "http://localhost:8000/api/v1/partner/energy/calculate" \
  -H "Content-Type: application/json" \
  -d '{"amount_usdt": 100, "withdrawal_requests": [{"to_address": "TRX123", "amount_usdt": 50}], "batch_mode": true}'
```

## 6. 주의사항

1. **인증 필요**: 대부분의 비즈니스 로직 API는 인증이 필요합니다
2. **CORS 설정**: 프론트엔드에서 접근 시 CORS 설정 확인
3. **Rate Limiting**: API 호출 횟수 제한이 있을 수 있습니다
4. **데이터 검증**: 모든 요청 데이터는 Pydantic 스키마로 검증됩니다

## 7. 개발 팁

- API 문서: http://localhost:8000/docs 에서 interactive 테스트 가능
- 스키마 확인: http://localhost:8000/openapi.json 에서 OpenAPI 스키마 다운로드
- 에러 응답: 표준화된 에러 응답 포맷 사용
