# TRON HD Wallet & Sweep Automation Tools

이 디렉토리는 TRON HD Wallet 및 Sweep 자동화 시스템의 핵심 도구들을 포함합니다.

## 파일 구조

### 실행 스크립트
- `create_master_and_users.py` - 마스터 지갑 및 사용자 지갑 생성
- `distribute_to_users.py` - 마스터에서 사용자들로 TRX 분산
- `sweep_test_main.py` - 사용자 지갑에서 마스터로 Sweep 테스트

### 결과 파일
- `api_test_result.json` - 지갑 생성 결과 (주소, 시드구문 등)
- `distribute_log.json` - TRX 분산 전송 결과 로그
- `sweep_test_log.json` - Sweep 테스트 결과 로그

## 사용 방법

### 1. 마스터 및 사용자 지갑 생성

```bash
cd /path/to/dantarowallet
python3 scripts/sweep_tools/create_master_and_users.py
```

이 스크립트는:
- 새로운 마스터 HD 지갑을 생성합니다
- 10개의 사용자 지갑을 파생시킵니다
- 모든 키를 암호화하여 데이터베이스에 저장합니다
- 결과를 `api_test_result.json`에 기록합니다

### 2. TRX 분산 전송

먼저 마스터 지갑에 충분한 TRX를 확보한 후:

```bash
python3 scripts/sweep_tools/distribute_to_users.py
```

이 스크립트는:
- `api_test_result.json`에서 마스터 및 사용자 주소를 읽습니다
- 마스터 지갑에서 각 사용자에게 20 TRX씩 전송합니다
- 전송 결과를 `distribute_log.json`에 기록합니다

### 3. Sweep 테스트

```bash
python3 scripts/sweep_tools/sweep_test_main.py
```

이 스크립트는:
- 모든 사용자 지갑의 잔액을 확인합니다
- 수수료를 제외한 전체 잔액을 마스터로 전송합니다
- Sweep 결과를 `sweep_test_log.json`에 기록합니다

## 전체 플로우 예시

```bash
# 1. 지갑 생성
python3 scripts/sweep_tools/create_master_and_users.py

# 2. 마스터 지갑에 TRX 충전 (Faucet 또는 외부 전송)
# TRON Nile Testnet Faucet: https://nileex.io/join/getJoinPage

# 3. 사용자들에게 TRX 분산
python3 scripts/sweep_tools/distribute_to_users.py

# 4. Sweep 테스트 실행
python3 scripts/sweep_tools/sweep_test_main.py
```

## 주요 특징

- **메인 시스템 통합**: 모든 스크립트는 실제 데이터베이스와 서비스를 사용합니다
- **암호화 보안**: 모든 개인키와 시드구문은 EncryptionService로 암호화됩니다
- **TRON 표준**: TronPy 라이브러리와 TRON 표준 주소 파생을 사용합니다
- **상세 로깅**: 모든 트랜잭션과 결과가 JSON 형식으로 기록됩니다
- **에러 처리**: 네트워크 오류, 잔액 부족 등에 대한 적절한 처리를 포함합니다

## 환경 설정

실행 전 다음 환경변수가 설정되어 있는지 확인하세요:

```bash
export TRON_NETWORK=nile  # 테스트넷
export TRON_API_KEY=your_api_key  # TronGrid API 키
```

## 트러블슈팅

### 잔액 부족 오류
- 마스터 지갑에 충분한 TRX가 있는지 확인
- 네트워크 수수료를 고려한 충분한 여유분 확보

### 네트워크 오류
- TRON 네트워크 상태 확인
- API 키의 유효성 확인
- 재시도 로직 활용

### 주소 불일치
- 결과 JSON 파일의 주소와 데이터베이스 주소 일치 여부 확인
- 암호화/복호화 과정의 정상 동작 확인
