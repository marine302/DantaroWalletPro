# Copilot 문서 #7: GitHub Actions CI/CD 파이프라인

## 목표
GitHub Actions를 사용하여 자동화된 CI/CD 파이프라인을 구축합니다. 코드 푸시 시 자동 테스트, Docker 이미지 빌드, 개발 서버 배포, Telegram 알림을 포함합니다.

## 전제 조건
- GitHub 저장소가 생성되어 있어야 합니다.
- Docker Hub 계정이 있어야 합니다.
- Telegram Bot Token이 준비되어 있어야 합니다.
- 개발 서버(VPS)가 준비되어 있어야 합니다.

## 상세 지시사항

### 1. GitHub Actions 워크플로우 - 테스트 (.github/workflows/test.yml)

```yaml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: "3.11"
  POETRY_VERSION: "1.6.1"

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: dantarowallet_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: ${{ env.POETRY_VERSION }}
        virtualenvs-create: true
        virtualenvs-in-project: true
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: .venv
        key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
    
    - name: Install dependencies
      run: poetry install --no-interaction --no-root
    
    - name: Create test env file
      run: |
        cat > .env.test << EOF
        APP_NAME=DantaroWallet
        APP_VERSION=test
        DEBUG=True
        SECRET_KEY=test-secret-key-for-ci-only
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        ALGORITHM=HS256
        DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dantarowallet_test
        REDIS_URL=redis://localhost:6379/0
        BACKEND_CORS_ORIGINS=["http://localhost:3000"]
        WALLET_ENCRYPTION_KEY=test-wallet-encryption-key-32char
        TRON_NETWORK=nile
        TESTING=True
        EOF
    
    - name: Run migrations
      run: |
        cp .env.test .env
        poetry run alembic upgrade head
    
    - name: Run tests with coverage
      run: |
        poetry run pytest -v --cov=app --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
    
    - name: Run linting
      run: |
        poetry run flake8 app tests --max-line-length=88 --extend-ignore=E203
        poetry run black app tests --check
    
    - name: Run type checking
      run: |
        poetry run mypy app --ignore-missing-imports

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
```

### 2. GitHub Actions 워크플로우 - 빌드 및 배포 (.github/workflows/deploy.yml)

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  DOCKER_REGISTRY: docker.io
  DOCKER_IMAGE: ${{ secrets.DOCKER_USERNAME }}/dantarowallet
  DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
  DEPLOY_USER: ${{ secrets.DEPLOY_USER }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Generate version
      id: version
      run: |
        VERSION=$(date +%Y%m%d)-${GITHUB_SHA::7}
        echo "version=$VERSION" >> $GITHUB_OUTPUT
        echo "Version: $VERSION"
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ${{ env.DOCKER_IMAGE }}:latest
          ${{ env.DOCKER_IMAGE }}:${{ steps.version.outputs.version }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64
    
    - name: Send Telegram notification - Build Complete
      if: always()
      uses: appleboy/telegram-action@master
      with:
        to: ${{ secrets.TELEGRAM_CHAT_ID }}
        token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        message: |
          🔨 Build ${{ job.status }}
          
          Repository: ${{ github.repository }}
          Branch: ${{ github.ref_name }}
          Commit: ${{ github.sha }}
          Version: ${{ steps.version.outputs.version }}
          
          ${{ job.status == 'success' && '✅ Docker image built and pushed successfully!' || '❌ Build failed!' }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ env.DEPLOY_HOST }}
        username: ${{ env.DEPLOY_USER }}
        key: ${{ secrets.DEPLOY_SSH_KEY }}
        script: |
          cd /opt/dantarowallet
          
          # Backup current env
          cp .env .env.backup
          
          # Pull latest image
          docker pull ${{ env.DOCKER_IMAGE }}:${{ needs.build.outputs.version }}
          
          # Update docker-compose.yml
          sed -i "s|image: .*|image: ${{ env.DOCKER_IMAGE }}:${{ needs.build.outputs.version }}|g" docker-compose.prod.yml
          
          # Deploy with zero downtime
          docker-compose -f docker-compose.prod.yml up -d --no-deps --scale app=2 app
          sleep 30
          docker-compose -f docker-compose.prod.yml up -d --no-deps app
          
          # Cleanup old containers
          docker system prune -f
          
          # Health check
          sleep 10
          curl -f http://localhost:8000/health || exit 1
    
    - name: Send Telegram notification - Deploy Complete
      if: always()
      uses: appleboy/telegram-action@master
      with:
        to: ${{ secrets.TELEGRAM_CHAT_ID }}
        token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        message: |
          🚀 Deployment ${{ job.status }}
          
          Version: ${{ needs.build.outputs.version }}
          Server: ${{ env.DEPLOY_HOST }}
          
          ${{ job.status == 'success' && '✅ Deployment successful!' || '❌ Deployment failed!' }}
```

### 3. Dockerfile 최적화

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.6.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Docker Compose 프로덕션 설정 (docker-compose.prod.yml)

```yaml
version: '3.8'

services:
  app:
    image: your-dockerhub-username/dantarowallet:latest
    restart: always
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@postgres:5432/dantarowallet
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    networks:
      - dantaro-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: dantarowallet
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - dantaro-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - dantaro-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - app
    networks:
      - dantaro-network

volumes:
  postgres_data:
  redis_data:

networks:
  dantaro-network:
    driver: bridge
```

### 5. Nginx 설정 (nginx/nginx.conf)

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        client_max_body_size 10M;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
```

### 6. 배포 스크립트 (scripts/deploy.sh)

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Variables
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "📦 Backing up database..."
docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U postgres dantarowallet > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Pull latest images
echo "🔄 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Deploy with rolling update
echo "🔄 Starting rolling update..."
docker-compose -f $COMPOSE_FILE up -d --no-deps --scale app=2 app
sleep 30
docker-compose -f $COMPOSE_FILE up -d --no-deps app

# Run migrations
echo "🔧 Running migrations..."
docker-compose -f $COMPOSE_FILE exec -T app alembic upgrade head

# Cleanup
echo "🧹 Cleaning up..."
docker system prune -f

# Health check
echo "🏥 Running health check..."
sleep 10
curl -f http://localhost/health || exit 1

echo "✅ Deployment completed successfully!"
```

### 7. GitHub Secrets 설정 안내 (docs/deployment/github-secrets.md)

```markdown
# GitHub Secrets Configuration

다음 시크릿들을 GitHub 저장소 Settings > Secrets and variables > Actions에 추가하세요:

## Docker Hub
- `DOCKER_USERNAME`: Docker Hub 사용자명
- `DOCKER_PASSWORD`: Docker Hub 액세스 토큰

## 배포 서버
- `DEPLOY_HOST`: 배포 서버 IP 또는 도메인
- `DEPLOY_USER`: SSH 사용자명 (예: ubuntu)
- `DEPLOY_SSH_KEY`: SSH 프라이빗 키 (전체 내용)

## Telegram 알림
- `TELEGRAM_BOT_TOKEN`: Telegram Bot API 토큰
- `TELEGRAM_CHAT_ID`: 알림을 받을 채팅 ID

### SSH 키 생성 방법
```bash
ssh-keygen -t ed25519 -C "github-actions"
# 생성된 프라이빗 키를 DEPLOY_SSH_KEY에 추가
# 공개 키를 서버의 ~/.ssh/authorized_keys에 추가
```

### Telegram Bot 설정 방법
1. @BotFather에게 /newbot 명령으로 봇 생성
2. 봇 토큰 받기
3. 봇과 대화 시작
4. https://api.telegram.org/bot<TOKEN>/getUpdates 에서 chat_id 확인
```

### 8. 서버 초기 설정 스크립트 (scripts/server-setup.sh)

```bash
#!/bin/bash
# 서버 초기 설정 스크립트

echo "🔧 Setting up DantaroWallet server..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/dantarowallet
sudo chown $USER:$USER /opt/dantarowallet
cd /opt/dantarowallet

# Create necessary directories
mkdir -p logs backups nginx/ssl

# Set up firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Install certbot for SSL
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

echo "✅ Server setup completed!"
echo "📝 Next steps:"
echo "1. Copy docker-compose.prod.yml to /opt/dantarowallet/"
echo "2. Create .env file with production settings"
echo "3. Set up SSL certificates with: sudo certbot certonly --standalone -d your-domain.com"
echo "4. Run: docker-compose -f docker-compose.prod.yml up -d"
```

### 9. 환경 변수 템플릿 프로덕션용 (.env.production.example)

```env
# Application
APP_NAME=DantaroWallet
APP_VERSION=1.0.0
DEBUG=False
API_V1_PREFIX=/api/v1

# Security
SECRET_KEY=your-production-secret-key-minimum-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
ALLOWED_HOSTS=["your-domain.com", "www.your-domain.com"]

# Database
DATABASE_URL=postgresql+asyncpg://postgres:strong-password@postgres:5432/dantarowallet
DB_PASSWORD=strong-password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://redis:6379/0

# CORS
BACKEND_CORS_ORIGINS=["https://your-domain.com", "https://app.your-domain.com"]

# Wallet
WALLET_ENCRYPTION_KEY=your-production-wallet-encryption-key-32char

# TRON
TRON_NETWORK=mainnet
TRON_API_KEY=your-trongrid-api-key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

### 10. 모니터링 대시보드 설정 (추가 - Prometheus + Grafana)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    restart: always
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - dantaro-network

  grafana:
    image: grafana/grafana:latest
    restart: always
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    networks:
      - dantaro-network

volumes:
  prometheus_data:
  grafana_data:

networks:
  dantaro-network:
    external: true
```

## 실행 및 검증

### 로컬 테스트
1. GitHub Actions 워크플로우 파일 커밋
2. 코드 푸시하여 자동 테스트 실행 확인

### 배포 준비
1. GitHub Secrets 설정
2. Docker Hub 저장소 생성
3. 서버 초기 설정 실행

### 첫 배포
```bash
git push origin main
# GitHub Actions에서 자동 빌드 및 배포 진행
```

## 검증 포인트

- [ ] GitHub Actions 테스트가 성공적으로 실행되는가?
- [ ] Docker 이미지가 빌드되고 푸시되는가?
- [ ] 배포가 자동으로 진행되는가?
- [ ] Telegram 알림이 전송되는가?
- [ ] 헬스체크가 정상 작동하는가?
- [ ] 롤링 업데이트가 무중단으로 진행되는가?
- [ ] SSL 인증서가 적용되는가?
- [ ] 로그가 정상적으로 수집되는가?

이 문서를 완료하면 완전히 자동화된 CI/CD 파이프라인이 구축되며, 코드 푸시만으로 안전한 배포가 가능해집니다.