# Copilot 문서 #21: 파트너사 가이드 문서화

## 목표
파트너사가 DantaroWallet 화이트라벨 플랫폼을 효과적으로 활용할 수 있도록 완전한 가이드 시스템을 구축합니다.

## 상세 지시사항

### 1. API 연동 매뉴얼 구축

#### 1.1 API 문서 자동 생성 시스템
```python
# app/docs/api_documentation.py
from fastapi import FastAPI
from app.core.config import settings

def setup_api_docs(app: FastAPI):
    """API 문서 커스터마이징"""
    app.title = "DantaroWallet Partner API"
    app.description = """
    ## 파트너사 API 가이드
    
    ### 인증
    - API Key 기반 인증
    - JWT 토큰 관리
    
    ### 주요 엔드포인트
    - 사용자 관리
    - 지갑 관리
    - 거래 처리
    - 에너지 풀 상태
    """
    app.version = "1.0.0"
    app.servers = [
        {"url": "https://api.dantarowallet.com", "description": "Production"},
        {"url": "https://sandbox.dantarowallet.com", "description": "Sandbox"}
    ]
```

#### 1.2 연동 가이드 문서 구조
```markdown
# docs/partner-guide/
├── 01-getting-started/
│   ├── authentication.md      # API 인증 방법
│   ├── sandbox-setup.md       # 샌드박스 환경 설정
│   └── first-api-call.md     # 첫 API 호출 예제
├── 02-user-management/
│   ├── user-creation.md       # 사용자 생성
│   ├── kyc-integration.md     # KYC 연동
│   └── user-permissions.md    # 권한 관리
├── 03-wallet-operations/
│   ├── wallet-creation.md     # 지갑 생성
│   ├── deposit-handling.md    # 입금 처리
│   └── withdrawal-flow.md     # 출금 플로우
├── 04-energy-management/
│   ├── energy-pool-status.md  # 에너지 풀 상태 확인
│   ├── energy-purchase.md     # 에너지 구매
│   └── usage-optimization.md  # 사용 최적화
└── 05-best-practices/
    ├── security-guide.md      # 보안 가이드
    ├── error-handling.md      # 오류 처리
    └── performance-tips.md    # 성능 최적화
```

### 2. 에너지 풀 운영 가이드

#### 2.1 에너지 관리 대시보드 문서
```python
# docs/templates/energy_guide.py
energy_guide_template = """
# 에너지 풀 운영 가이드

## 1. 에너지 풀 개념
- TRON 네트워크의 에너지 시스템
- 거래 수수료 절감 방법
- 에너지 풀 공유 메커니즘

## 2. 모니터링 지표
### 실시간 모니터링
```python
# 에너지 상태 확인 예제
response = await client.get("/api/v1/energy/status")
{
    "total_energy": 1000000,
    "used_energy": 450000,
    "available_energy": 550000,
    "usage_rate": 45.0,
    "estimated_depletion": "2025-01-15T10:30:00Z"
}
```

## 3. 에너지 부족 대응
### 자동 알림 설정
- 임계값 설정 (예: 20% 미만)
- 알림 채널 구성 (이메일, 웹훅)
- 자동 구매 옵션

## 4. 비용 최적화
- 피크 시간대 회피
- 배치 처리 활용
- 에너지 효율적인 거래 설계
"""
```

### 3. 브랜딩 커스터마이징 가이드

#### 3.1 화이트라벨 설정 문서
```yaml
# docs/examples/branding_config.yaml
partner_branding:
  # 기본 정보
  company_name: "PartnerWallet"
  logo_url: "https://partner.com/logo.png"
  
  # 색상 테마
  colors:
    primary: "#1890ff"
    secondary: "#52c41a"
    error: "#ff4d4f"
    warning: "#faad14"
    
  # 텍스트 커스터마이징
  texts:
    welcome_message: "Welcome to PartnerWallet"
    deposit_instruction: "Send USDT to the address below"
    withdrawal_confirmation: "Please confirm your withdrawal"
    
  # 이메일 템플릿
  email_templates:
    header_image: "https://partner.com/email-header.png"
    footer_text: "© 2025 PartnerWallet. All rights reserved."
    
  # 커스텀 도메인
  custom_domain:
    api: "api.partnerwallet.com"
    admin: "admin.partnerwallet.com"
```

### 4. 트러블슈팅 가이드

#### 4.1 공통 문제 해결 가이드
```python
# app/utils/troubleshooting.py
COMMON_ISSUES = {
    "ENERGY_INSUFFICIENT": {
        "description": "에너지 풀 잔량 부족",
        "solutions": [
            "에너지 풀 충전하기",
            "TRX 직접 결제로 전환",
            "거래 대기열에 추가"
        ],
        "code_example": """
# 에너지 부족 시 대체 처리
if energy_pool.available < required_energy:
    if user.prefer_trx_payment:
        return process_with_trx(transaction)
    else:
        return add_to_queue(transaction)
"""
    },
    "API_RATE_LIMIT": {
        "description": "API 호출 제한 초과",
        "solutions": [
            "요청 속도 조절",
            "배치 API 사용",
            "캐싱 활용"
        ]
    }
}
```

### 5. 베스트 프랙티스 문서

#### 5.1 보안 체크리스트
```markdown
# docs/partner-guide/security-checklist.md

## API 보안
- [ ] API 키 환경변수 저장
- [ ] HTTPS 전용 통신
- [ ] IP 화이트리스트 설정
- [ ] 요청 서명 검증

## 사용자 보안
- [ ] 2FA 활성화 권장
- [ ] 세션 타임아웃 설정
- [ ] 비정상 활동 모니터링

## 거래 보안
- [ ] 출금 한도 설정
- [ ] 출금 지연 시간 구현
- [ ] 의심 거래 자동 차단

## 데이터 보안
- [ ] 민감 정보 암호화
- [ ] 정기 보안 감사
- [ ] 접근 로그 모니터링
```

#### 5.2 성능 최적화 가이드
```python
# docs/examples/performance_optimization.py
"""
## 성능 최적화 팁

### 1. API 호출 최적화
- 배치 요청 활용
- 응답 캐싱
- 필요한 필드만 요청

### 2. 웹훅 처리
- 비동기 처리
- 재시도 로직
- 멱등성 보장

### 3. 데이터베이스 쿼리
- 인덱스 활용
- N+1 문제 방지
- 커넥션 풀 관리
"""

# 배치 요청 예제
async def batch_create_wallets(user_ids: List[int]):
    """여러 사용자의 지갑을 한 번에 생성"""
    batch_request = {
        "operations": [
            {
                "method": "POST",
                "path": "/api/v1/wallets",
                "body": {"user_id": user_id}
            }
            for user_id in user_ids
        ]
    }
    
    response = await client.post("/api/v1/batch", json=batch_request)
    return response.json()
```

### 6. 샘플 통합 코드

#### 6.1 Python SDK 예제
```python
# docs/examples/python_integration.py
import asyncio
import httpx
from typing import Optional, Dict, Any

class DantaroWalletClient:
    """DantaroWallet Partner API Client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dantarowallet.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"X-API-Key": api_key},
            timeout=30.0
        )
    
    async def create_user(self, email: str, external_id: str) -> Dict[str, Any]:
        """새 사용자 생성"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/users",
            json={
                "email": email,
                "external_id": external_id
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def create_wallet(self, user_id: int) -> Dict[str, Any]:
        """사용자 지갑 생성"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/wallets",
            json={"user_id": user_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_balance(self, wallet_address: str) -> Dict[str, Any]:
        """지갑 잔액 조회"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/wallets/{wallet_address}/balance"
        )
        response.raise_for_status()
        return response.json()

# 사용 예제
async def main():
    client = DantaroWalletClient(api_key="your-api-key")
    
    # 사용자 생성
    user = await client.create_user(
        email="user@example.com",
        external_id="partner-user-123"
    )
    
    # 지갑 생성
    wallet = await client.create_wallet(user_id=user["id"])
    
    # 잔액 확인
    balance = await client.get_balance(wallet["address"])
    print(f"Wallet balance: {balance['usdt_balance']} USDT")

if __name__ == "__main__":
    asyncio.run(main())
```

## 검증 포인트

- [ ] API 문서가 자동으로 생성되는가?
- [ ] 모든 API 엔드포인트에 예제가 포함되어 있는가?
- [ ] 에너지 풀 운영 가이드가 명확한가?
- [ ] 브랜딩 설정이 쉽게 이해되는가?
- [ ] 트러블슈팅 가이드가 실용적인가?
- [ ] 보안 체크리스트가 완전한가?
- [ ] 샘플 코드가 실제로 작동하는가?
- [ ] 파트너사가 독립적으로 통합할 수 있는가?