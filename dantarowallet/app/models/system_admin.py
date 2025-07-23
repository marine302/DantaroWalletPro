"""시스템 모니터링 및 관리 관련 모델"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class SystemMonitoring(Base):
    """시스템 모니터링 테이블"""

    __tablename__ = "system_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, comment="메트릭 이름")
    metric_value = Column(Numeric(18, 8), nullable=False, comment="메트릭 값")
    metric_unit = Column(String(20), comment="메트릭 단위")
    partner_id = Column(
        String(36),
        ForeignKey("partners.id", ondelete="CASCADE"),
        comment="파트너 ID (NULL이면 전체)",
    )
    node_id = Column(String(50), comment="노드 ID")
    tags = Column(JSON, default={}, comment="추가 태그")
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), comment="측정 시각"
    )

    # 관계
    partner = relationship("Partner")


class SystemAlert(Base):
    """시스템 알림 테이블"""

    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False, comment="알림 유형")
    severity = Column(String(20), nullable=False, comment="심각도")
    title = Column(String(255), nullable=False, comment="알림 제목")
    message = Column(Text, nullable=False, comment="알림 메시지")
    partner_id = Column(
        String(36),
        ForeignKey("partners.id", ondelete="CASCADE"),
        comment="관련 파트너 ID",
    )
    node_id = Column(String(50), comment="관련 노드 ID")
    extra_data = Column(JSON, default={}, comment="추가 메타데이터")
    is_resolved = Column(Boolean, default=False, comment="해결 여부")
    resolved_at = Column(DateTime(timezone=True), comment="해결 시간")
    resolved_by = Column(String(255), comment="해결자")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="생성일"
    )

    # 관계
    partner = relationship("Partner")


class SuperAdminUser(Base):
    """슈퍼 어드민 사용자 테이블"""

    __tablename__ = "super_admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, comment="사용자명")
    email = Column(String(255), unique=True, nullable=False, comment="이메일")
    hashed_password = Column(String(255), nullable=False, comment="해시된 비밀번호")
    full_name = Column(String(100), comment="전체 이름")
    role = Column(String(50), nullable=False, comment="역할")
    permissions = Column(JSON, default=[], comment="권한 목록")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    last_login_at = Column(DateTime(timezone=True), comment="마지막 로그인")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="생성일"
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")

    # 관계
    activity_logs = relationship("SuperAdminActivityLog", back_populates="admin_user")


class SuperAdminActivityLog(Base):
    """슈퍼 어드민 활동 로그 테이블"""

    __tablename__ = "super_admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(
        Integer,
        ForeignKey("super_admin_users.id", ondelete="CASCADE"),
        nullable=False,
        comment="슈퍼 어드민 사용자 ID",
    )
    action = Column(String(100), nullable=False, comment="수행한 작업")
    target_type = Column(String(50), comment="대상 유형")
    target_id = Column(String(100), comment="대상 ID")
    details = Column(JSON, default={}, comment="작업 세부사항")
    ip_address = Column(String(45), comment="IP 주소")
    user_agent = Column(Text, comment="User Agent")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="생성일"
    )

    # 관계
    admin_user = relationship("SuperAdminUser", back_populates="activity_logs")


class PlatformRevenueStatistics(Base):
    """플랫폼 전체 매출 통계 테이블"""

    __tablename__ = "platform_revenue_statistics"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False, unique=True, comment="통계 날짜")
    total_partners = Column(Integer, default=0, comment="총 파트너 수")
    active_partners = Column(Integer, default=0, comment="활성 파트너 수")
    total_transactions = Column(Integer, default=0, comment="총 거래 수")
    total_volume = Column(Numeric(18, 8), default=0, comment="총 거래량")
    total_fees_collected = Column(Numeric(18, 8), default=0, comment="총 수집된 수수료")
    total_partner_commissions = Column(
        Numeric(18, 8), default=0, comment="총 파트너 커미션"
    )
    platform_revenue = Column(Numeric(18, 8), default=0, comment="플랫폼 순 수익")
    energy_costs = Column(Numeric(18, 8), default=0, comment="에너지 비용")
    operational_costs = Column(Numeric(18, 8), default=0, comment="운영 비용")
    net_profit = Column(Numeric(18, 8), default=0, comment="순 이익")
    average_fee_rate = Column(Numeric(8, 6), comment="평균 수수료율")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="생성일"
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
