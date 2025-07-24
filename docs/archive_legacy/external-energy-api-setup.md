# 🔑 외부 에너지 공급업체 API 키 설정 가이드

**업데이트 일자**: 2025년 7월 24일  
**목적**: TronNRG, EnergyTRON 등 외부 에너지 공급업체 API 키 설정 방법

## 📋 개요

DantaroWallet에서 외부 에너지 공급업체와 연동하기 위해서는 각 공급업체의 API 키가 필요합니다. 현재 지원되는 공급업체는 다음과 같습니다:

- **TronNRG**: 트론 에너지 전문 공급업체
- **EnergyTRON**: B2B/B2C 하이브리드 에너지 서비스

## 🔧 설정 방법

### 1. 환경 변수 파일 설정

#### 개발 환경 (`.env`)
```bash
# External Energy Providers API Keys
# TronNRG API 설정
TRONNRG_API_KEY=your-tronnrg-api-key-here
TRONNRG_BASE_URL=https://api.tronnrg.com/v1

# EnergyTRON API 설정
ENERGYTRON_API_KEY=your-energytron-api-key-here
ENERGYTRON_PARTNER_ID=your-partner-id-here  
ENERGYTRON_BASE_URL=https://api.energytron.io/v1

# External Energy Service Configuration
EXTERNAL_ENERGY_TIMEOUT=30
EXTERNAL_ENERGY_RETRY_COUNT=3
EXTERNAL_ENERGY_RETRY_DELAY=1
```

#### 프로덕션 환경 (`.env.prod`)
```bash
# External Energy Providers API Keys (Production)
TRONNRG_API_KEY=${TRONNRG_API_KEY}
ENERGYTRON_API_KEY=${ENERGYTRON_API_KEY}
ENERGYTRON_PARTNER_ID=${ENERGYTRON_PARTNER_ID}
```

### 2. API 키 발급 방법

#### 🟢 TronNRG API 키 발급
1. **웹사이트 방문**: https://tronnrg.com
2. **계정 생성**: 비즈니스 계정으로 회원가입
3. **API 키 신청**: 
   - 대시보드 > API 관리 > 새 API 키 생성
   - 용도: "DantaroWallet 통합"
   - 권한: Market Data, Order Management
4. **API 키 복사**: 생성된 키를 `.env` 파일에 설정

```bash
# 예시
TRONNRG_API_KEY=trx_live_sk_abcd1234efgh5678ijkl9012mnop3456
```

#### 🟡 EnergyTRON API 키 발급  
1. **웹사이트 방문**: https://energytron.io
2. **파트너 신청**: B2B 파트너십 프로그램 신청
3. **API 키 발급**:
   - 파트너 대시보드 > 개발자 도구 > API 키 생성
   - 통합 타입: "화이트라벨 솔루션"
4. **파트너 ID 확인**: 계정 설정에서 파트너 ID 확인

```bash
# 예시
ENERGYTRON_API_KEY=et_partner_sk_1234567890abcdef
ENERGYTRON_PARTNER_ID=partner_dantarowallet_001
```

### 3. 설정 검증

API 키 설정 후 다음 명령어로 연동 상태를 확인할 수 있습니다:

```bash
# 개발 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# API 테스트
curl -X GET "http://localhost:8000/api/v1/external-energy/providers" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 헬스 체크
curl -X GET "http://localhost:8000/api/v1/external-energy/providers/health"
```

## 🔒 보안 고려사항

### 1. API 키 보안
- ✅ **절대 공개하지 마세요**: Git 커밋에 API 키 포함 금지
- ✅ **환경 변수 사용**: `.env` 파일 사용하고 `.gitignore`에 추가
- ✅ **권한 최소화**: 필요한 권한만 부여
- ✅ **정기 로테이션**: 주기적으로 API 키 갱신

### 2. 네트워크 보안
- ✅ **HTTPS 사용**: 모든 API 호출은 HTTPS로
- ✅ **IP 화이트리스트**: 가능한 경우 IP 제한 설정
- ✅ **Rate Limiting**: API 호출 빈도 제한

### 3. 모니터링
- ✅ **API 키 사용량 추적**: 비정상적인 사용 패턴 감지
- ✅ **에러 로깅**: API 호출 실패 시 상세 로그 기록
- ✅ **알림 설정**: API 키 만료 전 미리 알림

## 🧪 테스트 방법

### 1. 로컬 테스트
```python
# 테스트 스크립트 실행
python3 scripts/test_external_energy_apis.py

# 또는 직접 테스트
python3 -c "
import asyncio
from app.services.external_energy.tronnrg_service import tronnrg_service

async def test():
    try:
        data = await tronnrg_service.get_market_price()
        print('✅ TronNRG 연동 성공:', data)
    except Exception as e:
        print('❌ TronNRG 연동 실패:', e)

asyncio.run(test())
"
```

### 2. API 응답 예시
#### TronNRG 시장 가격 조회
```json
{
  "success": true,
  "data": {
    "price_per_energy": 0.00042,
    "currency": "TRX",
    "available_energy": 1500000000,
    "last_updated": "2025-07-24T10:30:00Z"
  }
}
```

#### EnergyTRON 공급자 목록
```json
{
  "success": true,
  "data": [
    {
      "provider_id": "energytron_pool_1",
      "name": "EnergyTRON Premium Pool",
      "price_per_energy": 0.00038,
      "available_energy": 2000000000,
      "reliability_score": 98.5
    }
  ]
}
```

## 🚨 문제 해결

### 일반적인 오류와 해결법

#### 1. API 키 인증 실패
```
Error: 401 Unauthorized - Invalid API key
```
**해결법**: 
- API 키가 올바른지 확인
- API 키 권한 설정 확인
- API 키 만료 여부 확인

#### 2. 네트워크 연결 오류
```
Error: Connection timeout
```
**해결법**:
- 인터넷 연결 상태 확인
- 방화벽 설정 확인
- VPN 사용 시 우회 확인

#### 3. 요청 한도 초과
```
Error: 429 Too Many Requests
```
**해결법**:
- API 호출 빈도 줄이기
- Rate limiting 설정 확인
- 더 높은 티어 계정으로 업그레이드

## 📞 지원

### 공급업체 지원
- **TronNRG**: support@tronnrg.com
- **EnergyTRON**: partners@energytron.io

### 개발팀 지원  
- **GitHub Issues**: 기술적 문제 보고
- **팀 Slack**: 긴급 지원 요청

---

**⚠️ 중요**: 프로덕션 배포 전에 반드시 모든 API 키가 정상 작동하는지 확인하세요!
