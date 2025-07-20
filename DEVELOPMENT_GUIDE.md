# 🚀 DantaroWallet - 완전 자동화 개발 환경 가이드

## 📋 기획자님을 위한 원클릭 개발 환경

**이 문서는 AI 개발자가 까먹지 않도록 작성된 영구 가이드입니다.**

---

## 🎯 핵심 철학
- **기획자는 기술적 세부사항을 기억할 필요 없음**
- **모든 것은 자동화되어야 함**
- **한 번의 명령어로 모든 것이 동작해야 함**
- **에러가 나면 자동으로 해결되어야 함**

---

## 💎 마스터 명령어 (기획자님 전용)

### 🚀 완전 자동화 실행
```bash
./dev-manager.sh auto
```
**이것 하나면 끝!** 환경 설정부터 서버 시작까지 모든 것을 자동 처리

### 📊 현재 상태 확인
```bash
./dev-manager.sh status
```

### 🔄 모든 서버 재시작
```bash
./dev-manager.sh restart
```

### 🛑 모든 서버 중지
```bash
./dev-manager.sh stop
```

---

## 🎮 접속 URL (북마크 해두세요!)

- **🔧 백엔드 API 문서**: http://localhost:8000/api/v1/docs
- **❤️ 서버 상태 확인**: http://localhost:8000/health
- **👑 Super Admin**: http://localhost:3020 (개발 예정)
- **🤝 Partner Admin**: http://localhost:3030 (개발 예정)

---

## 🆘 문제 해결 (원클릭)

### 포트 충돌/서버 안됨
```bash
./dev-manager.sh ports clean
```

### 환경 문제/패키지 오류
```bash
./dev-manager.sh setup
```

### 완전 초기화 (마지막 수단)
```bash
./dev-manager.sh clean
./dev-manager.sh setup
./dev-manager.sh auto
```

---

## 🤖 AI 개발자를 위한 불변 규칙

### ⚠️ 절대 하지 말 것
1. **기존 dev-manager.sh 구조 변경 금지**
2. **새로운 복잡한 스크립트 만들기 금지**
3. **기획자에게 터미널 명령어 여러 개 요구 금지**
4. **환경 설정을 수동으로 하라고 안내 금지**

### ✅ 반드시 지킬 것
1. **모든 기능은 dev-manager.sh에 통합**
2. **에러 발생 시 자동 복구 로직 포함**
3. **상태 체크 우선, 중복 실행 방지**
4. **사용자 친화적 메시지와 이모지 사용**
5. **이 문서 업데이트 후 커밋**

---

## 📂 프로젝트 구조 (변경 금지)

```
DantaroWalletPro/
├── 🔧 dev-manager.sh          # 마스터 컨트롤러 (모든 기능)
├── 📋 DEVELOPMENT_GUIDE.md    # 이 문서 (영구 가이드)
├── 📋 DEVELOPMENT_LOG.md      # 개발 이력
├── 📋 README.md               # 프로젝트 소개
├── 📁 dantarowallet/          # 백엔드
│   ├── 🐍 run.py              # 백엔드 전용 실행기
│   ├── 🚀 app/main.py         # FastAPI 앱
│   └── ...
└── 📁 frontend/               # 프론트엔드 (개발 예정)
```

---

## 🔄 개발 플로우 (AI 개발자용)

### 1. 환경 진단
```bash
./dev-manager.sh health
```

### 2. 자동 실행
```bash
./dev-manager.sh auto
```

### 3. 상태 확인
```bash
./dev-manager.sh status
curl http://localhost:8000/health
```

### 4. API 문서 확인
- 브라우저: http://localhost:8000/api/v1/docs
- curl: `curl http://localhost:8000/api/v1/openapi.json`

---

## 🎯 성공 기준

### ✅ 백엔드 완료 체크리스트
- [ ] `./dev-manager.sh auto` 실행 성공
- [ ] `curl http://localhost:8000/health` 응답 OK
- [ ] `http://localhost:8000/api/v1/docs` 브라우저 접속 OK
- [ ] API 엔드포인트 목록 확인 OK
- [ ] 포트 충돌 없음
- [ ] 가상환경 자동 설정 OK

### ✅ 프론트엔드 준비 체크리스트 (향후)
- [ ] Super Admin 포트 3020 준비
- [ ] Partner Admin 포트 3030 준비
- [ ] 프론트엔드 자동 실행 기능

---

## 🚨 AI 개발자 경고사항

### 기획자님이 이런 말씀하시면...

**"서버가 안돼요"** → `./dev-manager.sh auto`
**"포트 오류 나요"** → `./dev-manager.sh ports clean`
**"환경 설정 안돼요"** → `./dev-manager.sh setup`
**"다 초기화하고 싶어요"** → `./dev-manager.sh clean && ./dev-manager.sh auto`

### 절대 이렇게 답변하지 마세요
- ❌ "터미널에서 cd 명령어로..."
- ❌ "가상환경을 먼저 활성화하고..."
- ❌ "pip install을 실행해서..."
- ❌ "포트를 직접 확인해보세요..."

### 항상 이렇게 답변하세요
- ✅ "dev-manager.sh auto 실행해주세요!"
- ✅ "자동으로 해결해드릴게요!"
- ✅ "원클릭으로 처리 가능합니다!"

---

## 💾 이 문서의 중요성

**이 문서는 AI 개발자의 기억을 대신하는 영구 가이드입니다.**

- 매번 새로운 세션에서 이 문서를 먼저 읽으세요
- 기획자님의 요청은 항상 이 가이드에 따라 처리하세요
- 새로운 기능 추가 시 이 문서를 업데이트하세요
- 모든 변경사항은 git에 커밋하세요

---

## 📞 응급 연락망 (농담)

- **서버 안될 때**: `./dev-manager.sh auto`
- **포트 문제**: `./dev-manager.sh ports clean`
- **모든 게 이상할 때**: `./dev-manager.sh restart`
- **AI가 또 까먹었을 때**: 이 문서 다시 읽기

---

**🎯 목표: 기획자님이 기술적 세부사항을 전혀 몰라도 개발 환경을 완벽하게 관리할 수 있도록!**
