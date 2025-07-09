# Copilot 문서 #11: 웹 기반 관리자 대시보드

## 목표
FastAPI + Jinja2 템플릿을 사용하여 웹 기반 관리자 패널을 구축합니다. 사용자 관리, 트랜잭션 조회, 시스템 모니터링, 긴급 정지 기능을 포함합니다.

## 전제 조건
- Copilot 문서 #1-10이 완료되어 있어야 합니다.
- 관리자 계정이 생성되어 있어야 합니다.
- Jinja2가 설치되어 있어야 합니다.

## 상세 지시사항

### 1. 관리자 인증 미들웨어 (app/middleware/admin_auth.py)

```python
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from app.core.config import settings
from app.core.security import verify_token

class AdminAuthMiddleware(BaseHTTPMiddleware):
    """관리자 페이지 인증 미들웨어"""
    
    def __init__(self, app, admin_paths: list):
        super().__init__(app)
        self.admin_paths = admin_paths
    
    async def dispatch(self, request: Request, call_next):
        # 관리자 경로인지 확인
        if not any(request.url.path.startswith(path) for path in self.admin_paths):
            return await call_next(request)
        
        # 로그인 페이지는 제외
        if request.url.path.endswith("/login"):
            return await call_next(request)
        
        # 쿠키에서 토큰 확인
        token = request.cookies.get("admin_token")
        if not token:
            return RedirectResponse(url="/admin/login", status_code=302)
        
        # 토큰 검증
        payload = verify_token(token)
        if not payload:
            return RedirectResponse(url="/admin/login", status_code=302)
        
        # request에 사용자 정보 추가
        request.state.admin_id = payload.get("sub")
        request.state.is_admin = True
        
        response = await call_next(request)
        return response
```

### 2. 관리자 대시보드 라우터 (app/api/v1/endpoints/admin_dashboard.py)

```python
from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionStatus
from app.models.deposit import Deposit, DepositStatus
from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.models.wallet import Wallet
from app.services.alert_service import alert_service, AlertLevel

router = APIRouter()
templates = Jinja2Templates(directory="app/templates/admin")

# 관리자 인증 헬퍼
async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """현재 관리자 사용자 가져오기"""
    admin_id = getattr(request.state, "admin_id", None)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.execute(
        select(User).filter(User.id == int(admin_id))
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin")
    
    return admin

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """관리자 로그인 페이지"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """관리자 로그인 처리"""
    # 사용자 확인
    result = await db.execute(
        select(User).filter(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"}
        )
    
    if not user.is_admin:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Admin access required"}
        )
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # 대시보드로 리다이렉트
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    return response

@router.get("/logout")
async def admin_logout():
    """관리자 로그아웃"""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """관리자 대시보드 메인"""
    # 통계 수집
    stats = await get_dashboard_stats(db)
    
    # 최근 활동
    recent_activities = await get_recent_activities(db)
    
    # 시스템 상태
    from app.services.health_service import HealthService
    health_service = HealthService()
    health_status = await health_service.get_health_status()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "activities": recent_activities,
            "health": health_status
        }
    )

@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    search: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """사용자 관리 페이지"""
    # 쿼리 생성
    query = select(User)
    
    if search:
        query = query.filter(
            or_(
                User.email.contains(search),
                User.tron_address.contains(search)
            )
        )
    
    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "inactive":
        query = query.filter(User.is_active == False)
    
    # 페이지네이션
    per_page = 20
    offset = (page - 1) * per_page
    
    # 전체 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 사용자 목록
    query = query.order_by(User.created_at.desc())
    query = query.limit(per_page).offset(offset)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 각 사용자의 잔고 정보 가져오기
    user_data = []
    for user in users:
        balance_result = await db.execute(
            select(Balance).filter(Balance.user_id == user.id)
        )
        balance = balance_result.scalar_one_or_none()
        
        user_data.append({
            "user": user,
            "balance": balance
        })
    
    # 페이지 정보
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "admin": admin,
            "users": user_data,
            "search": search,
            "status": status,
            "page": page,
            "total_pages": total_pages,
            "total": total
        }
    )

@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """사용자 상태 토글"""
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    await db.commit()
    
    # 로그 기록
    action = "activated" if user.is_active else "deactivated"
    logger.info(f"User {user_id} {action} by admin {admin.id}")
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.get("/transactions", response_class=HTMLResponse)
async def admin_transactions(
    request: Request,
    tx_type: str = Query(None),
    status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """트랜잭션 관리 페이지"""
    query = select(Transaction).join(User)
    
    # 필터링
    if tx_type:
        query = query.filter(Transaction.type == tx_type)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    if date_from:
        query = query.filter(Transaction.created_at >= datetime.fromisoformat(date_from))
    
    if date_to:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(date_to))
    
    # 페이지네이션
    per_page = 50
    offset = (page - 1) * per_page
    
    # 전체 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 트랜잭션 목록
    query = query.order_by(Transaction.created_at.desc())
    query = query.limit(per_page).offset(offset)
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # 사용자 정보 포함
    tx_data = []
    for tx in transactions:
        user_result = await db.execute(
            select(User).filter(User.id == tx.user_id)
        )
        user = user_result.scalar_one()
        
        tx_data.append({
            "transaction": tx,
            "user": user
        })
    
    # 페이지 정보
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "admin": admin,
            "transactions": tx_data,
            "tx_type": tx_type,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
            "page": page,
            "total_pages": total_pages,
            "total": total
        }
    )

@router.get("/withdrawals", response_class=HTMLResponse)
async def admin_withdrawals(
    request: Request,
    status: str = Query("pending"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """출금 관리 페이지"""
    query = select(Withdrawal).join(User)
    
    if status and status != "all":
        query = query.filter(Withdrawal.status == status)
    
    query = query.order_by(Withdrawal.priority.desc(), Withdrawal.requested_at.asc())
    
    result = await db.execute(query)
    withdrawals = result.scalars().all()
    
    # 사용자 정보 포함
    withdrawal_data = []
    for w in withdrawals:
        user_result = await db.execute(
            select(User).filter(User.id == w.user_id)
        )
        user = user_result.scalar_one()
        
        withdrawal_data.append({
            "withdrawal": w,
            "user": user
        })
    
    return templates.TemplateResponse(
        "withdrawals.html",
        {
            "request": request,
            "admin": admin,
            "withdrawals": withdrawal_data,
            "current_status": status
        }
    )

@router.get("/system", response_class=HTMLResponse)
async def admin_system(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """시스템 관리 페이지"""
    # 시스템 설정 가져오기
    from app.middleware.metrics import metrics_collector
    metrics = metrics_collector.get_metrics()
    
    # 백그라운드 태스크 상태
    from app.core.background import background_tasks
    task_status = []
    for task in background_tasks.tasks:
        task_status.append({
            "name": task.get_name(),
            "done": task.done(),
            "cancelled": task.cancelled()
        })
    
    return templates.TemplateResponse(
        "system.html",
        {
            "request": request,
            "admin": admin,
            "metrics": metrics,
            "task_status": task_status,
            "emergency_stop_enabled": getattr(settings, "EMERGENCY_STOP", False)
        }
    )

@router.post("/emergency-stop")
async def emergency_stop(
    action: str = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """긴급 정지/해제"""
    if action == "enable":
        settings.EMERGENCY_STOP = True
        message = "Emergency stop ENABLED"
        level = AlertLevel.CRITICAL
    else:
        settings.EMERGENCY_STOP = False
        message = "Emergency stop DISABLED"
        level = AlertLevel.INFO
    
    # 알림 전송
    await alert_service.send_alert(
        "Emergency Stop",
        f"{message} by admin {admin.email}",
        level,
        "emergency_stop"
    )
    
    logger.warning(f"Emergency stop {action}d by admin {admin.id}")
    
    return RedirectResponse(url="/admin/system", status_code=302)

# 헬퍼 함수들

async def get_dashboard_stats(db: AsyncSession) -> dict:
    """대시보드 통계 수집"""
    # 사용자 통계
    total_users = await db.execute(select(func.count(User.id)))
    total_users = total_users.scalar()
    
    active_users = await db.execute(
        select(func.count(User.id)).filter(User.is_active == True)
    )
    active_users = active_users.scalar()
    
    # 잔고 통계
    total_balance = await db.execute(
        select(func.sum(Balance.amount))
    )
    total_balance = total_balance.scalar() or 0
    
    # 오늘 통계
    today = datetime.utcnow().date()
    
    today_deposits = await db.execute(
        select(func.count(Deposit.id), func.sum(Deposit.amount))
        .filter(Deposit.created_at >= today)
    )
    deposit_count, deposit_amount = today_deposits.one()
    
    today_withdrawals = await db.execute(
        select(func.count(Withdrawal.id), func.sum(Withdrawal.amount))
        .filter(Withdrawal.requested_at >= today)
    )
    withdrawal_count, withdrawal_amount = today_withdrawals.one()
    
    # 대기 중인 출금
    pending_withdrawals = await db.execute(
        select(func.count(Withdrawal.id))
        .filter(Withdrawal.status == WithdrawalStatus.PENDING)
    )
    pending_count = pending_withdrawals.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_balance": float(total_balance),
        "today_deposits": {
            "count": deposit_count or 0,
            "amount": float(deposit_amount or 0)
        },
        "today_withdrawals": {
            "count": withdrawal_count or 0,
            "amount": float(withdrawal_amount or 0)
        },
        "pending_withdrawals": pending_count
    }

async def get_recent_activities(db: AsyncSession, limit: int = 10) -> list:
    """최근 활동 조회"""
    activities = []
    
    # 최근 가입
    recent_users = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(5)
    )
    for user in recent_users.scalars():
        activities.append({
            "type": "signup",
            "user": user.email,
            "time": user.created_at,
            "details": "New user registration"
        })
    
    # 최근 입금
    recent_deposits = await db.execute(
        select(Deposit)
        .filter(Deposit.status == DepositStatus.CREDITED)
        .order_by(Deposit.created_at.desc())
        .limit(5)
    )
    for deposit in recent_deposits.scalars():
        activities.append({
            "type": "deposit",
            "amount": float(deposit.amount),
            "time": deposit.created_at,
            "details": f"Deposit credited"
        })
    
    # 최근 출금
    recent_withdrawals = await db.execute(
        select(Withdrawal)
        .filter(Withdrawal.status == WithdrawalStatus.COMPLETED)
        .order_by(Withdrawal.completed_at.desc())
        .limit(5)
    )
    for withdrawal in recent_withdrawals.scalars():
        activities.append({
            "type": "withdrawal",
            "amount": float(withdrawal.amount),
            "time": withdrawal.completed_at,
            "details": f"Withdrawal completed"
        })
    
    # 시간순 정렬
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:limit]
```

### 3. 관리자 템플릿 - 베이스 레이아웃 (app/templates/admin/base.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DantaroWallet Admin{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.5rem;
        }
        
        .nav {
            background: #34495e;
            padding: 0 2rem;
        }
        
        .nav ul {
            list-style: none;
            display: flex;
        }
        
        .nav a {
            color: white;
            text-decoration: none;
            padding: 1rem 1.5rem;
            display: block;
            transition: background 0.3s;
        }
        
        .nav a:hover, .nav a.active {
            background: #2c3e50;
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .stat-label {
            color: #7f8c8d;
            margin-top: 0.5rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            text-align: left;
            padding: 1rem;
            border-bottom: 1px solid #ecf0f1;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .btn {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #2980b9;
        }
        
        .btn-small {
            padding: 0.25rem 0.75rem;
            font-size: 0.85rem;
        }
        
        .btn-danger {
            background: #e74c3c;
        }
        
        .btn-danger:hover {
            background: #c0392b;
        }
        
        .btn-success {
            background: #27ae60;
        }
        
        .btn-success:hover {
            background: #229954;
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-active { background: #d4edda; color: #155724; }
        .status-pending { background: #fff3cd; color: #856404; }
        .status-completed { background: #d1ecf1; color: #0c5460; }
        .status-failed { background: #f8d7da; color: #721c24; }
        
        .alert {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .search-box {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .search-box input, .search-box select {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        
        .search-box input {
            flex: 1;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 2rem;
        }
        
        .pagination a {
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid #ddd;
            text-decoration: none;
            color: #333;
            border-radius: 4px;
        }
        
        .pagination a.active {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header class="header">
        <h1>DantaroWallet Admin</h1>
        <div>
            <span>{{ admin.email }}</span> |
            <a href="/admin/logout" style="color: white;">Logout</a>
        </div>
    </header>
    
    <nav class="nav">
        <ul>
            <li><a href="/admin/dashboard" {% if request.url.path == '/admin/dashboard' %}class="active"{% endif %}>Dashboard</a></li>
            <li><a href="/admin/users" {% if request.url.path == '/admin/users' %}class="active"{% endif %}>Users</a></li>
            <li><a href="/admin/transactions" {% if request.url.path == '/admin/transactions' %}class="active"{% endif %}>Transactions</a></li>
            <li><a href="/admin/withdrawals" {% if request.url.path == '/admin/withdrawals' %}class="active"{% endif %}>Withdrawals</a></li>
            <li><a href="/admin/system" {% if request.url.path == '/admin/system' %}class="active"{% endif %}>System</a></li>
        </ul>
    </nav>
    
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 4. 관리자 템플릿 - 로그인 (app/templates/admin/login.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - DantaroWallet</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        
        .login-container {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        
        h2 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #555;
            font-weight: 500;
        }
        
        input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        
        input:focus {
            outline: none;
            border-color: #3498db;
        }
        
        button {
            width: 100%;
            padding: 0.75rem;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #2980b9;
        }
        
        .error {
            color: #e74c3c;
            text-align: center;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>DantaroWallet Admin</h2>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="post" action="/admin/login">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
```

### 5. 관리자 템플릿 - 대시보드 (app/templates/admin/dashboard.html)

```html
{% extends "admin/base.html" %}

{% block title %}Dashboard - DantaroWallet Admin{% endblock %}

{% block content %}
<h2>Dashboard</h2>

<!-- 통계 카드 -->
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">{{ stats.total_users }}</div>
        <div class="stat-label">Total Users</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">{{ stats.active_users }}</div>
        <div class="stat-label">Active Users</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">${{ "%.2f"|format(stats.total_balance) }}</div>
        <div class="stat-label">Total Balance</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">{{ stats.pending_withdrawals }}</div>
        <div class="stat-label">Pending Withdrawals</div>
    </div>
</div>

<!-- 오늘의 활동 -->
<div class="card">
    <h3>Today's Activity</h3>
    <div class="stats-grid" style="margin-top: 1rem;">
        <div>
            <strong>Deposits:</strong> {{ stats.today_deposits.count }} 
            (${{"%.2f"|format(stats.today_deposits.amount)}})
        </div>
        <div>
            <strong>Withdrawals:</strong> {{ stats.today_withdrawals.count }}
            (${{"%.2f"|format(stats.today_withdrawals.amount)}})
        </div>
    </div>
</div>

<!-- 시스템 상태 -->
<div class="card">
    <h3>System Health</h3>
    <div style="margin-top: 1rem;">
        <strong>Overall Status:</strong> 
        <span class="status-badge status-{{ health.status }}">{{ health.status|upper }}</span>
    </div>
    
    <table style="margin-top: 1rem;">
        <thead>
            <tr>
                <th>Component</th>
                <th>Status</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
            {% for name, check in health.checks.items() %}
            <tr>
                <td>{{ name|title }}</td>
                <td>
                    <span class="status-badge status-{{ check.status }}">
                        {{ check.status|upper }}
                    </span>
                </td>
                <td>{{ check.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- 최근 활동 -->
<div class="card">
    <h3>Recent Activities</h3>
    <table>
        <thead>
            <tr>
                <th>Type</th>
                <th>Details</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody>
            {% for activity in activities %}
            <tr>
                <td>
                    <span class="status-badge status-{{ activity.type }}">
                        {{ activity.type|upper }}
                    </span>
                </td>
                <td>{{ activity.details }}</td>
                <td>{{ activity.time.strftime('%Y-%m-%d %H:%M:%S') }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

### 6. 관리자 템플릿 - 사용자 관리 (app/templates/admin/users.html)

```html
{% extends "admin/base.html" %}

{% block title %}Users - DantaroWallet Admin{% endblock %}

{% block content %}
<h2>User Management</h2>

<!-- 검색 -->
<form class="search-box" method="get">
    <input type="text" name="search" placeholder="Search by email or address" value="{{ search or '' }}">
    <select name="status">
        <option value="">All Status</option>
        <option value="active" {% if status == 'active' %}selected{% endif %}>Active</option>
        <option value="inactive" {% if status == 'inactive' %}selected{% endif %}>Inactive</option>
    </select>
    <button type="submit" class="btn">Search</button>
</form>

<!-- 사용자 테이블 -->
<div class="card">
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Balance</th>
                <th>Status</th>
                <th>Verified</th>
                <th>Created</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for item in users %}
            <tr>
                <td>{{ item.user.id }}</td>
                <td>{{ item.user.email }}</td>
                <td>${{ "%.2f"|format(item.balance.amount if item.balance else 0) }}</td>
                <td>
                    <span class="status-badge status-{{ 'active' if item.user.is_active else 'failed' }}">
                        {{ 'Active' if item.user.is_active else 'Inactive' }}
                    </span>
                </td>
                <td>{{ '✓' if item.user.is_verified else '✗' }}</td>
                <td>{{ item.user.created_at.strftime('%Y-%m-%d') }}</td>
                <td>
                    <form method="post" action="/admin/users/{{ item.user.id }}/toggle-status" style="display: inline;">
                        <button type="submit" class="btn btn-small {% if item.user.is_active %}btn-danger{% else %}btn-success{% endif %}">
                            {{ 'Deactivate' if item.user.is_active else 'Activate' }}
                        </button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- 페이지네이션 -->
<div class="pagination">
    {% if page > 1 %}
    <a href="?page={{ page - 1 }}&search={{ search or '' }}&status={{ status or '' }}">Previous</a>
    {% endif %}
    
    {% for p in range(1, total_pages + 1) %}
        {% if p == page %}
        <a href="#" class="active">{{ p }}</a>
        {% else %}
        <a href="?page={{ p }}&search={{ search or '' }}&status={{ status or '' }}">{{ p }}</a>
        {% endif %}
    {% endfor %}
    
    {% if page < total_pages %}
    <a href="?page={{ page + 1 }}&search={{ search or '' }}&status={{ status or '' }}">Next</a>
    {% endif %}
</div>
{% endblock %}
```

### 7. 관리자 템플릿 - 출금 관리 (app/templates/admin/withdrawals.html)

```html
{% extends "admin/base.html" %}

{% block title %}Withdrawals - DantaroWallet Admin{% endblock %}

{% block content %}
<h2>Withdrawal Management</h2>

<!-- 상태 필터 -->
<div class="search-box">
    <select onchange="window.location.href='?status=' + this.value">
        <option value="all" {% if current_status == 'all' %}selected{% endif %}>All Status</option>
        <option value="pending" {% if current_status == 'pending' %}selected{% endif %}>Pending</option>
        <option value="approved" {% if current_status == 'approved' %}selected{% endif %}>Approved</option>
        <option value="processing" {% if current_status == 'processing' %}selected{% endif %}>Processing</option>
        <option value="completed" {% if current_status == 'completed' %}selected{% endif %}>Completed</option>
        <option value="rejected" {% if current_status == 'rejected' %}selected{% endif %}>Rejected</option>
    </select>
</div>

<!-- 출금 테이블 -->
<div class="card">
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Amount</th>
                <th>Fee</th>
                <th>To Address</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Requested</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for item in withdrawals %}
            <tr>
                <td>{{ item.withdrawal.id }}</td>
                <td>{{ item.user.email }}</td>
                <td>${{ "%.2f"|format(item.withdrawal.amount) }}</td>
                <td>${{ "%.2f"|format(item.withdrawal.fee) }}</td>
                <td title="{{ item.withdrawal.to_address }}">
                    {{ item.withdrawal.to_address[:8] }}...{{ item.withdrawal.to_address[-6:] }}
                </td>
                <td>
                    <span class="status-badge status-{{ item.withdrawal.status }}">
                        {{ item.withdrawal.status|upper }}
                    </span>
                </td>
                <td>
                    <span class="status-badge" style="background: {% if item.withdrawal.priority == 'urgent' %}#e74c3c{% elif item.withdrawal.priority == 'high' %}#f39c12{% elif item.withdrawal.priority == 'normal' %}#3498db{% else %}#95a5a6{% endif %}; color: white;">
                        {{ item.withdrawal.priority|upper }}
                    </span>
                </td>
                <td>{{ item.withdrawal.requested_at.strftime('%Y-%m-%d %H:%M') }}</td>
                <td>
                    {% if item.withdrawal.status == 'pending' %}
                    <a href="/api/v1/withdrawals/admin/{{ item.withdrawal.id }}/processing-guide" 
                       class="btn btn-small btn-success" target="_blank">Process</a>
                    {% elif item.withdrawal.status == 'processing' %}
                    <span style="color: #f39c12;">Processing...</span>
                    {% elif item.withdrawal.status == 'completed' %}
                    {% if item.withdrawal.tx_hash %}
                    <a href="https://tronscan.org/#/transaction/{{ item.withdrawal.tx_hash }}" 
                       target="_blank" class="btn btn-small">View TX</a>
                    {% endif %}
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

### 8. 관리자 템플릿 - 시스템 (app/templates/admin/system.html)

```html
{% extends "admin/base.html" %}

{% block title %}System - DantaroWallet Admin{% endblock %}

{% block content %}
<h2>System Management</h2>

<!-- 긴급 정지 -->
<div class="card">
    <h3>Emergency Controls</h3>
    <p>Emergency stop will halt all withdrawals and critical operations.</p>
    
    <form method="post" action="/admin/emergency-stop" style="margin-top: 1rem;">
        {% if emergency_stop_enabled %}
        <div class="alert alert-danger">
            ⚠️ EMERGENCY STOP IS CURRENTLY ACTIVE
        </div>
        <input type="hidden" name="action" value="disable">
        <button type="submit" class="btn btn-success">Disable Emergency Stop</button>
        {% else %}
        <input type="hidden" name="action" value="enable">
        <button type="submit" class="btn btn-danger" 
                onclick="return confirm('Are you sure? This will halt all critical operations!')">
            Enable Emergency Stop
        </button>
        {% endif %}
    </form>
</div>

<!-- 시스템 메트릭 -->
<div class="card">
    <h3>System Metrics</h3>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ metrics.cpu_percent }}%</div>
            <div class="stat-label">CPU Usage</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-value">{{ metrics.memory_percent }}%</div>
            <div class="stat-label">Memory Usage</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-value">{{ metrics.disk_percent }}%</div>
            <div class="stat-label">Disk Usage</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-value">{{ metrics.active_requests }}</div>
            <div class="stat-label">Active Requests</div>
        </div>
    </div>
    
    <table style="margin-top: 2rem;">
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Requests</td>
                <td>{{ metrics.total_requests }}</td>
            </tr>
            <tr>
                <td>Error Rate</td>
                <td>{{ metrics.error_rate }}%</td>
            </tr>
            <tr>
                <td>Avg Response Time</td>
                <td>{{ metrics.avg_response_time_ms }}ms</td>
            </tr>
            <tr>
                <td>P95 Response Time</td>
                <td>{{ metrics.p95_response_time_ms }}ms</td>
            </tr>
            <tr>
                <td>P99 Response Time</td>
                <td>{{ metrics.p99_response_time_ms }}ms</td>
            </tr>
            <tr>
                <td>Uptime</td>
                <td>{{ (metrics.uptime_seconds // 3600) }}h {{ ((metrics.uptime_seconds % 3600) // 60) }}m</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- 백그라운드 태스크 -->
<div class="card">
    <h3>Background Tasks</h3>
    
    <table>
        <thead>
            <tr>
                <th>Task Name</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for task in task_status %}
            <tr>
                <td>{{ task.name }}</td>
                <td>
                    {% if task.done %}
                        <span class="status-badge status-failed">Done</span>
                    {% elif task.cancelled %}
                        <span class="status-badge status-failed">Cancelled</span>
                    {% else %}
                        <span class="status-badge status-active">Running</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

### 9. 메인 애플리케이션 업데이트 (app/main.py)

관리자 미들웨어와 라우터 추가:

```python
# 기존 imports에 추가
from app.middleware.admin_auth import AdminAuthMiddleware
from app.api.v1.endpoints import admin_dashboard

# 미들웨어 추가 (MetricsMiddleware 다음)
app.add_middleware(
    AdminAuthMiddleware,
    admin_paths=["/admin"]
)

# 관리자 라우터 추가 (별도로)
app.include_router(
    admin_dashboard.router,
    prefix="/admin",
    tags=["admin"]
)

# 템플릿 디렉토리 생성
import os
os.makedirs("app/templates/admin", exist_ok=True)
```

### 10. 환경 변수 추가 (설정 파일)

```python
# app/core/config.py에 추가
class Settings(BaseSettings):
    # 기존 설정들...
    
    # Emergency Stop
    EMERGENCY_STOP: bool = False
    
    # 기존 설정 계속...
```

### 11. 관리자 대시보드 테스트 (tests/test_admin_dashboard.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def create_admin_user():
    """테스트용 관리자 생성"""
    async with AsyncSessionLocal() as db:
        # 관리자 생성
        admin = User(
            email="admin@test.com",
            password_hash="$2b$12$test",  # 실제로는 hash 필요
            is_admin=True,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        await db.commit()
        return admin

@pytest.mark.asyncio
async def test_admin_login_required():
    """관리자 로그인 필요 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/dashboard")
    
    assert response.status_code == 302  # 리다이렉트
    assert "/admin/login" in response.headers["location"]

@pytest.mark.asyncio
async def test_admin_dashboard_access():
    """관리자 대시보드 접근 테스트"""
    # 관리자 생성
    admin = await create_admin_user()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 로그인
        response = await client.post(
            "/admin/login",
            data={"email": "admin@test.com", "password": "testpassword"}
        )
        
        # 쿠키 확인
        assert "admin_token" in response.cookies
        
        # 대시보드 접근
        response = await client.get(
            "/admin/dashboard",
            cookies={"admin_token": response.cookies["admin_token"]}
        )
        
        assert response.status_code == 200
```

## 실행 및 검증

1. 템플릿 디렉토리 생성:
   ```bash
   mkdir -p app/templates/admin
   ```

2. 모든 템플릿 파일 생성

3. 서버 재시작:
   ```bash
   make dev
   ```

4. 관리자 계정 생성 (수동 또는 스크립트):
   ```python
   # scripts/create_admin.py
   import asyncio
   from app.core.database import AsyncSessionLocal
   from app.models.user import User
   from app.core.security import get_password_hash
   
   async def create_admin():
       async with AsyncSessionLocal() as db:
           admin = User(
               email="admin@dantarowallet.com",
               password_hash=get_password_hash("securepassword123!"),
               is_admin=True,
               is_active=True,
               is_verified=True
           )
           db.add(admin)
           await db.commit()
           print("Admin created successfully")
   
   if __name__ == "__main__":
       asyncio.run(create_admin())
   ```

5. 관리자 대시보드 접속:
   http://localhost:8000/admin/login

## 검증 포인트

- [ ] 관리자 로그인이 작동하는가?
- [ ] 로그인 후 대시보드가 표시되는가?
- [ ] 사용자 관리가 작동하는가?
- [ ] 트랜잭션 조회가 가능한가?
- [ ] 출금 관리가 작동하는가?
- [ ] 시스템 메트릭이 표시되는가?
- [ ] 긴급 정지 기능이 작동하는가?
- [ ] 로그아웃이 정상 작동하는가?

이 문서를 완료하면 웹 기반 관리자 대시보드가 구축되어 시스템을 효율적으로 관리할 수 있습니다.