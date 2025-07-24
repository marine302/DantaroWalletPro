# 🔑 외부 에너지 공급업체 API 키 발급 가이드

**작성일**: 2025년 7월 24일  
**목적**: TronNRG, EnergyTRON 등 외부 에너지 공급업체 API 키 발급 및 설정 가이드

## 📋 현재 상황

### ✅ **구현 완료 상태**
- TronNRG API 연동 서비스 완성
- EnergyTRON API 연동 서비스 완성  
- 19개 외부 에너지 API 엔드포인트 등록
- 설정 파일 및 환경 변수 준비 완료

### 🔧 **현재 사용 중인 키**
```env
# 현재 .env 파일
TRONNRG_API_KEY=demo_key_tronnrg_2024
ENERGYTRON_API_KEY=demo_key_energytron
ENERGYTRON_PARTNER_ID=partner_demo
```

## 🏢 1. TronNRG API 키 발급

### 📍 **TronNRG 개요**
- **웹사이트**: https://tronnrg.com
- **API 문서**: https://docs.tronnrg.com  
- **서비스**: 트론 네트워크 에너지 거래 플랫폼
- **타겟**: B2B 에너지 공급 서비스

### 🔗 **API 키 발급 과정**

#### **1단계: 회원가입**
```bash
# 접속: https://tronnrg.com/register
1. 이메일 주소 입력
2. 비즈니스 정보 입력
   - 회사명: DantaroWallet  
   - 비즈니스 유형: Cryptocurrency Wallet
   - 예상 월 거래량: [실제 예상량 입력]
3. 이메일 인증 완료
```

#### **2단계: KYB (Know Your Business) 인증**
```
필요 서류:
- 사업자등록증 또는 법인등록증
- 대표자 신분증  
- 사업 계획서 (에너지 사용 목적)
- 예상 거래량 및 규모 설명
```

#### **3단계: API 키 신청**
```bash
# 대시보드 접속 후
1. Developer 섹션 이동
2. "New API Key" 생성
3. 권한 설정:
   - Market Data: Read
   - Order Management: Read/Write  
   - Account Info: Read
4. IP 화이트리스트 설정 (서버 IP 추가)
```

#### **4단계: 결제 정보 등록**
```
- 결제 방법: 신용카드 또는 은행 계좌
- 최소 보증금: $1,000 ~ $5,000 (거래량에 따라)
- 수수료 구조: 거래량별 차등 (0.1% ~ 0.5%)
```

---

## 🏢 2. EnergyTRON API 키 발급

### 📍 **EnergyTRON 개요**  
- **웹사이트**: https://energytron.io
- **API 문서**: https://docs.energytron.io
- **서비스**: B2B/B2C 하이브리드 에너지 플랫폼
- **특징**: 파트너십 프로그램, 화이트라벨 솔루션

### 🔗 **API 키 발급 과정**

#### **1단계: 파트너 신청**
```bash
# 접속: https://energytron.io/partners
1. 파트너십 신청서 작성
   - 서비스 유형: Cryptocurrency Wallet
   - 예상 사용자 수: [실제 예상치]
   - 월 에너지 사용량: [예상량]
2. 비즈니스 모델 설명
3. 기술 통합 계획서 제출
```

#### **2단계: 기술 검토**
```
EnergyTRON 기술팀 검토:
- API 통합 능력 평가
- 보안 수준 검토  
- 사용량 예측 분석
- 승인/거부 결정 (보통 3-5영업일)
```

#### **3단계: 계약 및 설정**
```bash
1. 파트너 계약서 체결
2. 파트너 ID 발급 (예: PARTNER_DANTARO_001)
3. API 키 발급:
   - Production API Key
   - Sandbox API Key (테스트용)
4. 초기 크레딧 설정
```

#### **4단계: 통합 테스트**
```bash
# Sandbox 환경에서 테스트
1. API 연결 테스트
2. 주문 생성/취소 테스트  
3. 결제 플로우 테스트
4. 에러 핸들링 테스트
5. 승인 후 Production 환경 이전
```

---

## 🏢 3. 기타 공급업체 옵션

### **JustLend Energy**
- **웹사이트**: https://justlend.org
- **특징**: 트론 생태계 기반 DeFi 에너지 대출
- **발급**: 지갑 연결 후 즉시 사용 가능

### **SunPump Energy**  
- **웹사이트**: https://sunpump.meme
- **특징**: 밈코인 기반 에너지 거래
- **발급**: 커뮤니티 참여 후 신청

### **TronScan Energy**
- **웹사이트**: https://tronscan.org
- **특징**: 트론스캔 공식 에너지 서비스
- **발급**: 트론스캔 계정 연동

---

## ⚙️ 개발 환경에서의 임시 해결책

### **Mock API 서버 활용**
현재 개발 중이므로 실제 API 키 없이도 테스트 가능:

```python
# app/services/external_energy/mock_service.py
class MockEnergyService:
    """개발용 Mock 에너지 서비스"""
    
    async def get_market_price(self):
        return {
            "price": 0.00002,  # TRX per Energy
            "available": 10000000,
            "timestamp": "2025-07-24T12:00:00Z"
        }
    
    async def create_order(self, amount: int):
        return {
            "order_id": f"mock_order_{random.randint(1000, 9999)}",
            "status": "completed",
            "amount": amount,
            "cost": amount * 0.00002
        }
```

### **환경별 설정**
```bash
# 개발 환경 (.env.development)
TRONNRG_API_KEY=demo_key_tronnrg_2024
ENERGYTRON_API_KEY=demo_key_energytron
USE_MOCK_ENERGY_SERVICE=true

# 프로덕션 환경 (.env.production)  
TRONNRG_API_KEY=prod_api_key_from_tronnrg
ENERGYTRON_API_KEY=prod_api_key_from_energytron
USE_MOCK_ENERGY_SERVICE=false
```

---

## 📊 비용 및 수수료 구조

### **TronNRG 비용 구조**
- **가입비**: 무료
- **최소 보증금**: $1,000 - $5,000
- **거래 수수료**: 0.1% - 0.5% (거래량별)
- **API 호출**: 무료 (월 100만 호출까지)

### **EnergyTRON 파트너십**
- **파트너십 수수료**: 협상 가능
- **수익 분배**: 거래량에 따라 5-15% 커미션
- **최소 계약 기간**: 12개월
- **기술 지원**: 무료 포함

---

## 🚀 권장 진행 순서

### **단계 1: 개발 완료 (현재)**
```bash
✅ Mock 서비스로 개발 및 테스트 완료
✅ API 구조 및 엔드포인트 구현 완료
✅ 프론트엔드 연동 테스트 완료
```

### **단계 2: 파트너십 신청**
```bash
📋 TronNRG 회원가입 및 KYB 인증
📋 EnergyTRON 파트너십 신청
📋 계약 협상 및 조건 확정
```

### **단계 3: 통합 테스트**  
```bash
🔧 Sandbox 환경에서 실제 API 테스트
🔧 에러 핸들링 및 예외 상황 대응
🔧 성능 테스트 및 최적화
```

### **단계 4: 프로덕션 배포**
```bash
🚀 실제 API 키 적용
🚀 모니터링 시스템 구축  
🚀 사용자 서비스 시작
```

---

## 📞 연락처 및 지원

### **TronNRG 지원**
- **이메일**: partnerships@tronnrg.com
- **텔레그램**: @TronNRGSupport  
- **문의**: 사업 제휴 관련

### **EnergyTRON 지원**
- **이메일**: partners@energytron.io
- **디스코드**: EnergyTRON Official
- **문의**: 기술 통합 관련

### **기술 문의**
개발 과정에서 API 연동 관련 기술적 문의사항이 있으시면 각 플랫폼의 개발자 문서를 참조하거나 기술 지원팀에 문의하세요.

---

**⚠️ 주의사항**: 실제 API 키는 보안이 중요하므로 환경 변수로 관리하고, 절대 코드에 하드코딩하지 마세요. 또한 정기적으로 API 키를 갱신하고 권한을 최소화하여 보안을 유지하세요.
