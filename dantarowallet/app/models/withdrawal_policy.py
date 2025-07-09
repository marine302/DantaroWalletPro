"""
파트너사 출금 정책 관리 모델 - Doc #28
파트너사별 유연한 출금 정책 및 자동화 규칙을 관리합니다.
"""
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, Text, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class WithdrawalPolicyType(str, Enum):
    """출금 정책 유형"""
    REALTIME = "realtime"      # 실시간 자동 처리
    BATCH_DAILY = "batch_daily"     # 일괄 처리 (일단위)
    BATCH_WEEKLY = "batch_weekly"   # 일괄 처리 (주단위)
    BATCH_MONTHLY = "batch_monthly" # 일괄 처리 (월단위)
    MANUAL = "manual"          # 수동 승인
    HYBRID = "hybrid"          # 혼합형 (금액별)


class ApprovalRuleType(str, Enum):
    """승인 규칙 유형"""
    AUTO_APPROVE = "auto_approve"    # 자동 승인
    WHITELIST_ONLY = "whitelist_only" # 화이트리스트만
    AMOUNT_LIMIT = "amount_limit"    # 금액 제한
    DAILY_LIMIT = "daily_limit"      # 일일 한도
    MANUAL_REVIEW = "manual_review"  # 수동 검토
    TWO_FACTOR = "two_factor"        # 2단계 인증


class BatchExecutionDay(str, Enum):
    """배치 실행 요일"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class PartnerWithdrawalPolicy(BaseModel):
    """파트너사 출금 정책"""
    
    # 파트너 정보
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 기본 정책 설정
    policy_type = Column(SQLEnum(WithdrawalPolicyType), nullable=False, default=WithdrawalPolicyType.HYBRID)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 자동 승인 설정
    auto_approve_enabled = Column(Boolean, nullable=False, default=False)
    auto_approve_max_amount = Column(Numeric(precision=28, scale=8), nullable=True)  # 자동 승인 최대 금액
    auto_approve_daily_limit = Column(Numeric(precision=28, scale=8), nullable=True)  # 일일 자동 승인 한도
    
    # 화이트리스트 설정
    whitelist_enabled = Column(Boolean, nullable=False, default=False)
    whitelist_only = Column(Boolean, nullable=False, default=False)  # 화이트리스트만 허용
    
    # 금액 제한
    min_withdrawal_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    max_withdrawal_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    daily_withdrawal_limit = Column(Numeric(precision=28, scale=8), nullable=True)
    monthly_withdrawal_limit = Column(Numeric(precision=28, scale=8), nullable=True)
    
    # 배치 처리 설정
    batch_enabled = Column(Boolean, nullable=False, default=False)
    batch_execution_time = Column(String(8), nullable=True)  # HH:MM:SS 형식
    batch_execution_days = Column(JSON, nullable=True)  # 실행 요일 리스트
    batch_min_count = Column(Integer, nullable=True, default=1)  # 최소 배치 개수
    batch_max_count = Column(Integer, nullable=True, default=100)  # 최대 배치 개수
    
    # TronLink 자동 서명 설정
    auto_sign_enabled = Column(Boolean, nullable=False, default=False)
    auto_sign_max_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    auto_sign_script_path = Column(String(500), nullable=True)  # 자동 서명 스크립트 경로
    
    # 수수료 최적화 설정
    fee_optimization_enabled = Column(Boolean, nullable=False, default=True)
    energy_cost_threshold = Column(Numeric(precision=28, scale=8), nullable=True)  # 에너지 비용 임계값
    optimal_batch_size = Column(Integer, nullable=True, default=20)  # 최적 배치 크기
    
    # 보안 설정
    two_factor_required = Column(Boolean, nullable=False, default=False)
    ip_whitelist_enabled = Column(Boolean, nullable=False, default=False)
    risk_score_threshold = Column(Integer, nullable=True, default=50)  # 위험 점수 임계값
    
    # 알림 설정
    notification_enabled = Column(Boolean, nullable=False, default=True)
    notification_webhook_url = Column(String(500), nullable=True)
    notification_email = Column(String(255), nullable=True)
    
    # 관계 설정
    partner = relationship("Partner", back_populates="withdrawal_policy")
    approval_rules = relationship("WithdrawalApprovalRule", back_populates="policy")
    whitelist_addresses = relationship("WithdrawalWhitelist", back_populates="policy")
    execution_logs = relationship("WithdrawalBatchLog", back_populates="policy")

    def __repr__(self) -> str:
        return f"<PartnerWithdrawalPolicy(partner_id={self.partner_id}, policy_type={self.policy_type})>"


class WithdrawalApprovalRule(BaseModel):
    """출금 승인 규칙"""
    
    # 정책 연결
    policy_id = Column(Integer, ForeignKey("partner_withdrawal_policies.id"), nullable=False)
    
    # 규칙 설정
    rule_type = Column(SQLEnum(ApprovalRuleType), nullable=False)
    rule_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=1)  # 우선순위 (낮을수록 우선)
    
    # 조건 설정
    min_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    max_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    target_addresses = Column(JSON, nullable=True)  # 대상 주소 리스트
    time_restrictions = Column(JSON, nullable=True)  # 시간 제한 설정
    
    # 액션 설정
    action = Column(String(50), nullable=False)  # approve, reject, review, delay
    delay_minutes = Column(Integer, nullable=True)  # 지연 시간 (분)
    required_approvers = Column(Integer, nullable=True, default=1)  # 필요 승인자 수
    
    # 추가 설정
    conditions = Column(JSON, nullable=True)  # 복잡한 조건들
    metadata = Column(JSON, nullable=True)  # 추가 메타데이터
    
    # 관계 설정
    policy = relationship("PartnerWithdrawalPolicy", back_populates="approval_rules")

    def __repr__(self) -> str:
        return f"<WithdrawalApprovalRule(rule_type={self.rule_type}, rule_name={self.rule_name})>"


class WithdrawalWhitelist(BaseModel):
    """출금 화이트리스트"""
    
    # 정책 연결
    policy_id = Column(Integer, ForeignKey("partner_withdrawal_policies.id"), nullable=False)
    
    # 주소 정보
    address = Column(String(42), nullable=False)
    address_label = Column(String(100), nullable=True)  # 주소 라벨
    
    # 제한 설정
    max_daily_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    max_monthly_amount = Column(Numeric(precision=28, scale=8), nullable=True)
    
    # 상태 정보
    is_active = Column(Boolean, nullable=False, default=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 통계 정보
    total_withdrawn = Column(Numeric(precision=28, scale=8), nullable=False, default=0)
    withdrawal_count = Column(Integer, nullable=False, default=0)
    last_withdrawal_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관계 설정
    policy = relationship("PartnerWithdrawalPolicy", back_populates="whitelist_addresses")

    def __repr__(self) -> str:
        return f"<WithdrawalWhitelist(address={self.address}, label={self.address_label})>"


class WithdrawalBatchLog(BaseModel):
    """출금 배치 실행 로그"""
    
    # 정책 연결
    policy_id = Column(Integer, ForeignKey("partner_withdrawal_policies.id"), nullable=False)
    
    # 배치 정보
    batch_id = Column(String(36), nullable=False, unique=True)  # UUID
    batch_type = Column(String(50), nullable=False)  # manual, scheduled, triggered
    
    # 실행 정보
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 처리 결과
    total_requests = Column(Integer, nullable=False, default=0)
    processed_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    total_amount = Column(Numeric(precision=28, scale=8), nullable=False, default=0)
    total_fee = Column(Numeric(precision=28, scale=8), nullable=False, default=0)
    
    # 상태 및 결과
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    execution_details = Column(JSON, nullable=True)  # 상세 실행 정보
    
    # 관계 설정
    policy = relationship("PartnerWithdrawalPolicy", back_populates="execution_logs")

    def __repr__(self) -> str:
        return f"<WithdrawalBatchLog(batch_id={self.batch_id}, status={self.status})>"


class WithdrawalRiskScore(BaseModel):
    """출금 위험 점수"""
    
    # 출금 정보
    withdrawal_id = Column(Integer, ForeignKey("withdrawals.id"), nullable=False, unique=True)
    
    # 위험 점수
    total_score = Column(Integer, nullable=False, default=0)  # 총 위험 점수
    address_score = Column(Integer, nullable=False, default=0)  # 주소 위험 점수
    amount_score = Column(Integer, nullable=False, default=0)  # 금액 위험 점수
    frequency_score = Column(Integer, nullable=False, default=0)  # 빈도 위험 점수
    pattern_score = Column(Integer, nullable=False, default=0)  # 패턴 위험 점수
    
    # 위험 요소
    risk_factors = Column(JSON, nullable=True)  # 위험 요소들
    
    # 분석 결과
    risk_level = Column(String(20), nullable=False, default="low")  # low, medium, high, critical
    recommended_action = Column(String(50), nullable=False, default="approve")  # approve, review, reject
    
    # 분석 정보
    analyzed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    analyzer_version = Column(String(20), nullable=True)
    
    def __repr__(self) -> str:
        return f"<WithdrawalRiskScore(withdrawal_id={self.withdrawal_id}, total_score={self.total_score})>"


class WithdrawalBatch(BaseModel):
    """출금 배치"""
    
    # 파트너 정보
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False, index=True)
    
    # 배치 정보
    batch_type = Column(String(20), nullable=False, default="manual")  # manual, scheduled, auto
    total_count = Column(Integer, nullable=False, default=0)
    total_amount = Column(Numeric(precision=28, scale=8), nullable=False, default=0)
    total_fee = Column(Numeric(precision=28, scale=8), nullable=False, default=0)
    
    # 스케줄 정보
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 상태 정보
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    
    # 출금 ID들
    withdrawal_ids = Column(Text, nullable=False)  # JSON 배열 문자열
    
    # 실행 결과
    successful_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    
    # 트랜잭션 정보
    tx_hashes = Column(Text, nullable=True)  # JSON 배열 문자열
    total_gas_used = Column(Integer, nullable=True)
    total_energy_used = Column(Integer, nullable=True)
    
    def __repr__(self) -> str:
        return f"<WithdrawalBatch(partner_id={self.partner_id}, total_count={self.total_count}, status={self.status})>"


# 인덱스 설정
Index("idx_partner_withdrawal_policy_partner", PartnerWithdrawalPolicy.partner_id)
Index("idx_withdrawal_approval_rule_policy", WithdrawalApprovalRule.policy_id)
Index("idx_withdrawal_whitelist_policy_address", WithdrawalWhitelist.policy_id, WithdrawalWhitelist.address)
Index("idx_withdrawal_batch_log_policy_batch", WithdrawalBatchLog.policy_id, WithdrawalBatchLog.batch_id)
Index("idx_withdrawal_risk_score_withdrawal", WithdrawalRiskScore.withdrawal_id)
