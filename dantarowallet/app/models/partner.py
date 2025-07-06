"""파트너사 관련 모델"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, JSON, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Partner(Base):
    """파트너사 테이블"""
    __tablename__ = "partners"
    
    id = Column(String(36), primary_key=True, index=True, comment="파트너 ID (UUID)")
    name = Column(String(100), nullable=False, unique=True, comment="파트너사명")
    display_name = Column(String(100), comment="표시명")
    domain = Column(String(255), unique=True, comment="도메인")
    contact_email = Column(String(255), nullable=False, unique=True, comment="연락처 이메일")
    contact_phone = Column(String(50), comment="연락처 전화번호")
    business_type = Column(String(50), nullable=False, comment="비즈니스 유형")
    
    # API 관리
    api_key = Column(String(255), unique=True, nullable=False, comment="API 키")
    api_secret_hash = Column(String(255), nullable=False, comment="API 시크릿 해시")
    previous_api_key = Column(String(255), comment="이전 API 키")
    api_key_created_at = Column(DateTime(timezone=True), comment="API 키 생성일")
    
    # 상태 관리
    status = Column(String(20), default="pending", comment="파트너 상태")
    onboarding_status = Column(String(50), default="pending", comment="온보딩 상태")
    
    # 구독 및 제한
    subscription_plan = Column(String(50), default="basic", comment="구독 플랜")
    monthly_limit = Column(Numeric(18, 8), comment="월간 한도")
    commission_rate = Column(Numeric(5, 4), default=0, comment="수수료율")
    
    # 에너지 관리
    energy_balance = Column(Numeric(18, 8), default=0, comment="에너지 잔액")
    
    # 설정 (JSON)
    settings = Column(JSON, default={}, comment="파트너 설정")
    deployment_config = Column(JSON, default={}, comment="배포 설정")
    
    # 활동 추적
    last_activity_at = Column(DateTime(timezone=True), comment="마지막 활동 시간")
    activated_at = Column(DateTime(timezone=True), comment="활성화 시간")
    suspended_at = Column(DateTime(timezone=True), comment="정지 시간")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
    
    # 관계 설정
    users = relationship("PartnerUser", back_populates="partner")
    fee_configs = relationship("FeeConfig", foreign_keys="FeeConfig.partner_id")


class PartnerUser(Base):
    """파트너-사용자 매핑 테이블"""
    __tablename__ = "partner_users"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, comment="파트너사 ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID")
    partner_user_id = Column(String(255), comment="파트너사 내부 사용자 ID")
    
    # 파트너별 사용자 설정
    custom_data = Column(Text, comment="파트너별 커스텀 데이터 (JSON)")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="users")
    user = relationship("User")


class PartnerAPILog(Base):
    """파트너 API 호출 로그 테이블"""
    __tablename__ = "partner_api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, comment="파트너사 ID")
    
    # API 호출 정보
    endpoint = Column(String(255), nullable=False, comment="호출된 엔드포인트")
    method = Column(String(10), nullable=False, comment="HTTP 메서드")
    request_data = Column(Text, comment="요청 데이터 (JSON)")
    response_data = Column(Text, comment="응답 데이터 (JSON)")
    
    # 응답 정보
    status_code = Column(Integer, comment="응답 상태 코드")
    response_time_ms = Column(Integer, comment="응답 시간 (밀리초)")
    
    # 메타데이터
    ip_address = Column(String(45), comment="요청 IP 주소")
    user_agent = Column(String(500), comment="User Agent")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PartnerStatistics(Base):
    """파트너 통계 테이블"""
    __tablename__ = "partner_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, comment="파트너사 ID")
    date = Column(DateTime(timezone=True), nullable=False, comment="통계 날짜")
    
    # 사용자 통계
    total_users = Column(Integer, default=0, comment="총 사용자 수")
    active_users = Column(Integer, default=0, comment="활성 사용자 수")
    new_users = Column(Integer, default=0, comment="신규 사용자 수")
    
    # 거래 통계
    total_transactions = Column(Integer, default=0, comment="총 거래 수")
    transaction_volume = Column(Numeric(18, 8), default=0, comment="거래량")
    fee_collected = Column(Numeric(18, 8), default=0, comment="수수료 수집액")
    
    # API 사용 통계
    api_calls = Column(Integer, default=0, comment="API 호출 수")
    api_errors = Column(Integer, default=0, comment="API 오류 수")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PartnerWebhook(Base):
    """파트너 웹훅 설정 테이블"""
    __tablename__ = "partner_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, comment="파트너사 ID")
    
    # 웹훅 설정
    event_type = Column(String(50), nullable=False, comment="이벤트 유형")
    webhook_url = Column(String(500), nullable=False, comment="웹훅 URL")
    secret_key = Column(String(255), comment="웹훅 시크릿 키")
    
    # 설정
    is_active = Column(Boolean, default=True, comment="활성 상태")
    retry_count = Column(Integer, default=3, comment="재시도 횟수")
    timeout_seconds = Column(Integer, default=30, comment="타임아웃 (초)")
    
    # 통계
    success_count = Column(Integer, default=0, comment="성공 횟수")
    failure_count = Column(Integer, default=0, comment="실패 횟수")
    last_success_at = Column(DateTime(timezone=True), comment="마지막 성공 시간")
    last_failure_at = Column(DateTime(timezone=True), comment="마지막 실패 시간")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
