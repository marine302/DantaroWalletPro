# 관리자 페이지 리팩토링 TODO

**작성일**: 2025년 7월 5일  
**업데이트**: 2025년 7월 5일  
**현재 상태**: ✅ 설계 완료, 구현 준비됨

## 📋 **상황 업데이트 - 2025년 7월 5일**

### ✅ **완료된 작업**
- [x] **수수료 시스템 비즈니스 로직 명확화 완료**
  - 📄 `/docs/FEE_SYSTEM_CLARIFICATION.md` 생성
  - 실제 비즈니스 모델 정확히 파악
  - 기존 수수료 시스템이 올바르게 구현되어 있음을 확인

### ✅ **오해 해결**
1. **이전 오해**: 수수료 시스템이 TRON Energy와 맞지 않아 잘못됨
2. **실제 구조**: 
   - **TRON 레벨**: 본사가 에너지로 스폰서십 (TRX freeze)
   - **플랫폼 레벨**: 외부 출금 시 서비스 수수료 부과 (1 USDT 등)
   - **내부 거래**: DB상 이동만, 수수료 없음

3. **현재 시스템**: 이미 올바르게 구현됨
   - FeeConfig 모델: 플랫폼 서비스 수수료용 (정상)
   - Fee Service: 외부 출금용 수수료 계산 (정상)
   - Withdrawal Service: 올바른 로직 구현됨

## 🛠️ **실제 구현 계획 (수정된 방향)**

### Phase 1: Energy Pool 모니터링 추가 (1주)
#### 현재 시스템 유지하되 관리 기능 보강
- [ ] `app/models/fee_config.py` 삭제
- [ ] `app/services/fee_service.py` 삭제  
- [ ] `app/templates/admin/fees.html` 삭제
- [ ] `alembic/versions/*fee_config*.py` 마이그레이션 롤백
- [ ] 관련 API 엔드포인트 제거

#### 새로운 모델 구현
- [ ] `EnergyPool` 모델 구현
- [ ] `EnergyUsageLog` 모델 구현  
- [ ] `EnergyPriceHistory` 모델 구현
- [ ] Alembic 마이그레이션 생성

### Phase 2: 코어 서비스 구현 (2-3주)
- [ ] `EnergyPoolService` 구현
  - [ ] TRX 프리징/언프리징 기능
  - [ ] 에너지 풀 상태 관리
  - [ ] 자동 충전 로직
- [ ] `EnergyUsageTracker` 구현
  - [ ] 실시간 에너지 사용량 추적
  - [ ] 사용자별 통계
- [ ] `TronEnergyAPI` 구현
  - [ ] TRON 네트워크 실시간 연동
  - [ ] 에너지 가격 조회
  - [ ] 트랜잭션 스폰서십

### Phase 3: 관리자 대시보드 UI (2-3주)
- [ ] 메인 대시보드 (에너지 풀 현황)
- [ ] 에너지 풀 관리 페이지
- [ ] 실시간 에너지 사용량 모니터링
- [ ] 에너지 사용 리포트 및 통계
- [ ] 알림 및 경고 시스템

### Phase 4: 자동화 및 최적화 (1-2주)
- [ ] 에너지 모니터링 스케줄러
- [ ] 자동 충전 시스템
- [ ] 실시간 가격 모니터링
- [ ] 성능 최적화 및 테스트

## 🎯 **다음 단계 (즉시 시작 가능)**

### 1️⃣ **기존 잘못된 구현 제거**
```bash
# 삭제 대상 파일들
app/models/fee_config.py
app/services/fee_service.py  
app/templates/admin/fees.html
alembic/versions/*fee_config*.py
```

### 2️⃣ **새로운 모델 구현 시작**
- `app/models/energy_pool.py` 생성
- `app/models/energy_usage_log.py` 생성
- `app/models/energy_price_history.py` 생성

### 3️⃣ **TRON 에너지 API 확장**
- 기존 `TronService` 클래스에 에너지 관련 메서드 추가
- 에너지 가격, 사용량 조회 기능 구현

## 📚 **참고 문서**
- 📄 **ADMIN_DASHBOARD_DESIGN.md** - 완전한 설계 문서
- 📄 기존 TRON 관련 문서들 (copilot-doc-6.md, copilot-doc-9.md 등)

## ⚠️ **주의사항**
- **기존 수수료 시스템을 완전히 제거 후 새 시스템 구현**
- **TRON 테스트넷(Nile)에서 개발 및 테스트**
- **실제 에너지 비용과 스폰서십 로직 정확히 구현**

---

**✅ 설계 완료 - 구현 시작 준비됨**  
**📋 다음 작업: Phase 1 기존 시스템 제거부터 시작**
