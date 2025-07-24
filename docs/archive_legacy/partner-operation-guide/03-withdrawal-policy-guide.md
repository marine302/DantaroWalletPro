# 출금 정책 설정 가이드

## 1. 출금 정책 기본 원칙

### 1.1 정책 설계 철학
- **보안 우선**: 모든 출금은 보안을 최우선으로 처리
- **사용자 경험**: 합리적인 처리 시간과 수수료
- **비용 효율성**: 에너지와 수수료 최적화
- **규제 준수**: AML/KYC 규정 완벽 준수

### 1.2 출금 분류 체계

#### 즉시 출금 (Instant Withdrawal)
- **처리 시간**: 1분 이내
- **한도**: 일일 $1,000 이하
- **조건**: 화이트리스트 주소, KYC 완료
- **수수료**: 표준 + 즉시 처리 프리미엄

#### 일반 출금 (Standard Withdrawal)  
- **처리 시간**: 1-6시간
- **한도**: 일일 $10,000 이하
- **조건**: 기본 KYC 완료
- **수수료**: 표준 수수료

#### 대량 출금 (Bulk Withdrawal)
- **처리 시간**: 6-24시간
- **한도**: 무제한 (별도 승인)
- **조건**: 고급 KYC, 사전 승인
- **수수료**: 협상 가능

## 2. 출금 한도 관리

### 2.1 사용자별 한도 설정

```javascript
// 사용자 출금 한도 계산
const calculateWithdrawalLimits = (user) => {
  const baseLimit = 1000; // 기본 한도 $1,000
  
  const multipliers = {
    kycLevel: {
      basic: 1,
      enhanced: 5,
      premium: 20
    },
    accountAge: {
      new: 0.5,      // 30일 미만
      established: 1, // 30-90일
      veteran: 2      // 90일 이상
    },
    transactionHistory: {
      low: 0.8,    // 거래량 적음
      medium: 1,   // 평균
      high: 1.5    // 거래량 많음
    },
    riskScore: {
      low: 2,      // 저위험
      medium: 1,   // 보통
      high: 0.3    // 고위험
    }
  };
  
  const finalMultiplier = 
    multipliers.kycLevel[user.kycLevel] *
    multipliers.accountAge[user.accountAge] *
    multipliers.transactionHistory[user.transactionHistory] *
    multipliers.riskScore[user.riskScore];
  
  return {
    daily: Math.floor(baseLimit * finalMultiplier),
    weekly: Math.floor(baseLimit * finalMultiplier * 5),
    monthly: Math.floor(baseLimit * finalMultiplier * 20)
  };
};
```

### 2.2 동적 한도 조정

```javascript
// 실시간 한도 조정 시스템
class DynamicLimitManager {
  constructor() {
    this.baseLimits = new Map();
    this.adjustmentFactors = {
      networkCongestion: 1.0,
      liquidityStatus: 1.0,
      riskLevel: 1.0,
      timeOfDay: 1.0
    };
  }
  
  calculateCurrentLimit(userId) {
    const baseLimit = this.baseLimits.get(userId);
    const currentFactors = this.getCurrentAdjustmentFactors();
    
    const adjustedLimit = baseLimit * 
      currentFactors.networkCongestion *
      currentFactors.liquidityStatus *
      currentFactors.riskLevel *
      currentFactors.timeOfDay;
    
    return Math.floor(adjustedLimit);
  }
  
  getCurrentAdjustmentFactors() {
    return {
      networkCongestion: this.calculateCongestionFactor(),
      liquidityStatus: this.calculateLiquidityFactor(),
      riskLevel: this.calculateRiskFactor(),
      timeOfDay: this.calculateTimeFactor()
    };
  }
}
```

## 3. 수수료 전략

### 3.1 수수료 구조 설계

```javascript
// 동적 수수료 계산
const calculateWithdrawalFee = (amount, type, network, urgency) => {
  const baseFees = {
    TRON: {
      fixed: 1,      // 고정 1 USDT
      percentage: 0.001 // 0.1%
    },
    ETHEREUM: {
      fixed: 5,
      percentage: 0.002
    }
  };
  
  const multipliers = {
    urgency: {
      standard: 1,
      express: 1.5,
      instant: 2.5
    },
    amount: {
      small: 1.2,    // < $100
      medium: 1,     // $100-$1000
      large: 0.8     // > $1000
    },
    network: {
      congested: 1.5,
      normal: 1,
      fast: 0.9
    }
  };
  
  const base = baseFees[network];
  const fixedFee = base.fixed * multipliers.urgency[urgency];
  const percentageFee = amount * base.percentage * multipliers.amount[getAmountTier(amount)];
  
  return Math.max(fixedFee, percentageFee);
};
```

### 3.2 수수료 최적화

```javascript
// 수수료 최적화 전략
class FeeOptimizer {
  async optimizeWithdrawalFees() {
    const market = await this.getMarketConditions();
    const competition = await this.getCompetitorFees();
    const costs = await this.getOperationalCosts();
    
    return {
      recommended: this.calculateOptimalFees(market, competition, costs),
      adjustments: this.suggestAdjustments(market),
      timing: this.suggestOptimalTiming(market)
    };
  }
  
  calculateOptimalFees(market, competition, costs) {
    const targetMargin = 0.15; // 15% 마진
    const competitivePosition = 0.95; // 경쟁사 대비 5% 할인
    
    return {
      standard: Math.max(
        costs.operational * (1 + targetMargin),
        competition.average * competitivePosition
      ),
      express: this.standard * 1.5,
      instant: this.standard * 2.5
    };
  }
}
```

## 4. 보안 정책

### 4.1 위험 기반 인증

```javascript
// 위험 평가 시스템
class RiskAssessment {
  evaluateWithdrawalRisk(withdrawal, user) {
    const factors = {
      amount: this.assessAmountRisk(withdrawal.amount, user.history),
      destination: this.assessDestinationRisk(withdrawal.address),
      timing: this.assessTimingRisk(withdrawal.timestamp),
      behavior: this.assessBehaviorRisk(user.recentActivity),
      device: this.assessDeviceRisk(withdrawal.deviceInfo),
      location: this.assessLocationRisk(withdrawal.ipAddress)
    };
    
    const weightedScore = 
      factors.amount * 0.25 +
      factors.destination * 0.20 +
      factors.timing * 0.15 +
      factors.behavior * 0.20 +
      factors.device * 0.10 +
      factors.location * 0.10;
    
    return {
      score: weightedScore,
      level: this.getRiskLevel(weightedScore),
      requiredActions: this.getRequiredActions(weightedScore),
      explanation: this.generateExplanation(factors)
    };
  }
  
  getRequiredActions(score) {
    if (score >= 0.8) return ['MANUAL_REVIEW', '2FA', 'MANAGER_APPROVAL'];
    if (score >= 0.6) return ['2FA', 'EMAIL_CONFIRMATION'];
    if (score >= 0.4) return ['EMAIL_CONFIRMATION'];
    return ['AUTO_APPROVE'];
  }
}
```

### 4.2 다단계 승인 시스템

```javascript
// 승인 워크플로우
class ApprovalWorkflow {
  constructor() {
    this.approvalLevels = {
      auto: { maxAmount: 1000, requiredApprovers: 0 },
      level1: { maxAmount: 10000, requiredApprovers: 1 },
      level2: { maxAmount: 50000, requiredApprovers: 2 },
      level3: { maxAmount: Infinity, requiredApprovers: 3 }
    };
  }
  
  async processWithdrawal(withdrawal) {
    const level = this.determineApprovalLevel(withdrawal);
    
    if (level === 'auto') {
      return await this.autoApprove(withdrawal);
    }
    
    const workflow = await this.createApprovalWorkflow(withdrawal, level);
    return await this.executeWorkflow(workflow);
  }
  
  async createApprovalWorkflow(withdrawal, level) {
    const requiredApprovers = this.approvalLevels[level].requiredApprovers;
    const approvers = await this.selectApprovers(requiredApprovers);
    
    return {
      id: this.generateWorkflowId(),
      withdrawal: withdrawal,
      requiredApprovers: requiredApprovers,
      assignedApprovers: approvers,
      approvals: [],
      status: 'PENDING',
      createdAt: new Date()
    };
  }
}
```

## 5. 자동화 및 스케줄링

### 5.1 배치 처리 시스템

```javascript
// 출금 배치 처리
class WithdrawalBatchProcessor {
  constructor() {
    this.batchConfig = {
      maxBatchSize: 100,
      maxBatchValue: 1000000, // $1M
      processingInterval: 300000, // 5분
      priorityThreshold: 10000 // $10K 이상 우선 처리
    };
  }
  
  async processBatch() {
    const pendingWithdrawals = await this.getPendingWithdrawals();
    const batches = this.createOptimalBatches(pendingWithdrawals);
    
    for (const batch of batches) {
      await this.executeBatch(batch);
    }
  }
  
  createOptimalBatches(withdrawals) {
    // 1. 우선순위별 정렬
    const sorted = withdrawals.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      return a.timestamp - b.timestamp;
    });
    
    // 2. 최적 배치 생성
    const batches = [];
    let currentBatch = [];
    let currentValue = 0;
    
    for (const withdrawal of sorted) {
      if (currentBatch.length >= this.batchConfig.maxBatchSize ||
          currentValue + withdrawal.amount > this.batchConfig.maxBatchValue) {
        if (currentBatch.length > 0) {
          batches.push(currentBatch);
          currentBatch = [];
          currentValue = 0;
        }
      }
      
      currentBatch.push(withdrawal);
      currentValue += withdrawal.amount;
    }
    
    if (currentBatch.length > 0) {
      batches.push(currentBatch);
    }
    
    return batches;
  }
}
```

### 5.2 스마트 스케줄링

```javascript
// 지능형 스케줄러
class SmartScheduler {
  constructor() {
    this.networkAnalyzer = new NetworkAnalyzer();
    this.costOptimizer = new CostOptimizer();
  }
  
  async getOptimalProcessingTime(withdrawal) {
    const networkConditions = await this.networkAnalyzer.analyze();
    const costPredictions = await this.costOptimizer.predict24Hours();
    
    const timeSlots = this.generateTimeSlots();
    const scores = timeSlots.map(slot => {
      return {
        time: slot,
        score: this.calculateScore(slot, networkConditions, costPredictions),
        cost: costPredictions[slot.hour],
        networkSpeed: networkConditions[slot.hour]
      };
    });
    
    return scores.sort((a, b) => b.score - a.score)[0];
  }
  
  calculateScore(slot, network, costs) {
    const timeScore = this.getTimeScore(slot);
    const costScore = 1 - (costs[slot.hour] / Math.max(...Object.values(costs)));
    const speedScore = network[slot.hour].speed / Math.max(...Object.values(network).map(n => n.speed));
    
    return timeScore * 0.4 + costScore * 0.4 + speedScore * 0.2;
  }
}
```

## 6. 모니터링 및 알림

### 6.1 실시간 모니터링

```javascript
// 출금 모니터링 시스템
class WithdrawalMonitor {
  constructor() {
    this.metrics = {
      processedCount: 0,
      failedCount: 0,
      totalVolume: 0,
      averageProcessingTime: 0,
      queueLength: 0
    };
    
    this.alerts = {
      highFailureRate: 0.05,      // 5% 실패율
      longProcessingTime: 3600,   // 1시간
      highQueueLength: 100,       // 대기열 100개
      lowLiquidity: 0.1          // 10% 유동성
    };
  }
  
  async monitor() {
    const current = await this.getCurrentMetrics();
    this.updateMetrics(current);
    
    // 알림 체크
    this.checkAlerts(current);
    
    // 대시보드 업데이트
    this.updateDashboard(current);
  }
  
  checkAlerts(metrics) {
    const alerts = [];
    
    if (metrics.failureRate > this.alerts.highFailureRate) {
      alerts.push({
        type: 'HIGH_FAILURE_RATE',
        severity: 'CRITICAL',
        message: `출금 실패율이 ${metrics.failureRate * 100}%로 임계값을 초과했습니다.`
      });
    }
    
    if (metrics.averageProcessingTime > this.alerts.longProcessingTime) {
      alerts.push({
        type: 'SLOW_PROCESSING',
        severity: 'WARNING',
        message: `평균 처리 시간이 ${metrics.averageProcessingTime}초로 지연되고 있습니다.`
      });
    }
    
    alerts.forEach(alert => this.triggerAlert(alert));
  }
}
```

### 6.2 성능 지표 추적

```javascript
// KPI 계산 및 추적
const calculateWithdrawalKPIs = (data) => {
  return {
    // 처리 성능
    throughput: data.processed / (data.timespan / 3600), // 시간당 처리량
    successRate: data.successful / data.total,
    averageProcessingTime: data.totalProcessingTime / data.processed,
    
    // 사용자 경험
    customerSatisfaction: data.positiveReviews / data.totalReviews,
    escalationRate: data.escalations / data.total,
    
    // 비용 효율성
    costPerTransaction: data.totalCosts / data.processed,
    energyEfficiency: data.energyUsed / data.processed,
    
    // 보안
    fraudDetectionRate: data.fraudDetected / data.suspicious,
    falsePositiveRate: data.falsePositives / data.flagged
  };
};
```

## 7. 규제 준수

### 7.1 AML/KYC 통합

```javascript
// AML 체크 시스템
class AMLChecker {
  async checkWithdrawal(withdrawal, user) {
    const checks = await Promise.all([
      this.checkSanctionsList(withdrawal.address),
      this.checkVelocityRules(user.id, withdrawal.amount),
      this.checkPatternAnalysis(user.transactions),
      this.checkGeographicRestrictions(withdrawal.location)
    ]);
    
    const riskScore = this.calculateAMLRisk(checks);
    
    return {
      approved: riskScore < 0.7,
      riskScore: riskScore,
      requiredActions: this.getRequiredActions(riskScore),
      checks: checks
    };
  }
  
  checkVelocityRules(userId, amount) {
    const rules = [
      { period: '24h', limit: 10000 },
      { period: '7d', limit: 50000 },
      { period: '30d', limit: 200000 }
    ];
    
    return rules.map(rule => ({
      rule: rule,
      currentAmount: this.getAmountInPeriod(userId, rule.period),
      violation: this.getAmountInPeriod(userId, rule.period) + amount > rule.limit
    }));
  }
}
```

### 7.2 감사 로그

```javascript
// 감사 로그 시스템
class AuditLogger {
  async logWithdrawal(withdrawal, user, decision) {
    const auditRecord = {
      id: this.generateAuditId(),
      timestamp: new Date(),
      event: 'WITHDRAWAL_PROCESSED',
      userId: user.id,
      withdrawalId: withdrawal.id,
      amount: withdrawal.amount,
      destination: withdrawal.address,
      decision: decision,
      approvers: decision.approvers,
      riskScore: decision.riskScore,
      processingTime: decision.processingTime,
      fees: withdrawal.fees,
      energyUsed: withdrawal.energyUsed,
      networkConditions: await this.getNetworkConditions(),
      compliance: {
        amlChecked: true,
        kycLevel: user.kycLevel,
        sanctionsChecked: true
      }
    };
    
    await this.store(auditRecord);
    await this.notifyCompliance(auditRecord);
  }
}
```

## 8. 최적화 전략

### 8.1 성능 최적화

```javascript
// 출금 성능 최적화
class WithdrawalOptimizer {
  async optimize() {
    const strategies = [
      this.optimizeNetworkTiming(),
      this.optimizeEnergyUsage(),
      this.optimizeBatchSizes(),
      this.optimizeRoutingPaths()
    ];
    
    const results = await Promise.all(strategies);
    return this.combineOptimizations(results);
  }
  
  async optimizeNetworkTiming() {
    const historical = await this.getHistoricalNetworkData();
    const patterns = this.analyzeNetworkPatterns(historical);
    
    return {
      optimalTimes: patterns.lowCongestionPeriods,
      avoidTimes: patterns.highCongestionPeriods,
      estimatedSavings: patterns.estimatedCostSavings
    };
  }
  
  optimizeBatchSizes() {
    const data = this.getProcessingData();
    const optimalSize = this.findOptimalBatchSize(data);
    
    return {
      recommendedBatchSize: optimalSize,
      expectedImprovement: this.calculateImprovement(optimalSize),
      implementation: this.generateImplementationPlan(optimalSize)
    };
  }
}
```

### 8.2 비용 최적화

```javascript
// 출금 비용 최적화
class CostOptimizer {
  calculateOptimalFeeStructure() {
    const marketAnalysis = this.analyzeMarket();
    const costAnalysis = this.analyzeCosts();
    const competitionAnalysis = this.analyzeCompetition();
    
    return {
      recommended: {
        instant: this.calculateInstantFee(marketAnalysis),
        standard: this.calculateStandardFee(costAnalysis),
        bulk: this.calculateBulkFee(competitionAnalysis)
      },
      justification: this.generateJustification(),
      expectedRevenue: this.projectRevenue(),
      riskAssessment: this.assessPricingRisk()
    };
  }
}
```

## 9. 장애 대응

### 9.1 일반적인 문제 해결

#### 출금 지연
**원인**: 네트워크 혼잡, 에너지 부족, 시스템 부하
**해결책**:
1. 에너지 풀 확인 및 보충
2. 배치 크기 조정
3. 네트워크 상태 모니터링

#### 높은 실패율
**원인**: 잘못된 주소, 잔액 부족, 네트워크 오류
**해결책**:
1. 주소 검증 강화
2. 잔액 실시간 확인
3. 재시도 로직 개선

### 9.2 비상 절차

```javascript
// 비상 상황 대응
class EmergencyResponse {
  async handleCriticalIssue(issue) {
    const response = {
      immediate: await this.takeImmediateAction(issue),
      investigation: await this.startInvestigation(issue),
      communication: await this.notifyStakeholders(issue),
      recovery: await this.planRecovery(issue)
    };
    
    return response;
  }
  
  async takeImmediateAction(issue) {
    switch (issue.type) {
      case 'MASS_FAILURES':
        await this.pauseAutomaticWithdrawals();
        break;
      case 'SECURITY_BREACH':
        await this.lockdownSystem();
        break;
      case 'LIQUIDITY_CRISIS':
        await this.activateEmergencyFunds();
        break;
    }
  }
}
```
