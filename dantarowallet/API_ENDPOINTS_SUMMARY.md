# DantaroWallet Pro API 엔드포인트 정리

## 🌐 API 문서 접속
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🏥 시스템 상태
- **헬스체크**: `GET /health`
- **테스트**: `GET /api/v1/test`

## 🔐 인증 및 사용자 관리
- **인증**: `/api/v1/auth`
- **사용자 관리**: `/api/v1/users`

## ⚡ Simple Energy Service (개인/소규모 프로젝트용) ✅
**인증 불필요, 5분 내 시작 가능**

| 엔드포인트 | 메소드 | 설명 | 테스트 결과 |
|-----------|--------|------|------------|
| `/api/v1/simple-energy/providers` | GET | 에너지 공급업체 목록 | ✅ 5개 업체 |
| `/api/v1/simple-energy/price` | GET | 실시간 에너지 가격 | ✅ 20 SUN/에너지 |
| `/api/v1/simple-energy/quick-start` | GET | 5분 시작 가이드 | ✅ 작동 |
| `/api/v1/simple-energy/config` | GET | 서비스 설정 상태 | ✅ 작동 |
| `/api/v1/simple-energy/account/{address}` | GET | 계정 에너지 정보 | ✅ 작동 |
| `/api/v1/simple-energy/simulate-purchase` | POST | 구매 시뮬레이션 | ✅ 작동 |

## 🔧 관리자 API (Super Admin)
- **대시보드**: `/api/v1/admin/dashboard`
- **에너지 렌탈**: `/api/v1/admin/energy-rental`
- **시스템 최적화**: `/api/v1/admin/optimization`
- **감사 및 컴플라이언스**: `/api/v1/audit-compliance`

## 🤝 파트너 API (Partner Admin)
- **파트너 에너지**: `/api/v1/partner-energy`
- **파트너 온보딩**: `/api/v1/partner-onboarding`
- **수수료 정책**: `/api/v1/fee-policy`
- **출금 관리**: `/api/v1/withdrawal-management`

## 💰 지갑 및 거래
- **지갑**: `/api/v1/wallet`
- **잔액**: `/api/v1/balance`
- **입금**: `/api/v1/deposit`
- **출금**: `/api/v1/withdrawal`
- **거래**: `/api/v1/transactions`
- **Sweep 자동화**: `/api/v1/sweep`

## ⚡ 에너지 관리
- **에너지 풀**: `/api/v1/energy`
- **에너지 관리**: `/api/v1/energy-management`
- **외부 에너지**: `/api/v1/external-energy`

## 🔗 외부 연동
- **TronLink**: `/api/v1/tronlink`
- **외부 에너지 공급자**: `/api/v1/external-energy`

## 📊 분석 및 통계
- **통합 대시보드**: `/api/v1/integrated-dashboard`
- **통계**: `/api/v1/stats`
- **거래 분석**: `/api/v1/transaction-analytics`

## 🌐 실시간 통신
- **WebSocket**: `/api/v1/ws`

## 🧪 현재 테스트 완료 상태

### ✅ Simple Energy Service
- 모든 6개 엔드포인트 정상 작동
- 실제 API 키 연동 완료 (TronGrid + TronScan)
- 실시간 데이터 조회 성공

### ✅ 시스템 상태
- 서버 정상 실행 (포트 8000)
- 헬스체크 통과
- API 문서 접근 가능

### 📋 다음 테스트 필요 항목
- 인증이 필요한 관리자/파트너 API
- 지갑 관련 API
- 실시간 WebSocket 연결
- 외부 에너지 공급자 연동 (TronNRG, EnergyTRON)

## 🎯 권장 시작 방법

### 개인/소규모 프로젝트
```bash
# 1. TronGrid API 키 발급 (3분)
https://www.trongrid.io/register

# 2. Simple Energy Service 테스트
curl "http://localhost:8000/api/v1/simple-energy/providers"
curl "http://localhost:8000/api/v1/simple-energy/price"
```

### 기업/대규모 프로젝트
1. 관리자 인증 설정
2. 파트너 등록
3. 외부 에너지 공급자 API 키 설정
4. 프로덕션 모드 활성화

---

**생성일**: 2025년 7월 24일  
**마지막 업데이트**: Simple Energy Service 실제 API 키 테스트 완료
