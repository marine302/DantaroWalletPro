// Doc-30 기반 감사 및 컴플라이언스 타입 정의
export enum AuditEventType {
  TRANSACTION_CREATED = "transaction_created",
  TRANSACTION_COMPLETED = "transaction_completed",
  TRANSACTION_FAILED = "transaction_failed",
  WALLET_CREATED = "wallet_created",
  WITHDRAWAL_REQUESTED = "withdrawal_requested",
  WITHDRAWAL_APPROVED = "withdrawal_approved",
  DEPOSIT_DETECTED = "deposit_detected",
  SUSPICIOUS_ACTIVITY = "suspicious_activity",
  COMPLIANCE_CHECK = "compliance_check",
  USER_ACTION = "user_action",
  SYSTEM_ACTION = "system_action"
}

export interface AuditLog {
  id: number;
  timestamp: Date;
  
  // 이벤트 정보
  event_type: AuditEventType;
  event_category: string; // "transaction", "compliance", "security"
  severity: string; // "info", "warning", "critical"
  
  // 엔티티 정보
  entity_type: string; // "user", "transaction", "wallet"
  entity_id: string;
  partner_id?: number;
  user_id?: number;
  
  // 상세 정보
  event_data: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  
  // 블록체인 증적
  block_hash?: string; // 이전 로그의 해시
  log_hash?: string;   // 현재 로그의 해시
  blockchain_tx_hash?: string; // 블록체인 저장 트랜잭션
}

export interface SuspiciousActivity {
  id: number;
  detection_time: Date;
  transaction_id?: string;
  user_id?: string;
  partner_id?: string;
  
  // 탐지 정보
  detection_type: string; // "pattern_anomaly", "velocity_check", "amount_threshold"
  risk_score: number; // 0-100
  confidence_level: number; // 0-1
  
  // ML 모델 정보
  model_version: string;
  features_used: Record<string, any>;
  
  // 상세 정보
  description: string;
  recommendation: string;
  status: 'pending' | 'investigating' | 'confirmed' | 'false_positive';
  
  // 조치 정보
  auto_blocked: boolean;
  manual_review_required: boolean;
  investigator_id?: number;
  resolution_notes?: string;
  resolved_at?: Date;
}

export interface ComplianceCheck {
  id: number;
  check_time: Date;
  entity_type: string;
  entity_id: string;
  
  // 체크 타입
  check_type: 'aml_screening' | 'kyc_verification' | 'sanctions_check' | 'pep_check';
  
  // 결과
  status: 'passed' | 'failed' | 'requires_review' | 'pending';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  confidence_score: number;
  
  // 상세 결과
  findings: Record<string, any>;
  external_references: string[];
  
  // 검토 정보
  reviewer_id?: number;
  review_notes?: string;
  approved_at?: Date;
}

export interface BlockchainAuditRecord {
  id: number;
  created_at: Date;
  
  // 블록체인 정보
  blockchain_network: string;
  transaction_hash: string;
  block_number: number;
  gas_used: number;
  
  // 감사 데이터
  audit_data_hash: string;
  merkle_root: string;
  previous_hash: string;
  
  // 검증 정보
  verification_status: 'pending' | 'verified' | 'failed';
  verification_nodes: string[];
}

// API 응답 타입
export interface AuditLogsResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

export interface SuspiciousActivitiesResponse {
  activities: SuspiciousActivity[];
  total: number;
  high_risk_count: number;
  pending_review_count: number;
}

export interface ComplianceMetrics {
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  pending_reviews: number;
  
  // 위험도별 분포
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  
  // 체크 타입별 통계
  check_type_stats: {
    aml_screening: number;
    kyc_verification: number;
    sanctions_check: number;
    pep_check: number;
  };
  
  // 최근 활동
  recent_activities: SuspiciousActivity[];
  compliance_score: number; // 0-100
  last_audit_date: string;
}

// 실시간 이벤트 타입
export interface RealtimeAuditEvent {
  type: 'audit_log' | 'suspicious_activity' | 'compliance_alert' | 'blockchain_verification';
  payload: AuditLog | SuspiciousActivity | ComplianceCheck | BlockchainAuditRecord;
  timestamp: Date;
}
