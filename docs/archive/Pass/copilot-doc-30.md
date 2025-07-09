# Copilot 문서 #30: 프로덕션 배포 및 운영 가이드

## 목표
DantaroWallet SaaS 플랫폼을 안전하고 확장 가능한 방식으로 프로덕션 환경에 배포하고 운영하는 완전한 가이드를 제공합니다.

## 상세 지시사항

### 1. 인프라 아키텍처

#### 1.1 AWS 기반 인프라 구성
```yaml
# infrastructure/terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC 구성
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "dantaro-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  enable_dns_hostnames = true
  
  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}

# EKS 클러스터
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "dantaro-eks"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10
      
      instance_types = ["t3.large"]
      
      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }
    }
    
    spot = {
      desired_size = 2
      min_size     = 1
      max_size     = 5
      
      instance_types = ["t3.large", "t3a.large"]
      capacity_type  = "SPOT"
      
      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "spot"
      }
    }
  }
}

# RDS (PostgreSQL)
module "rds" {
  source = "terraform-aws-modules/rds/aws"
  
  identifier = "dantaro-db"
  
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r6g.xlarge"
  allocated_storage = 100
  storage_encrypted = true
  
  db_name  = "dantarowallet"
  username = "postgres"
  port     = "5432"
  
  vpc_security_group_ids = [module.rds_security_group.security_group_id]
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  
  backup_retention_period = 30
  backup_window          = "03:00-06:00"
  maintenance_window     = "Mon:00:00-Mon:03:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  multi_az               = true
  deletion_protection    = true
  
  tags = {
    Environment = var.environment
  }
}

# ElastiCache (Redis)
module "elasticache" {
  source = "terraform-aws-modules/elasticache/aws"
  
  cluster_id           = "dantaro-cache"
  engine              = "redis"
  node_type           = "cache.r6g.large"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379
  
  subnet_group_name = module.vpc.elasticache_subnet_group_name
  security_group_ids = [module.elasticache_security_group.security_group_id]
  
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  
  tags = {
    Environment = var.environment
  }
}

# S3 버킷
resource "aws_s3_bucket" "static_assets" {
  bucket = "dantaro-static-assets-${var.environment}"
  
  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "backups" {
  bucket = "dantaro-backups-${var.environment}"
  
  lifecycle_rule {
    enabled = true
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
  
  tags = {
    Environment = var.environment
  }
}

# CloudFront CDN
module "cdn" {
  source = "terraform-aws-modules/cloudfront/aws"
  
  aliases = ["cdn.dantarowallet.com"]
  
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-static-assets"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.static_assets.cloudfront_access_identity_path
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static-assets"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }
  
  price_class = "PriceClass_200"
  
  tags = {
    Environment = var.environment
  }
}
```

### 2. Kubernetes 배포 구성

#### 2.1 애플리케이션 배포 매니페스트
```yaml
# k8s/base/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dantaro-backend
  labels:
    app: dantaro-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dantaro-backend
  template:
    metadata:
      labels:
        app: dantaro-backend
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - dantaro-backend
              topologyKey: kubernetes.io/hostname
      
      containers:
      - name: backend
        image: dantarowallet/backend:latest
        ports:
        - containerPort: 8000
        
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: secret-key
        - name: TRON_API_KEY
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: tron-api-key
              
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
            
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          
        volumeMounts:
        - name: app-logs
          mountPath: /app/logs
          
      volumes:
      - name: app-logs
        persistentVolumeClaim:
          claimName: logs-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: dantaro-backend
spec:
  selector:
    app: dantaro-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dantaro-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dantaro-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### 2.2 Celery 워커 배포
```yaml
# k8s/base/celery-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: dantarowallet/backend:latest
        command: ["celery", "-A", "app.core.celery", "worker", "-l", "info"]
        
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: redis-url
              
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
spec:
  replicas: 1  # Beat는 단일 인스턴스만
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: beat
        image: dantarowallet/backend:latest
        command: ["celery", "-A", "app.core.celery", "beat", "-l", "info"]
        
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: dantaro-secrets
              key: redis-url
```

#### 2.3 Ingress 설정
```yaml
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dantaro-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.dantarowallet.com
    - "*.dantarowallet.com"
    secretName: dantaro-tls
    
  rules:
  - host: api.dantarowallet.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dantaro-backend
            port:
              number: 80
              
  - host: "*.dantarowallet.com"
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: partner-frontend
            port:
              number: 80
```

### 3. CI/CD 파이프라인

#### 3.1 GitHub Actions 워크플로우
```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: ap-northeast-2
  ECR_REPOSITORY: dantarowallet
  EKS_CLUSTER_NAME: dantaro-eks

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
        
    - name: Run tests
      run: |
        poetry run pytest --cov=app --cov-report=xml
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
      
    - name: Build and push image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
        
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name ${{ env.EKS_CLUSTER_NAME }}
        
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/dantaro-backend backend=${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
        kubectl rollout status deployment/dantaro-backend
        
    - name: Run database migrations
      run: |
        kubectl exec -it $(kubectl get pod -l app=dantaro-backend -o jsonpath="{.items[0].metadata.name}") -- alembic upgrade head
        
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Production deployment completed'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 4. 모니터링 및 로깅

#### 4.1 Prometheus 모니터링 설정
```yaml
# k8s/monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
          
    rule_files:
      - /etc/prometheus/rules/*.yml
      
    scrape_configs:
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
        
    - job_name: 'dantaro-backend'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: dantaro-backend
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: __address__
        replacement: $1:8000
        
    - job_name: 'node-exporter'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:9100'
        target_label: __address__
```

#### 4.2 알림 규칙
```yaml
# k8s/monitoring/alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
data:
  alerts.yml: |
    groups:
    - name: dantaro_alerts
      interval: 30s
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"
          
      - alert: EnergyPoolLow
        expr: energy_pool_available / energy_pool_total < 0.2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Energy pool running low"
          description: "Energy pool is below 20%"
          
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections near limit"
          description: "Database connections are above 80% of max"
          
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod is crash looping"
          description: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash looping"
          
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container memory usage is high"
          description: "Container {{ $labels.container }} memory usage is above 90%"
```

#### 4.3 ELK 스택 로깅
```yaml
# k8s/logging/elasticsearch.yaml
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: dantaro-es
spec:
  version: 8.11.0
  nodeSets:
  - name: master
    count: 3
    config:
      node.roles: ["master"]
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
        storageClassName: gp3
        
  - name: data
    count: 3
    config:
      node.roles: ["data", "ingest"]
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 100Gi
        storageClassName: gp3
---
# k8s/logging/filebeat.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/*.log
      processors:
        - add_kubernetes_metadata:
            host: ${NODE_NAME}
            matchers:
            - logs_path:
                logs_path: "/var/log/containers/"
                
    output.elasticsearch:
      hosts: ['${ELASTICSEARCH_HOST:elasticsearch}:${ELASTICSEARCH_PORT:9200}']
      username: ${ELASTICSEARCH_USERNAME}
      password: ${ELASTICSEARCH_PASSWORD}
      
    setup.kibana:
      host: '${KIBANA_HOST:kibana}:${KIBANA_PORT:5601}'
```

### 5. 보안 강화

#### 5.1 보안 스캔 자동화
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * *'  # 매일 자정
  push:
    branches: [main, develop]

jobs:
  trivy-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'dantarowallet/backend:latest'
        format: 'sarif'
        output: 'trivy-results.sarif'
        
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
        
  dependency-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run OWASP Dependency Check
      uses: dependency-check/Dependency-Check_Action@main
      with:
        project: 'dantarowallet'
        path: '.'
        format: 'HTML'
        
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: dependency-check-report
        path: reports/
```

#### 5.2 네트워크 정책
```yaml
# k8s/security/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: dantaro-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
      
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
      
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
      
  - to:  # 외부 API 호출 허용
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

### 6. 백업 및 재해 복구

#### 6.1 자동 백업 스크립트
```bash
#!/bin/bash
# scripts/backup.sh

set -e

# 환경 변수
BACKUP_DIR="/backups"
S3_BUCKET="dantaro-backups-prod"
DB_NAME="dantarowallet"
RETENTION_DAYS=30

# 타임스탬프
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 데이터베이스 백업
echo "Starting database backup..."
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Redis 백업
echo "Starting Redis backup..."
redis-cli -h $REDIS_HOST --rdb "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

# 파일 암호화
echo "Encrypting backups..."
openssl enc -aes-256-cbc -salt -in "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz" \
  -out "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz.enc" -k $BACKUP_PASSWORD
openssl enc -aes-256-cbc -salt -in "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb" \
  -out "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb.enc" -k $BACKUP_PASSWORD

# S3 업로드
echo "Uploading to S3..."
aws s3 cp "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz.enc" "s3://$S3_BUCKET/database/"
aws s3 cp "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb.enc" "s3://$S3_BUCKET/redis/"

# 로컬 백업 정리
find $BACKUP_DIR -name "*.enc" -mtime +7 -delete

# S3 백업 정리
aws s3 ls "s3://$S3_BUCKET/database/" | while read -r line;
do
  createDate=$(echo $line | awk '{print $1" "$2}')
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk '{print $4}')
    aws s3 rm "s3://$S3_BUCKET/database/$fileName"
  fi
done

echo "Backup completed successfully!"

# 백업 성공 알림
curl -X POST $SLACK_WEBHOOK -H 'Content-type: application/json' \
  --data "{\"text\":\"✅ Production backup completed successfully at $TIMESTAMP\"}"
```

#### 6.2 복구 절차
```bash
#!/bin/bash
# scripts/restore.sh

set -e

# 복구할 백업 파일 선택
echo "Available backups:"
aws s3 ls "s3://$S3_BUCKET/database/" | grep ".enc$" | sort -r | head -20

read -p "Enter backup filename to restore: " BACKUP_FILE

# S3에서 백업 다운로드
echo "Downloading backup..."
aws s3 cp "s3://$S3_BUCKET/database/$BACKUP_FILE" "/tmp/$BACKUP_FILE"

# 백업 복호화
echo "Decrypting backup..."
openssl enc -aes-256-cbc -d -in "/tmp/$BACKUP_FILE" \
  -out "/tmp/restore.sql.gz" -k $BACKUP_PASSWORD

# 데이터베이스 복구
echo "Restoring database..."
gunzip -c "/tmp/restore.sql.gz" | PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME

echo "Restore completed successfully!"

# 복구 완료 알림
curl -X POST $SLACK_WEBHOOK -H 'Content-type: application/json' \
  --data "{\"text\":\"✅ Production restore completed from $BACKUP_FILE\"}"
```

### 7. 운영 절차서

#### 7.1 배포 체크리스트
```markdown
# 프로덕션 배포 체크리스트

## 배포 전
- [ ] 모든 테스트 통과 확인
- [ ] 데이터베이스 마이그레이션 검토
- [ ] 환경 변수 확인
- [ ] 리소스 요구사항 검토
- [ ] 롤백 계획 수립
- [ ] 배포 공지 발송

## 배포 중
- [ ] 현재 버전 백업
- [ ] 데이터베이스 백업
- [ ] 블루-그린 배포 시작
- [ ] 헬스체크 모니터링
- [ ] 로그 모니터링

## 배포 후
- [ ] 기능 테스트
- [ ] 성능 모니터링
- [ ] 에러 로그 확인
- [ ] 사용자 피드백 모니터링
- [ ] 배포 완료 보고
```

#### 7.2 장애 대응 매뉴얼
```markdown
# 장애 대응 프로세스

## 1. 장애 감지
- 모니터링 알림 확인
- 사용자 신고 접수
- 로그 분석

## 2. 초기 대응
### 심각도 분류
- P1 (Critical): 서비스 전체 중단
- P2 (Major): 주요 기능 장애
- P3 (Minor): 일부 기능 장애
- P4 (Low): 사소한 문제

### 즉시 조치
1. 장애 공지 발송
2. 대응팀 소집
3. 워룸 개설

## 3. 문제 해결
### 진단
- 로그 분석
- 메트릭 확인
- 최근 변경사항 검토

### 복구
- 긴급 패치
- 롤백 (필요시)
- 스케일링 조정

## 4. 사후 처리
- RCA (Root Cause Analysis) 작성
- 재발 방지 대책 수립
- 프로세스 개선
```

### 8. 성능 최적화

#### 8.1 데이터베이스 최적화
```sql
-- 인덱스 최적화
CREATE INDEX CONCURRENTLY idx_transactions_user_created 
ON transactions(user_id, created_at DESC) 
WHERE status = 'completed';

CREATE INDEX CONCURRENTLY idx_users_partner_active 
ON users(partner_id) 
WHERE is_active = true;

-- 파티션 테이블 생성 (대용량 트랜잭션)
CREATE TABLE transactions_2025_01 PARTITION OF transactions
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- 자동 파티션 생성 함수
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE + interval '1 month');
    end_date := start_date + interval '1 month';
    partition_name := 'transactions_' || to_char(start_date, 'YYYY_MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF transactions FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- 매월 실행되는 크론잡
SELECT cron.schedule('create-partitions', '0 0 1 * *', 'SELECT create_monthly_partitions()');
```

#### 8.2 캐싱 전략
```python
# app/core/cache.py
from functools import wraps
import hashlib
import json
from typing import Optional, Callable, Any

class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_hash = hashlib.md5(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()
        return f"{prefix}:{key_hash}"
        
    def cached(
        self, 
        prefix: str, 
        ttl: int = 300,
        version: int = 1
    ) -> Callable:
        """캐시 데코레이터"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                # 캐시 키 생성
                cache_key = self.cache_key(
                    f"{prefix}:v{version}", 
                    *args, 
                    **kwargs
                )
                
                # 캐시 조회
                cached_value = await self.redis.get(cache_key)
                if cached_value:
                    return json.loads(cached_value)
                    
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # 캐시 저장
                await self.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(result)
                )
                
                return result
            return wrapper
        return decorator
        
    async def invalidate_pattern(self, pattern: str):
        """패턴 기반 캐시 무효화"""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, 
                match=pattern, 
                count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

# 사용 예시
cache_manager = CacheManager(redis_client)

@cache_manager.cached("user_stats", ttl=600, version=1)
async def get_user_statistics(user_id: int) -> Dict:
    # 복잡한 통계 계산
    pass
```

### 9. 비용 최적화

#### 9.1 스팟 인스턴스 활용
```yaml
# k8s/spot-instances.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spot-instance-config
data:
  spot-config: |
    # 스팟 인스턴스 비율
    spot_ratio: 0.7  # 70% 스팟, 30% 온디맨드
    
    # 스팟 인스턴스 타입
    instance_types:
      - t3.large
      - t3a.large
      - t2.large
      
    # 중단 처리
    interruption_handling:
      grace_period: 120  # 2분
      drain_node: true
      
    # 워크로드 배치 전략
    workload_placement:
      stateless: spot  # 무상태 워크로드는 스팟에
      stateful: on_demand  # 상태유지 워크로드는 온디맨드에
```

#### 9.2 리소스 최적화 스크립트
```python
#!/usr/bin/env python3
# scripts/optimize_resources.py

import boto3
import kubernetes
from datetime import datetime, timedelta

class ResourceOptimizer:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
        self.k8s = kubernetes.client.ApiClient()
        
    def analyze_ec2_usage(self):
        """EC2 인스턴스 사용률 분석"""
        instances = self.ec2.describe_instances()
        
        underutilized = []
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] != 'running':
                    continue
                    
                # CPU 사용률 확인
                cpu_stats = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {'Name': 'InstanceId', 'Value': instance['InstanceId']}
                    ],
                    StartTime=datetime.now() - timedelta(days=7),
                    EndTime=datetime.now(),
                    Period=3600,
                    Statistics=['Average']
                )
                
                avg_cpu = sum(
                    point['Average'] for point in cpu_stats['Datapoints']
                ) / len(cpu_stats['Datapoints'])
                
                if avg_cpu < 20:  # 20% 미만 사용
                    underutilized.append({
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'AvgCPU': avg_cpu
                    })
                    
        return underutilized
        
    def recommend_rightsizing(self):
        """인스턴스 크기 조정 추천"""
        recommendations = []
        
        underutilized = self.analyze_ec2_usage()
        for instance in underutilized:
            current_type = instance['InstanceType']
            
            # 다운사이징 추천
            if current_type.startswith('t3.'):
                size = current_type.split('.')[1]
                size_map = {
                    'xlarge': 'large',
                    'large': 'medium',
                    'medium': 'small'
                }
                
                if size in size_map:
                    new_type = f"t3.{size_map[size]}"
                    
                    # 비용 계산
                    current_cost = self.get_instance_cost(current_type)
                    new_cost = self.get_instance_cost(new_type)
                    savings = (current_cost - new_cost) * 24 * 30  # 월간
                    
                    recommendations.append({
                        'InstanceId': instance['InstanceId'],
                        'CurrentType': current_type,
                        'RecommendedType': new_type,
                        'MonthlySavings': savings
                    })
                    
        return recommendations

if __name__ == "__main__":
    optimizer = ResourceOptimizer()
    
    # 분석 실행
    underutilized = optimizer.analyze_ec2_usage()
    recommendations = optimizer.recommend_rightsizing()
    
    # 리포트 생성
    print("=== 리소스 최적화 리포트 ===")
    print(f"저사용 인스턴스: {len(underutilized)}개")
    print(f"예상 월간 절감액: ${sum(r['MonthlySavings'] for r in recommendations):.2f}")
    
    for rec in recommendations:
        print(f"- {rec['InstanceId']}: {rec['CurrentType']} → {rec['RecommendedType']} (${rec['MonthlySavings']:.2f}/월)")
```

## 검증 포인트

- [ ] 인프라가 자동으로 프로비저닝되는가?
- [ ] 무중단 배포가 가능한가?
- [ ] 자동 스케일링이 작동하는가?
- [ ] 모니터링 알림이 발송되는가?
- [ ] 백업 및 복구가 정상 작동하는가?
- [ ] 보안 스캔이 자동 실행되는가?
- [ ] 비용 최적화가 적용되는가?
- [ ] 장애 대응 프로세스가 명확한가?

이 가이드를 통해 DantaroWallet SaaS 플랫폼을 안정적이고 확장 가능한 방식으로 운영할 수 있습니다.