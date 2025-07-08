"""파트너 이력 및 통계 관련 모델"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, JSON, Date, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class PartnerApiUsage(Base):
    """파트너 API 사용 이력 테이블"""
    __tablename__ = "partner_api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    endpoint = Column(String(255), nullable=False, comment="API 엔드포인트")
    method = Column(String(10), nullable=False, comment="HTTP 메소드")
    status_code = Column(Integer, nullable=False, comment="응답 상태 코드")
    response_time = Column(Integer, comment="응답 시간 (ms)")
    request_size = Column(BigInteger, comment="요청 크기 (bytes)")
    response_size = Column(BigInteger, comment="응답 크기 (bytes)")
    ip_address = Column(String(45), comment="클라이언트 IP 주소")
    user_agent = Column(Text, comment="User Agent")
    error_message = Column(Text, comment="오류 메시지")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    
    # 관계
    partner = relationship("Partner", back_populates="api_usage_logs")


class PartnerDailyStatistics(Base):
    """파트너 일별 통계 테이블"""
    __tablename__ = "partner_daily_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    stat_date = Column(Date, nullable=False, comment="통계 날짜")
    total_transactions = Column(Integer, default=0, comment="총 거래 수")
    total_volume = Column(Numeric(18, 8), default=0, comment="총 거래량")
    total_fees = Column(Numeric(18, 8), default=0, comment="총 수수료")
    api_calls = Column(Integer, default=0, comment="API 호출 수")
    energy_consumed = Column(Numeric(18, 8), default=0, comment="소모된 에너지")
    active_users = Column(Integer, default=0, comment="활성 사용자 수")
    new_users = Column(Integer, default=0, comment="신규 사용자 수")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
    
    # 관계
    partner = relationship("Partner", back_populates="daily_statistics")


class PartnerEnergyAllocation(Base):
    """파트너별 에너지 할당 테이블"""
    __tablename__ = "partner_energy_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    energy_pool_id = Column(Integer, ForeignKey("energy_pools.id", ondelete="CASCADE"), nullable=False, comment="에너지 풀 ID")
    allocated_amount = Column(Numeric(18, 8), nullable=False, comment="할당된 에너지 양")
    used_amount = Column(Numeric(18, 8), default=0, comment="사용된 에너지 양")
    reserved_amount = Column(Numeric(18, 8), default=0, comment="예약된 에너지 양")
    priority = Column(Integer, default=1, comment="할당 우선순위")
    allocation_type = Column(String(50), nullable=False, comment="할당 유형")
    allocation_date = Column(Date, nullable=False, comment="할당 날짜")
    expiry_date = Column(Date, comment="만료 날짜")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    notes = Column(Text, comment="할당 메모")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
    
    # 관계
    partner = relationship("Partner", back_populates="energy_allocations")
    usage_history = relationship("PartnerEnergyUsageHistory", back_populates="allocation", cascade="all, delete-orphan")


class PartnerEnergyUsageHistory(Base):
    """파트너별 에너지 사용 이력 테이블"""
    __tablename__ = "partner_energy_usage_history"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    allocation_id = Column(Integer, ForeignKey("partner_energy_allocations.id", ondelete="CASCADE"), nullable=False, comment="에너지 할당 ID")
    transaction_hash = Column(String(64), comment="관련 거래 해시")
    energy_amount = Column(Numeric(18, 8), nullable=False, comment="사용된 에너지 양")
    energy_cost = Column(Numeric(18, 8), comment="에너지 비용")
    usage_type = Column(String(50), nullable=False, comment="사용 유형")
    wallet_address = Column(String(50), comment="사용된 지갑 주소")
    gas_used = Column(BigInteger, comment="사용된 가스")
    bandwidth_used = Column(BigInteger, comment="사용된 대역폭")
    success = Column(Boolean, default=True, comment="사용 성공 여부")
    error_message = Column(Text, comment="오류 메시지")
    extra_data = Column(JSON, default={}, comment="추가 메타데이터")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    
    # 관계
    partner = relationship("Partner", back_populates="partner_energy_usage_history")
    allocation = relationship("PartnerEnergyAllocation", back_populates="usage_history")


class PartnerFeeRevenue(Base):
    """파트너별 수수료 매출 테이블"""
    __tablename__ = "partner_fee_revenues"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    revenue_date = Column(Date, nullable=False, comment="매출 날짜")
    transaction_type = Column(String(50), nullable=False, comment="거래 유형")
    transaction_count = Column(Integer, default=0, comment="거래 건수")
    total_volume = Column(Numeric(18, 8), default=0, comment="총 거래량")
    base_fee_total = Column(Numeric(18, 8), default=0, comment="기본 수수료 합계")
    percentage_fee_total = Column(Numeric(18, 8), default=0, comment="비율 수수료 합계")
    total_fee_collected = Column(Numeric(18, 8), default=0, comment="총 수집된 수수료")
    partner_commission = Column(Numeric(18, 8), default=0, comment="파트너 커미션")
    platform_revenue = Column(Numeric(18, 8), default=0, comment="플랫폼 수익")
    average_fee_rate = Column(Numeric(8, 6), comment="평균 수수료율")
    settlement_status = Column(String(20), default="pending", comment="정산 상태")
    settlement_date = Column(Date, comment="정산 날짜")
    notes = Column(Text, comment="매출 메모")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
    
    # 관계
    partner = relationship("Partner", back_populates="fee_revenues")


class PartnerFeeConfigHistory(Base):
    """파트너별 수수료 설정 이력 테이블"""
    __tablename__ = "partner_fee_config_history"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    fee_config_id = Column(Integer, ForeignKey("fee_configs.id", ondelete="CASCADE"), nullable=False, comment="수수료 설정 ID")
    change_type = Column(String(20), nullable=False, comment="변경 유형")
    old_values = Column(JSON, comment="이전 설정값")
    new_values = Column(JSON, comment="새 설정값")
    changed_by = Column(String(255), comment="변경자")
    change_reason = Column(Text, comment="변경 사유")
    effective_date = Column(DateTime(timezone=True), comment="적용 날짜")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    
    # 관계
    partner = relationship("Partner", back_populates="partner_fee_config_history")
    fee_config = relationship("FeeConfig", back_populates="partner_history")


class PartnerOnboardingStep(Base):
    """파트너 온보딩 단계 테이블"""
    __tablename__ = "partner_onboarding_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    step_name = Column(String(100), nullable=False, comment="단계 이름")
    step_order = Column(Integer, nullable=False, comment="단계 순서")
    status = Column(String(20), default="pending", comment="단계 상태")
    required = Column(Boolean, default=True, comment="필수 단계 여부")
    completion_data = Column(JSON, default={}, comment="완료 데이터")
    error_message = Column(Text, comment="오류 메시지")
    started_at = Column(DateTime(timezone=True), comment="시작 시간")
    completed_at = Column(DateTime(timezone=True), comment="완료 시간")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
    
    # 관계
    partner = relationship("Partner", back_populates="onboarding_steps")


class PartnerDeployment(Base):
    """파트너 배포 이력 테이블"""
    __tablename__ = "partner_deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, comment="파트너 ID")
    deployment_type = Column(String(50), nullable=False, comment="배포 유형")
    template_version = Column(String(20), comment="템플릿 버전")
    instance_id = Column(String(100), comment="인스턴스 ID")
    domain = Column(String(255), comment="배포된 도메인")
    status = Column(String(50), nullable=False, comment="배포 상태")
    config = Column(JSON, default={}, comment="배포 설정")
    resources = Column(JSON, default={}, comment="리소스 정보")
    logs = Column(Text, comment="배포 로그")
    started_at = Column(DateTime(timezone=True), comment="배포 시작 시간")
    completed_at = Column(DateTime(timezone=True), comment="배포 완료 시간")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    
    # 관계
    partner = relationship("Partner", back_populates="deployments")
