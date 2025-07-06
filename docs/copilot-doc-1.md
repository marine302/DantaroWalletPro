# Copilot 문서 #1: DantaroWallet 개발 환경 구축

## 목표
DantaroWallet 프로젝트의 개발 환경을 완벽하게 구축합니다.

## 상세 지시사항

### 1. 프로젝트 디렉토리 및 구조 생성

다음과 같은 디렉토리 구조를 생성해주세요:

```
dantarowallet/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           └── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── schemas/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_health.py
├── docs/
│   ├── specifications/
│   └── api/
├── scripts/
│   ├── __init__.py
│   └── init_db.py
├── alembic/
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── docker-compose.yml
└── Makefile
```

### 2. Poetry 프로젝트 초기화

`pyproject.toml` 파일을 다음 내용으로 생성:

```toml
[tool.poetry]
name = "dantarowallet"
version = "0.1.0"
description = "Hybrid USDT wallet system with multi-tenant support"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"
alembic = "^1.12.1"
pydantic = {extras = ["email"], version = "^2.5.0"}
pydantic-settings = "^2.0.3"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
redis = "^5.0.1"
httpx = "^0.25.2"
tronpy = "^0.4.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
black = "^23.11.0"
flake8 = "^6.1.0"
mypy = "^1.7.1"
pre-commit = "^3.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

### 3. 환경 변수 템플릿 (.env.example)

```env
# Application
APP_NAME=DantaroWallet
APP_VERSION=0.1.0
DEBUG=True
API_V1_PREFIX=/api/v1

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/dantarowallet
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://localhost:6379/0

# TRON
TRON_NETWORK=nile  # nile for testnet, mainnet for production
TRON_API_KEY=your-trongrid-api-key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### 4. Git 설정 (.gitignore)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
ENV/
.env
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Project specific
/data/
/backups/
```

### 5. Docker Compose 설정

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dantarowallet
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/dantarowallet
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
```

### 6. Makefile 생성

```makefile
.PHONY: help install dev test lint format clean

help:
	@echo "Available commands:"
	@echo "  install    Install dependencies"
	@echo "  dev        Run development server"
	@echo "  test       Run tests"
	@echo "  lint       Run linters"
	@echo "  format     Format code"
	@echo "  clean      Clean up"

install:
	poetry install

dev:
	docker-compose up -d postgres redis
	poetry run uvicorn app.main:app --reload

test:
	poetry run pytest -v --cov=app

lint:
	poetry run flake8 app tests
	poetry run mypy app

format:
	poetry run black app tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v
```

### 7. 기본 FastAPI 앱 (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.on_event("startup")
async def startup_event():
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")
```

### 8. 설정 관리 (app/core/config.py)

```python
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DantaroWallet"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0
    
    # Redis
    REDIS_URL: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 9. README.md

```markdown
# DantaroWallet

Hybrid USDT wallet system with multi-tenant support.

## Quick Start

1. Install dependencies:
   ```bash
   make install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start development server:
   ```bash
   make dev
   ```

4. Check health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

## Development

- Run tests: `make test`
- Format code: `make format`
- Run linters: `make lint`

## Architecture

See `/docs/specifications/` for detailed architecture documents.
```

### 10. 첫 번째 테스트 (tests/test_health.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

## 실행 방법

1. 위의 모든 파일을 생성한 후
2. `poetry install` 실행
3. `docker-compose up -d postgres redis` 실행
4. `poetry run uvicorn app.main:app --reload` 실행
5. http://localhost:8000/health 접속하여 확인

## 검증 포인트

- [ ] 모든 디렉토리가 올바르게 생성되었는가?
- [ ] Poetry 의존성이 정상 설치되는가?
- [ ] Docker 컨테이너가 정상 실행되는가?
- [ ] Health 엔드포인트가 정상 응답하는가?
- [ ] 테스트가 통과하는가?

이 문서의 모든 지시사항을 완료하면, DantaroWallet의 기본 개발 환경이 구축됩니다.