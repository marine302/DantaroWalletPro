# 전체 API 구조 불일치 분석 보고서

## 🚨 발견된 주요 구조 불일치들

### 1. **인증 API 구조 불일치**

#### 백엔드 (FastAPI)
```python
@router.post("/login", response_model=Token)
# Token 스키마:
class Token(BaseModel):
    access_token: str
    refresh_token: str  
    token_type: str = "bearer"
    expires_in: int
```

#### 프론트엔드 (TypeScript)
```typescript
// AuthResponse 인터페이스:
interface AuthResponse {
  access_token: string;  // ✅ 일치
  // ❌ refresh_token 누락
  // ❌ token_type 누락  
  // ❌ expires_in 누락
}
```

#### Mock 서버
```javascript
// 현재 Mock 응답:
{
  success: true,
  token: 'mock-jwt-token-' + Date.now(),  // ❌ 구조 완전히 다름
  user: { ... }
}
```

### 2. **Dashboard API 구조 불일치**

#### 백엔드 확인 필요:
- `/admin/dashboard/stats` 
- `/admin/system/health`

#### 현재 Mock 서버:
```javascript
// 직접 데이터 반환 (래퍼 없음)
res.json(generateDashboardStats());
```

### 3. **Partners API 구조 불일치**

#### 프론트엔드에서 사용:
- `GET /partners/` (페이지네이션)
- `POST /admin/partners`
- `PUT /admin/partners/{id}`

#### Mock 서버:
- 일부만 구현됨
- 백엔드와 응답 구조 다름

### 4. **Energy Management API**

#### 프론트엔드에서 사용하지만 Mock 없음:
- `GET /admin/energy/pool`
- `POST /admin/energy/recharge`
- `POST /admin/energy/allocate`
- `GET /admin/energy/transactions`

### 5. **Fee Management API**

#### 프론트엔드에서 사용하지만 Mock 없음:
- `GET /admin/fees/configs`
- `POST /admin/fees/configs`
- `PUT /admin/fees/configs/{id}`
- `DELETE /admin/fees/configs/{id}`
- `GET /admin/fees/revenue`

### 6. **System Admins API**

#### 프론트엔드에서 사용하지만 Mock 불완전:
- `GET /admin/system/admins`
- `POST /admin/system/admins`
- `PUT /admin/system/admins/{id}`
- `DELETE /admin/system/admins/{id}`

## 🔥 **심각성 평가**

### 🚨 **즉시 수정 필요 (Critical)**
1. **인증 API**: 완전히 다른 구조
2. **Energy Management**: Mock 완전 누락
3. **Fee Management**: Mock 완전 누락

### ⚠️ **수정 필요 (High)**
1. **Dashboard API**: 래퍼 구조 불일치
2. **Partners API**: 부분적 불일치
3. **System Admins**: 부분적 구현

### ⚡ **개선 필요 (Medium)**
1. **External Energy**: 이미 수정 완료 ✅
2. **Analytics**: 구조 확인 필요

## 📋 **해결 계획**

### Phase 1: Critical API 수정
1. 인증 API 백엔드 스키마 정확히 맞추기
2. Energy Management Mock API 추가
3. Fee Management Mock API 추가

### Phase 2: High Priority API 수정  
1. Dashboard API 래퍼 구조 통일
2. Partners API 완전 구현
3. System Admins API 완전 구현

### Phase 3: 전체 검증
1. 모든 API 엔드포인트 백엔드와 동기화 확인
2. TypeScript 타입 정의 백엔드 스키마와 100% 일치
3. 자동화된 구조 검증 도구 구축

이제 이 문제들을 하나씩 체계적으로 해결해나가겠습니다.
