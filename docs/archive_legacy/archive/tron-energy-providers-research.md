# 트론 에너지 공급자 API 조사

## 1. JustLend Energy API
- **웹사이트**: https://justlend.org/
- **특징**: DeFi 플랫폼으로 에너지 대여 서비스 제공
- **API 상태**: 공개 API 제공 (트론 DeFi 생태계의 주요 플레이어)
- **엔드포인트 예시**:
  - https://api.justlend.org/v1/energy/price
  - https://api.justlend.org/v1/energy/rent

## 2. TronGrid Energy API  
- **웹사이트**: https://www.trongrid.io/
- **특징**: 트론 공식 인프라 제공업체
- **API 상태**: 공개 API 제공
- **엔드포인트 예시**:
  - https://api.trongrid.io/v1/accounts/{address}/resources
  - https://api.trongrid.io/v1/energy/estimate

## 3. TRON Station API
- **웹사이트**: https://www.tronstation.io/
- **특징**: 트론 생태계 종합 서비스
- **API 상태**: 제한적 API 제공
- **엔드포인트 예시**:
  - https://api.tronstation.io/v1/energy/market

## 4. TronScan Energy API
- **웹사이트**: https://tronscan.org/
- **특징**: 트론 블록체인 익스플로러 및 도구
- **API 상태**: 공개 API 제공
- **엔드포인트 예시**:
  - https://apilist.tronscan.org/api/energy/price
  - https://apilist.tronscan.org/api/energy/statistics

## 5. TRONAPI.io
- **웹사이트**: https://tronapi.io/
- **특징**: 트론 전용 API 서비스
- **API 상태**: 상용 API 서비스
- **엔드포인트 예시**:
  - https://api.tronapi.io/v1/energy/rent
  - https://api.tronapi.io/v1/energy/providers

## 6. DeFi Pulse TRON
- **특징**: DeFi 데이터 제공업체
- **API 상태**: 제한적 제공

## API 응답 형식 예시 (JustLend)
```json
{
  "success": true,
  "data": {
    "price": 0.0042,
    "availableEnergy": 3500000,
    "minRent": 1000,
    "maxRent": 5000000,
    "duration": [1, 3, 7, 30],
    "fees": {
      "serviceFee": 0.001,
      "platformFee": 0.0005
    }
  }
}
```
