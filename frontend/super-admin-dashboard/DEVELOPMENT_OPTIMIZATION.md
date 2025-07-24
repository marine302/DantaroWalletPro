# 개발 환경 최적화 가이드

## 빌드 성능 문제 해결

### 1. Next.js 설정 최적화
- `next.config.ts`를 단순화하여 빌드 시간 단축
- 복잡한 webpack 설정 제거
- 불필요한 optimization 제거

### 2. TypeScript 설정 최적화
- `strict: false`로 설정하여 빠른 개발
- `skipLibCheck: true`로 라이브러리 체크 생략
- 증분 컴파일 활성화

### 3. 빠른 개발 명령어
```bash
# 빠른 개발 서버 시작 (백엔드 없이)
npm run dev-quick

# 빠른 빌드 (개발 모드)
npm run build-fast

# 캐시 클리어 후 시작
./quick-dev.sh
```

### 4. 성능 최적화 팁
- `.next` 폴더 정기적 삭제
- `node_modules/.cache` 정리
- 불필요한 프로세스 종료

### 5. 일반적인 문제 해결
- 포트 충돌: `lsof -ti:3000 | xargs kill -9`
- 메모리 부족: `export NODE_OPTIONS="--max-old-space-size=4096"`
- 빌드 멈춤: Ctrl+C 후 캐시 클리어

### 6. 권장 개발 워크플로우
1. `./quick-dev.sh` 사용하여 빠른 시작
2. 코드 변경 후 Hot Reload 활용
3. 필요시에만 전체 빌드 실행
4. TypeScript 에러는 개발 중에는 무시하고 완료 후 수정

## 현재 적용된 최적화
- Next.js 설정 단순화 완료
- package.json에 빠른 개발 스크립트 추가
- quick-dev.sh 스크립트 생성
