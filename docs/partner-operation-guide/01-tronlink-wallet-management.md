# TronLink 지갑 관리 베스트 프랙티스

## 1. 지갑 구조 설계

### 1.1 권장 지갑 구조
파트너사는 다음과 같은 3단계 지갑 구조를 사용하는 것을 권장합니다:

#### Hot Wallet (운영 지갑)
- **용도**: 일일 출금 처리
- **보유량**: 일일 출금 예상량의 120%
- **보안**: 다중 서명 권장
- **특징**:
  - 자동 출금 처리에 사용
  - 실시간 모니터링 필수
  - 일일 한도 설정

#### Warm Wallet (중간 지갑)
- **용도**: Hot Wallet 보충용
- **보유량**: 주간 출금 예상량의 50%
- **보안**: 하드웨어 지갑 연동
- **특징**:
  - 주 1-2회 Hot Wallet으로 이동
  - 수동 승인 필요
  - 접근 권한 제한

#### Cold Wallet (보관 지갑)
- **용도**: 장기 보관
- **보유량**: 전체 자산의 70% 이상
- **보안**: 오프라인 보관, 다중 서명 필수
- **특징**:
  - 분기별 검토
  - 최소 3인 이상의 서명 필요
  - 물리적 보안 적용

### 1.2 TronLink 연동 관리

#### 브라우저 보안
```javascript
// 안전한 TronLink 연결 확인
const checkTronLinkSecurity = async () => {
  // 1. 정품 TronLink 확인
  if (!window.tronWeb || !window.tronLink) {
    throw new Error('TronLink가 설치되지 않았습니다');
  }
  
  // 2. 버전 확인
  const version = await window.tronLink.request({ method: 'wallet_getVersion' });
  if (version < '4.0.0') {
    throw new Error('TronLink 업데이트가 필요합니다');
  }
  
  // 3. 네트워크 확인
  const network = window.tronWeb.fullNode.host;
  if (!network.includes('trongrid.io')) {
    throw new Error('신뢰할 수 없는 네트워크입니다');
  }
};
```

#### 트랜잭션 서명 보안
```javascript
// 트랜잭션 서명 전 검증
const validateTransaction = (tx) => {
  const checks = {
    // 수신 주소 화이트리스트 확인
    isWhitelisted: WHITELIST_ADDRESSES.includes(tx.to),
    
    // 금액 한도 확인
    isWithinLimit: tx.amount <= DAILY_LIMIT,
    
    // 가스 한도 확인
    isGasReasonable: tx.gas <= MAX_GAS_LIMIT,
    
    // 스마트 컨트랙트 확인
    isKnownContract: KNOWN_CONTRACTS.includes(tx.to)
  };
  
  return Object.values(checks).every(check => check);
};
```

## 2. 일일 운영 절차

### 2.1 아침 체크리스트 (09:00)
1. **지갑 잔액 확인**
   ```bash
   # Hot Wallet 잔액 체크
   curl -X GET "https://api.dantarowallet.com/v1/wallet/balance" \
     -H "Authorization: Bearer {API_KEY}"
   ```

2. **에너지 풀 상태 확인**
   ```bash
   # 에너지 잔량 확인
   curl -X GET "https://api.dantarowallet.com/v1/energy/status" \
     -H "Authorization: Bearer {API_KEY}"
   ```

3. **미처리 출금 요청 확인**
   ```bash
   # 대기 중인 출금 확인
   curl -X GET "https://api.dantarowallet.com/v1/withdrawals/pending" \
     -H "Authorization: Bearer {API_KEY}"
   ```

### 2.2 정오 체크리스트 (12:00)
1. **트랜잭션 로그 검토**
2. **에러 알림 확인**
3. **시스템 성능 모니터링**

### 2.3 저녁 체크리스트 (18:00)
1. **일일 거래량 리포트 생성**
2. **익일 운영 계획 수립**
3. **보안 로그 검토**

## 3. 월간 운영 절차

### 3.1 월초 작업 (매월 1일)
1. **월간 정산 보고서 생성**
2. **지갑 간 자산 재분배**
3. **API 키 로테이션 검토**

### 3.2 월말 작업 (매월 말일)
1. **월간 성과 리포트**
2. **보안 감사 실행**
3. **시스템 백업 검증**

## 4. 비상 상황 대응

### 4.1 지갑 보안 침해 의심
1. **즉시 조치**:
   - 모든 자동 출금 중단
   - 관련 지갑 격리
   - 보안팀 즉시 연락

2. **조사 절차**:
   - 트랜잭션 히스토리 분석
   - 접근 로그 검토
   - 외부 보안 업체 연락

### 4.2 TronLink 연결 실패
1. **기본 대응**:
   ```javascript
   // TronLink 재연결 시도
   const reconnectTronLink = async () => {
     try {
       await window.tronLink.request({ method: 'eth_requestAccounts' });
       console.log('TronLink 재연결 성공');
     } catch (error) {
       console.error('재연결 실패:', error);
       // 백업 지갑 활성화
       activateBackupWallet();
     }
   };
   ```

2. **백업 절차**:
   - 대체 지갑 활성화
   - 수동 트랜잭션 처리
   - 기술팀 지원 요청

## 5. 성능 최적화

### 5.1 TronLink 최적화
```javascript
// TronLink 성능 최적화 설정
const optimizeTronLink = () => {
  // 1. 트랜잭션 배치 처리
  const batchTransactions = (txs) => {
    return txs.reduce((batches, tx, index) => {
      const batchIndex = Math.floor(index / 10);
      batches[batchIndex] = batches[batchIndex] || [];
      batches[batchIndex].push(tx);
      return batches;
    }, []);
  };
  
  // 2. 가스 가격 최적화
  const optimizeGasPrice = async () => {
    const gasPrice = await window.tronWeb.trx.getGasPrice();
    return Math.min(gasPrice * 1.1, MAX_GAS_PRICE);
  };
};
```

### 5.2 모니터링 대시보드
```javascript
// 실시간 모니터링 설정
const setupMonitoring = () => {
  setInterval(async () => {
    const metrics = {
      balance: await checkBalance(),
      energy: await checkEnergyPool(),
      transactions: await getPendingTransactions(),
      errors: await getRecentErrors()
    };
    
    // 대시보드 업데이트
    updateDashboard(metrics);
    
    // 알림 체크
    checkAlerts(metrics);
  }, 30000); // 30초마다 체크
};
```

## 6. 문제 해결 가이드

### 6.1 일반적인 문제들

#### TronLink 서명 실패
**증상**: 트랜잭션 서명 시 오류 발생
**해결책**:
1. TronLink 확장 프로그램 재시작
2. 브라우저 캐시 삭제
3. TronLink 버전 확인 및 업데이트

#### 에너지 부족 오류
**증상**: 트랜잭션 전송 시 에너지 부족 메시지
**해결책**:
1. 에너지 풀 상태 확인
2. 긴급 TRX 스테이킹 실행
3. 외부 에너지 구매 검토

#### API 호출 한도 초과
**증상**: 429 Too Many Requests 오류
**해결책**:
1. 요청 간격 조정
2. 배치 처리 적용
3. API 키 분산 사용

## 7. 베스트 프랙티스 요약

### 7.1 보안
- ✅ 다중 서명 지갑 사용
- ✅ 정기적인 보안 감사
- ✅ API 키 주기적 로테이션
- ✅ 2FA 인증 필수

### 7.2 운영
- ✅ 실시간 모니터링 구축
- ✅ 자동화된 알림 시스템
- ✅ 정기적인 백업 실행
- ✅ 문서화된 절차 준수

### 7.3 성능
- ✅ 트랜잭션 배치 처리
- ✅ 가스 가격 최적화
- ✅ 에너지 효율적 사용
- ✅ 네트워크 부하 분산
