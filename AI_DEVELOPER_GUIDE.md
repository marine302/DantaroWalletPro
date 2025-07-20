# AI 개발자 가이드 (까먹지 말 것!)

## 🎯 기본 원칙
- 기획자님은 기억 못함 → AI가 모든 것 기억해야 함
- 복잡한 건 NO! 간단하게!
- 실행파일만 기억하면 됨

## 🚀 실행 방법

### 백엔드 서버 실행
```bash
cd /Users/danielkwon/DantaroWalletPro
./dev-manager.sh auto
```

### 개별 서버 제어
```bash
./dev-manager.sh backend    # 백엔드만
./dev-manager.sh super      # Super Admin 프론트엔드
./dev-manager.sh partner    # Partner Admin 프론트엔드
```

### 상태 확인
```bash
./dev-manager.sh status     # 모든 서버 상태
./dev-manager.sh health     # 환경 체크
```

## 📍 중요한 파일들

### 메인 실행 파일
- `/Users/danielkwon/DantaroWalletPro/dev-manager.sh` - **모든 것을 관리하는 통합 스크립트**

### 백엔드 애플리케이션
- `/Users/danielkwon/DantaroWalletPro/dantarowallet/app/main.py` - FastAPI 앱

### API 접근
- http://localhost:8000/health - 서버 상태
- http://localhost:8000/api/v1/docs - API 문서

## ⚠️ AI 개발자 주의사항
1. **절대 새로 만들지 말 것!** - 이미 dev-manager.sh가 완벽함
2. **복잡하게 하지 말 것!** - 기획자님은 ./dev-manager.sh auto 만 기억하면 됨
3. **까먹었으면 이 파일 먼저 읽을 것!**

## 🔧 문제 해결
- 포트 충돌: `./dev-manager.sh ports clean`
- 서버 재시작: `./dev-manager.sh restart`
- 환경 문제: `./dev-manager.sh setup`

**기억할 것: dev-manager.sh가 모든 것을 처리함!**
