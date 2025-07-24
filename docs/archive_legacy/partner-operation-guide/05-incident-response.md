# 장애 대응 매뉴얼

## 1. 장애 분류 및 우선순위

### 1.1 장애 심각도 분류

#### P0 - 치명적 (Critical)
- **정의**: 전체 서비스 중단, 데이터 손실, 보안 침해
- **대응 시간**: 즉시 (15분 이내)
- **해결 목표**: 2시간 이내
- **에스컬레이션**: 즉시 경영진 알림

**예시**:
- 전체 시스템 다운
- 대량 자금 손실
- 데이터베이스 손상
- 보안 침해 사고

#### P1 - 높음 (High)
- **정의**: 핵심 기능 장애, 다수 사용자 영향
- **대응 시간**: 30분 이내
- **해결 목표**: 4시간 이내
- **에스컬레이션**: 관리팀 알림

**예시**:
- 출금 기능 중단
- API 응답 시간 지연
- 에너지 풀 고갈
- TronLink 연동 실패

#### P2 - 보통 (Medium)
- **정의**: 부분적 기능 저하, 일부 사용자 영향
- **대응 시간**: 2시간 이내
- **해결 목표**: 24시간 이내
- **에스컬레이션**: 팀 리더 알림

#### P3 - 낮음 (Low)
- **정의**: 성능 저하, 사소한 기능 이상
- **대응 시간**: 24시간 이내
- **해결 목표**: 72시간 이내
- **에스컬레이션**: 일반 보고

### 1.2 장애 대응 팀 구성

```javascript
// 장애 대응 팀 관리
class IncidentResponseTeam {
  constructor() {
    this.teams = {
      p0: {
        lead: 'cto@company.com',
        members: [
          'senior-dev@company.com',
          'devops-lead@company.com',
          'security-lead@company.com'
        ],
        escalation: 'ceo@company.com'
      },
      p1: {
        lead: 'tech-lead@company.com',
        members: [
          'dev1@company.com',
          'dev2@company.com',
          'devops@company.com'
        ],
        escalation: 'cto@company.com'
      }
    };
  }
  
  async assembleTeam(severity) {
    const team = this.teams[severity.toLowerCase()];
    
    // 팀원들에게 알림 발송
    await this.notifyTeam(team, severity);
    
    // 전용 커뮤니케이션 채널 생성
    const channel = await this.createIncidentChannel(severity);
    
    return {
      team: team,
      channel: channel,
      assembledAt: new Date()
    };
  }
}
```

## 2. 일반적인 장애 시나리오

### 2.1 시스템 다운

#### 증상
- 웹 서비스 접근 불가
- API 응답 없음
- 데이터베이스 연결 실패

#### 진단 절차
```bash
# 1. 기본 서비스 상태 확인
systemctl status nginx
systemctl status postgresql
systemctl status redis

# 2. 프로세스 상태 확인
ps aux | grep -E "(node|python|nginx)"

# 3. 포트 상태 확인
netstat -tulpn | grep -E "(80|443|3000|5432)"

# 4. 디스크 용량 확인
df -h

# 5. 메모리 상태 확인
free -h
```

#### 복구 절차
```bash
#!/bin/bash
# system-recovery.sh

echo "=== 시스템 복구 시작 ==="

# 1. 서비스 재시작
echo "서비스 재시작..."
systemctl restart nginx
systemctl restart postgresql
systemctl restart redis

# 2. 애플리케이션 재시작
echo "애플리케이션 재시작..."
pm2 restart all

# 3. 상태 확인
echo "상태 확인..."
curl -f http://localhost/health || echo "WARNING: Health check failed"

# 4. 로드 밸런서 복구
echo "로드 밸런서 복구..."
curl -X POST "http://loadbalancer/api/enable-server" \
  -d '{"server": "app1.internal"}'

echo "=== 시스템 복구 완료 ==="
```

### 2.2 데이터베이스 장애

#### 증상
- 트랜잭션 실패
- 느린 쿼리 응답
- 연결 제한 초과

#### 진단 및 복구
```sql
-- 1. 활성 연결 확인
SELECT count(*) FROM pg_stat_activity;

-- 2. 느린 쿼리 확인
SELECT query, query_start, state 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < now() - interval '5 minutes';

-- 3. 잠금 상태 확인
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_locks.pid = blocked_activity.pid
JOIN pg_locks blocking_locks ON blocked_locks.locktype = blocking_locks.locktype
WHERE NOT blocked_locks.granted;

-- 4. 문제가 되는 연결 종료
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle in transaction' 
AND query_start < now() - interval '1 hour';
```

### 2.3 네트워크 장애

#### 증상
- 외부 API 호출 실패
- TRON 네트워크 연결 불가
- DNS 해상도 문제

#### 진단 절차
```bash
# 1. 네트워크 연결 확인
ping -c 4 8.8.8.8
ping -c 4 api.trongrid.io

# 2. DNS 확인
nslookup api.trongrid.io
dig api.trongrid.io

# 3. 방화벽 규칙 확인
iptables -L -n

# 4. 라우팅 테이블 확인
route -n

# 5. 트래픽 모니터링
tcpdump -i eth0 port 443
```

### 2.4 에너지 부족 장애

#### 자동 대응 시스템
```javascript
// 에너지 부족 자동 대응
class EnergyEmergencyResponse {
  constructor() {
    this.emergencyThreshold = 0.05; // 5%
    this.criticalThreshold = 0.01;  // 1%
  }
  
  async handleEnergyShortage() {
    const energyStatus = await this.getEnergyStatus();
    
    if (energyStatus.remaining < this.criticalThreshold) {
      return await this.executeCriticalResponse();
    } else if (energyStatus.remaining < this.emergencyThreshold) {
      return await this.executeEmergencyResponse();
    }
  }
  
  async executeCriticalResponse() {
    // 1. 모든 출금 중단
    await this.pauseAllWithdrawals();
    
    // 2. 긴급 TRX 스테이킹
    await this.emergencyStaking();
    
    // 3. 외부 에너지 구매
    await this.buyEmergencyEnergy();
    
    // 4. 경영진 알림
    await this.notifyManagement('CRITICAL_ENERGY_SHORTAGE');
    
    return {
      status: 'CRITICAL_RESPONSE_EXECUTED',
      actions: ['PAUSE_WITHDRAWALS', 'EMERGENCY_STAKING', 'BUY_ENERGY'],
      estimatedRecovery: '30-60 minutes'
    };
  }
  
  async emergencyStaking() {
    const availableTrx = await this.getAvailableTrx();
    const stakingAmount = Math.min(availableTrx * 0.8, 1000000); // 최대 100만 TRX
    
    try {
      const tx = await this.tronWeb.trx.freezeBalance(
        stakingAmount * 1000000,
        3, // 3일
        'ENERGY'
      );
      
      console.log(`긴급 스테이킹 완료: ${stakingAmount} TRX`);
      return tx;
    } catch (error) {
      console.error('긴급 스테이킹 실패:', error);
      throw error;
    }
  }
}
```

## 3. 모니터링 및 알림

### 3.1 실시간 모니터링 시스템

```javascript
// 종합 모니터링 시스템
class ComprehensiveMonitor {
  constructor() {
    this.metrics = {
      system: new SystemMetrics(),
      application: new ApplicationMetrics(),
      business: new BusinessMetrics(),
      security: new SecurityMetrics()
    };
    
    this.alertRules = this.loadAlertRules();
  }
  
  async startMonitoring() {
    // 1분마다 시스템 메트릭 수집
    setInterval(async () => {
      await this.collectAndAnalyze();
    }, 60000);
    
    // 실시간 로그 모니터링
    this.watchCriticalLogs();
    
    // 비즈니스 메트릭 모니터링
    this.monitorBusinessMetrics();
  }
  
  async collectAndAnalyze() {
    const data = {
      timestamp: new Date(),
      system: await this.metrics.system.collect(),
      application: await this.metrics.application.collect(),
      business: await this.metrics.business.collect(),
      security: await this.metrics.security.collect()
    };
    
    // 이상 징후 탐지
    const anomalies = await this.detectAnomalies(data);
    
    // 알림 규칙 적용
    const alerts = this.evaluateAlertRules(data, anomalies);
    
    // 알림 발송
    for (const alert of alerts) {
      await this.sendAlert(alert);
    }
    
    // 데이터 저장
    await this.storeMetrics(data);
  }
}
```

### 3.2 알림 채널 관리

```javascript
// 다중 채널 알림 시스템
class AlertManager {
  constructor() {
    this.channels = {
      email: new EmailChannel(),
      slack: new SlackChannel(),
      sms: new SMSChannel(),
      webhook: new WebhookChannel(),
      voice: new VoiceChannel()
    };
    
    this.escalationMatrix = {
      P0: ['voice', 'sms', 'slack', 'email'],
      P1: ['sms', 'slack', 'email'],
      P2: ['slack', 'email'],
      P3: ['email']
    };
  }
  
  async sendAlert(alert) {
    const channels = this.escalationMatrix[alert.severity];
    
    for (const channelName of channels) {
      try {
        await this.channels[channelName].send(alert);
      } catch (error) {
        console.error(`알림 발송 실패 (${channelName}):`, error);
      }
    }
    
    // 알림 발송 로그
    await this.logAlert(alert);
  }
  
  async escalateAlert(alertId) {
    const alert = await this.getAlert(alertId);
    
    if (!alert.acknowledged && this.shouldEscalate(alert)) {
      alert.severity = this.upgradeSeverity(alert.severity);
      await this.sendAlert(alert);
    }
  }
}
```

## 4. 복구 절차

### 4.1 데이터 복구

```bash
#!/bin/bash
# data-recovery.sh

echo "=== 데이터 복구 시작 ==="

# 1. 서비스 중단
echo "서비스 중단..."
systemctl stop nginx
systemctl stop dantaro-app

# 2. 데이터베이스 백업 확인
echo "최신 백업 확인..."
LATEST_BACKUP=$(ls -t /backup/db/*.sql | head -1)
echo "최신 백업: $LATEST_BACKUP"

# 3. 데이터베이스 복구
echo "데이터베이스 복구..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS dantaro;"
sudo -u postgres psql -c "CREATE DATABASE dantaro;"
sudo -u postgres psql dantaro < $LATEST_BACKUP

# 4. 데이터 일관성 검사
echo "데이터 일관성 검사..."
sudo -u postgres psql dantaro -c "
  SELECT 
    (SELECT COUNT(*) FROM users) as user_count,
    (SELECT COUNT(*) FROM wallets) as wallet_count,
    (SELECT COUNT(*) FROM transactions) as tx_count;
"

# 5. 서비스 재시작
echo "서비스 재시작..."
systemctl start dantaro-app
systemctl start nginx

echo "=== 데이터 복구 완료 ==="
```

### 4.2 서비스 무중단 복구

```javascript
// 무중단 복구 관리
class ZeroDowntimeRecovery {
  constructor() {
    this.loadBalancer = new LoadBalancerManager();
    this.healthChecker = new HealthChecker();
  }
  
  async performRollingRecovery() {
    const servers = await this.getServerList();
    
    for (const server of servers) {
      console.log(`서버 ${server.id} 복구 시작`);
      
      // 1. 로드 밸런서에서 제외
      await this.loadBalancer.removeServer(server);
      
      // 2. 기존 연결 완료 대기
      await this.waitForConnectionDrain(server);
      
      // 3. 서버 복구
      await this.recoverServer(server);
      
      // 4. 헬스 체크
      const healthy = await this.healthChecker.check(server);
      
      if (healthy) {
        // 5. 로드 밸런서에 추가
        await this.loadBalancer.addServer(server);
        console.log(`서버 ${server.id} 복구 완료`);
      } else {
        console.error(`서버 ${server.id} 복구 실패`);
        await this.notifyFailure(server);
      }
      
      // 다음 서버 복구 전 안정화 대기
      await this.sleep(30000);
    }
  }
  
  async recoverServer(server) {
    // 1. 애플리케이션 중단
    await this.stopApplication(server);
    
    // 2. 코드 업데이트
    await this.updateCode(server);
    
    // 3. 의존성 업데이트
    await this.updateDependencies(server);
    
    // 4. 설정 파일 업데이트
    await this.updateConfiguration(server);
    
    // 5. 애플리케이션 시작
    await this.startApplication(server);
  }
}
```

## 5. 사후 분석

### 5.1 포스트모템 프로세스

```javascript
// 포스트모템 관리 시스템
class PostmortemManager {
  constructor() {
    this.template = {
      summary: '',
      timeline: [],
      rootCause: '',
      impact: {
        users: 0,
        revenue: 0,
        duration: 0
      },
      contributing_factors: [],
      lessons_learned: [],
      action_items: []
    };
  }
  
  async generatePostmortem(incidentId) {
    const incident = await this.getIncident(incidentId);
    const timeline = await this.reconstructTimeline(incident);
    const metrics = await this.calculateImpact(incident);
    
    const postmortem = {
      ...this.template,
      incident_id: incidentId,
      summary: this.generateSummary(incident),
      timeline: timeline,
      impact: metrics,
      root_cause: await this.analyzeRootCause(incident),
      contributing_factors: await this.identifyContributingFactors(incident)
    };
    
    return postmortem;
  }
  
  async analyzeRootCause(incident) {
    // 5 Why 분석
    const whys = [];
    let currentWhy = incident.initial_symptom;
    
    for (let i = 0; i < 5; i++) {
      const why = await this.askWhy(currentWhy);
      whys.push(why);
      currentWhy = why;
    }
    
    return {
      immediate_cause: whys[0],
      underlying_cause: whys[whys.length - 1],
      analysis_chain: whys
    };
  }
  
  generateActionItems(postmortem) {
    const actionItems = [];
    
    // 즉시 조치 항목
    if (postmortem.severity >= 'P1') {
      actionItems.push({
        type: 'IMMEDIATE',
        description: '모니터링 알림 개선',
        owner: 'DevOps Team',
        due_date: this.addDays(new Date(), 7),
        priority: 'HIGH'
      });
    }
    
    // 단기 개선 항목
    actionItems.push({
      type: 'SHORT_TERM',
      description: '문서화 개선',
      owner: 'Engineering Team',
      due_date: this.addDays(new Date(), 30),
      priority: 'MEDIUM'
    });
    
    // 장기 개선 항목
    actionItems.push({
      type: 'LONG_TERM',
      description: '아키텍처 개선',
      owner: 'Architecture Team',
      due_date: this.addDays(new Date(), 90),
      priority: 'LOW'
    });
    
    return actionItems;
  }
}
```

### 5.2 성능 개선 추적

```javascript
// 성능 개선 추적 시스템
class PerformanceTracker {
  constructor() {
    this.metrics = {
      mttr: [], // Mean Time To Recovery
      mtbf: [], // Mean Time Between Failures
      availability: [],
      customer_satisfaction: []
    };
  }
  
  async calculateMTTR(incidents) {
    const recoveryTimes = incidents.map(incident => {
      const start = new Date(incident.created_at);
      const end = new Date(incident.resolved_at);
      return (end - start) / 1000 / 60; // 분 단위
    });
    
    return {
      average: recoveryTimes.reduce((a, b) => a + b, 0) / recoveryTimes.length,
      median: this.calculateMedian(recoveryTimes),
      p95: this.calculatePercentile(recoveryTimes, 95),
      trend: this.calculateTrend(this.metrics.mttr)
    };
  }
  
  async generateImprovementReport() {
    const lastMonth = await this.getIncidents(30);
    const lastQuarter = await this.getIncidents(90);
    
    return {
      mttr: {
        current: await this.calculateMTTR(lastMonth),
        previous: await this.calculateMTTR(lastQuarter),
        improvement: this.calculateImprovement('mttr')
      },
      mtbf: {
        current: await this.calculateMTBF(lastMonth),
        previous: await this.calculateMTBF(lastQuarter),
        improvement: this.calculateImprovement('mtbf')
      },
      availability: {
        current: await this.calculateAvailability(lastMonth),
        target: 99.9,
        gap: this.calculateAvailabilityGap()
      },
      recommendations: this.generateRecommendations()
    };
  }
}
```

## 6. 예방적 유지보수

### 6.1 정기 점검 스케줄

```javascript
// 예방적 유지보수 스케줄러
class PreventiveMaintenanceScheduler {
  constructor() {
    this.schedule = {
      daily: [
        'system_health_check',
        'backup_verification',
        'log_analysis'
      ],
      weekly: [
        'security_scan',
        'performance_analysis',
        'capacity_planning'
      ],
      monthly: [
        'dependency_update',
        'disaster_recovery_test',
        'security_audit'
      ],
      quarterly: [
        'architecture_review',
        'business_continuity_test',
        'vendor_assessment'
      ]
    };
  }
  
  async executeMaintenanceTasks(frequency) {
    const tasks = this.schedule[frequency];
    const results = [];
    
    for (const task of tasks) {
      try {
        const result = await this.executeTask(task);
        results.push({
          task: task,
          status: 'SUCCESS',
          result: result,
          timestamp: new Date()
        });
      } catch (error) {
        results.push({
          task: task,
          status: 'FAILED',
          error: error.message,
          timestamp: new Date()
        });
      }
    }
    
    await this.generateMaintenanceReport(frequency, results);
    return results;
  }
}
```

### 6.2 용량 계획

```javascript
// 용량 계획 시스템
class CapacityPlanner {
  async analyzeCapacityTrends() {
    const metrics = await this.getHistoricalMetrics();
    
    return {
      cpu: this.analyzeCPUTrends(metrics.cpu),
      memory: this.analyzeMemoryTrends(metrics.memory),
      storage: this.analyzeStorageTrends(metrics.storage),
      network: this.analyzeNetworkTrends(metrics.network),
      energy: this.analyzeEnergyTrends(metrics.energy)
    };
  }
  
  async predictCapacityNeeds(timeframe) {
    const trends = await this.analyzeCapacityTrends();
    const growth = this.calculateGrowthRate(trends);
    
    return {
      timeframe: timeframe,
      predictions: {
        cpu: this.predictResource('cpu', growth, timeframe),
        memory: this.predictResource('memory', growth, timeframe),
        storage: this.predictResource('storage', growth, timeframe),
        network: this.predictResource('network', growth, timeframe)
      },
      recommendations: this.generateCapacityRecommendations(growth),
      costs: this.estimateCosts(growth, timeframe)
    };
  }
}
```

## 7. 비즈니스 연속성

### 7.1 재해 복구 계획

```yaml
# 재해 복구 계획
disaster_recovery:
  rto: 4 hours  # Recovery Time Objective
  rpo: 1 hour   # Recovery Point Objective
  
  sites:
    primary:
      location: "Seoul"
      capacity: 100%
      
    secondary:
      location: "Busan"
      capacity: 50%
      failover_time: 30 minutes
      
    backup:
      location: "Cloud"
      capacity: 25%
      failover_time: 2 hours
      
  procedures:
    - assess_damage
    - activate_incident_team
    - notify_stakeholders
    - execute_failover
    - verify_operations
    - communicate_status
```

### 7.2 백업 및 복구 테스트

```bash
#!/bin/bash
# backup-test.sh

echo "=== 백업 및 복구 테스트 시작 ==="

# 1. 테스트 환경 준비
echo "테스트 환경 준비..."
docker run -d --name test-db postgres:13

# 2. 최신 백업으로 복구
echo "백업에서 복구..."
LATEST_BACKUP=$(ls -t /backup/*.sql | head -1)
docker exec -i test-db psql -U postgres < $LATEST_BACKUP

# 3. 데이터 검증
echo "데이터 검증..."
docker exec test-db psql -U postgres -c "
  SELECT 
    'users' as table_name, count(*) as row_count 
  FROM users
  UNION ALL
  SELECT 
    'transactions', count(*) 
  FROM transactions;
"

# 4. 애플리케이션 테스트
echo "애플리케이션 테스트..."
export DATABASE_URL="postgresql://postgres@localhost:5432/dantaro"
npm test

# 5. 정리
echo "테스트 환경 정리..."
docker stop test-db
docker rm test-db

echo "=== 백업 및 복구 테스트 완료 ==="
```

## 8. 커뮤니케이션 프로토콜

### 8.1 이해관계자 알림

```javascript
// 이해관계자 커뮤니케이션 관리
class StakeholderCommunication {
  constructor() {
    this.stakeholders = {
      internal: {
        engineering: ['dev-team@company.com'],
        operations: ['ops-team@company.com'],
        management: ['cto@company.com', 'ceo@company.com'],
        support: ['support@company.com']
      },
      external: {
        customers: ['notifications@customer-portal.com'],
        partners: ['partners@company.com'],
        vendors: ['vendor-relations@company.com']
      }
    };
  }
  
  async notifyIncident(incident) {
    const notifications = this.determineNotifications(incident);
    
    for (const notification of notifications) {
      await this.sendNotification(notification);
    }
  }
  
  determineNotifications(incident) {
    const notifications = [];
    
    // 내부 팀 알림
    if (incident.severity >= 'P1') {
      notifications.push({
        audience: this.stakeholders.internal.management,
        urgency: 'IMMEDIATE',
        template: 'incident_management_alert'
      });
    }
    
    // 고객 알림
    if (incident.customer_impact) {
      notifications.push({
        audience: this.stakeholders.external.customers,
        urgency: 'HIGH',
        template: 'customer_service_alert'
      });
    }
    
    return notifications;
  }
}
```

### 8.2 상태 페이지 관리

```javascript
// 서비스 상태 페이지 관리
class StatusPageManager {
  async updateServiceStatus(incident) {
    const status = this.determineServiceStatus(incident);
    
    await this.updateStatusPage({
      overall_status: status.overall,
      services: status.services,
      incident: {
        title: incident.title,
        description: incident.description,
        severity: incident.severity,
        updates: incident.updates
      }
    });
    
    // 구독자들에게 알림
    await this.notifySubscribers(status);
  }
  
  determineServiceStatus(incident) {
    const affectedServices = incident.affected_services;
    const serviceStatus = {};
    
    for (const service of this.getAllServices()) {
      if (affectedServices.includes(service.id)) {
        serviceStatus[service.id] = incident.severity >= 'P1' ? 'DOWN' : 'DEGRADED';
      } else {
        serviceStatus[service.id] = 'OPERATIONAL';
      }
    }
    
    const overall = this.calculateOverallStatus(serviceStatus);
    
    return {
      overall: overall,
      services: serviceStatus
    };
  }
}
```
