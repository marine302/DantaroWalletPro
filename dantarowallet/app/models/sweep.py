"""
HD Wallet 관리 관련 모델
TRON 네트워크 기반 HD Wallet 구조와 입금 주소 관리
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class HDWalletMaster(Base):
    """HD Wallet 마스터 정보
    
    파트너사별로 하나의 마스터 지갑을 생성하고 관리합니다.
    마스터 지갑에서 사용자별 입금 주소를 파생시킵니다.
    """
    __tablename__ = "hd_wallet_masters"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 암호화된 마스터 시드
    encrypted_seed = Column(String(500), nullable=False, comment="암호화된 마스터 시드")
    public_key = Column(String(130), nullable=False, comment="마스터 공개키")
    collection_address = Column(String(42), nullable=True, comment="마스터 수집 주소")  # 추가
    
    # 파생 정보
    derivation_path = Column(String(100), default="m/44'/195'/0'/0", comment="TRON 파생 경로")
    last_index = Column(Integer, default=0, comment="마지막 사용 인덱스")
    
    # 보안 설정
    encryption_method = Column(String(50), default="AES-256-GCM", comment="암호화 방식")
    key_version = Column(Integer, default=1, comment="키 버전")
    
    # 통계 정보
    total_addresses_generated = Column(Integer, default=0, comment="생성된 총 주소 수")
    total_sweep_amount = Column(Numeric(18, 6), default=0, comment="총 Sweep 금액")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    addresses = relationship("UserDepositAddress", back_populates="hd_wallet")
    partner = relationship("Partner")


class UserDepositAddress(Base):
    """사용자 입금 주소
    
    각 사용자가 입금에 사용할 고유한 TRON 주소입니다.
    HD Wallet에서 파생되며 Sweep 대상이 됩니다.
    """
    __tablename__ = "user_deposit_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    hd_wallet_id = Column(Integer, ForeignKey("hd_wallet_masters.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 주소 정보
    address = Column(String(42), nullable=False, unique=True, index=True, comment="TRON 입금 주소")
    derivation_index = Column(Integer, nullable=False, comment="HD Wallet 파생 인덱스")
    encrypted_private_key = Column(String(500), nullable=False, comment="암호화된 개인키")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    is_monitored = Column(Boolean, default=True, comment="모니터링 활성화")
    
    # 입금 통계
    total_received = Column(Numeric(18, 6), default=0, comment="총 입금액 (USDT)")
    total_swept = Column(Numeric(18, 6), default=0, comment="총 Sweep 금액")
    last_deposit_at = Column(DateTime(timezone=True), comment="마지막 입금 시간")
    last_sweep_at = Column(DateTime(timezone=True), comment="마지막 Sweep 시간")
    
    # 설정
    min_sweep_amount = Column(Numeric(18, 6), comment="최소 Sweep 금액 (개별 설정)")
    priority_level = Column(Integer, default=1, comment="우선순위 (1-10)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    hd_wallet = relationship("HDWalletMaster", back_populates="addresses")
    user = relationship("User")
    sweep_logs = relationship("SweepLog", back_populates="deposit_address")
    deposits = relationship("Deposit", foreign_keys="[Deposit.to_address]", 
                          primaryjoin="UserDepositAddress.address == Deposit.to_address")
    
    # 인덱스
    __table_args__ = (
        Index("idx_deposit_address_user", "user_id"),
        Index("idx_deposit_address_active", "is_active"),
        Index("idx_deposit_address_monitored", "is_monitored"),
    )


class SweepConfiguration(Base):
    """Sweep 설정
    
    파트너사별 Sweep 자동화 정책을 관리합니다.
    """
    __tablename__ = "sweep_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False, unique=True)
    
    # Sweep 대상 지갑
    destination_wallet_id = Column(Integer, ForeignKey("partner_wallets.id"), nullable=False)
    
    # 기본 설정
    is_enabled = Column(Boolean, default=True, comment="Sweep 활성화")
    auto_sweep_enabled = Column(Boolean, default=True, comment="자동 Sweep 활성화")
    min_sweep_amount = Column(Numeric(18, 6), default=10, comment="최소 Sweep 금액 (USDT)")
    max_sweep_amount = Column(Numeric(18, 6), comment="최대 Sweep 금액 (제한없으면 NULL)")
    
    # 스케줄 설정
    sweep_interval_minutes = Column(Integer, default=60, comment="Sweep 간격 (분)")
    immediate_threshold = Column(Numeric(18, 6), default=1000, comment="즉시 Sweep 임계값")
    daily_sweep_time = Column(String(5), comment="일일 Sweep 시간 (HH:MM)")
    
    # 가스비 설정
    max_gas_price_sun = Column(Numeric(20, 0), default=1000, comment="최대 가스비 (SUN)")
    gas_optimization_enabled = Column(Boolean, default=True, comment="가스비 최적화")
    gas_price_multiplier = Column(Numeric(3, 2), default=1.1, comment="가스비 승수")
    
    # 배치 설정
    batch_enabled = Column(Boolean, default=True, comment="배치 처리 활성화")
    max_batch_size = Column(Integer, default=20, comment="최대 배치 크기")
    batch_delay_seconds = Column(Integer, default=5, comment="배치 처리 간 지연 시간")
    
    # 리스크 관리
    daily_sweep_limit = Column(Numeric(18, 6), comment="일일 Sweep 한도")
    monthly_sweep_limit = Column(Numeric(18, 6), comment="월간 Sweep 한도")
    consecutive_failure_limit = Column(Integer, default=3, comment="연속 실패 제한")
    
    # 알림 설정
    notification_enabled = Column(Boolean, default=True, comment="알림 활성화")
    notification_channels = Column(JSON, comment="알림 채널 설정")
    success_notification = Column(Boolean, default=False, comment="성공 알림")
    failure_notification = Column(Boolean, default=True, comment="실패 알림")
    
    # 메타데이터
    last_sweep_at = Column(DateTime(timezone=True), comment="마지막 Sweep 실행 시간")
    total_sweeps = Column(Integer, default=0, comment="총 Sweep 횟수")
    total_sweep_amount = Column(Numeric(18, 6), default=0, comment="총 Sweep 금액")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner")
    destination_wallet = relationship("PartnerWallet")
    sweep_logs = relationship("SweepLog", back_populates="configuration")


class SweepLog(Base):
    """Sweep 실행 로그
    
    모든 Sweep 작업의 실행 내역을 추적합니다.
    """
    __tablename__ = "sweep_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    configuration_id = Column(Integer, ForeignKey("sweep_configurations.id"), nullable=False)
    deposit_address_id = Column(Integer, ForeignKey("user_deposit_addresses.id"), nullable=False)
    
    # Sweep 정보
    sweep_type = Column(String(20), default="auto", comment="Sweep 유형 (auto/manual/emergency)")
    sweep_amount = Column(Numeric(18, 6), nullable=False, comment="Sweep 금액 (USDT)")
    balance_before = Column(Numeric(18, 6), comment="Sweep 전 잔액")
    balance_after = Column(Numeric(18, 6), comment="Sweep 후 잔액")
    
    # 트랜잭션 정보
    tx_hash = Column(String(66), index=True, comment="트랜잭션 해시")
    from_address = Column(String(42), nullable=False, comment="출금 주소")
    to_address = Column(String(42), nullable=False, comment="입금 주소")
    
    # 가스 정보
    gas_limit = Column(Numeric(20, 0), comment="가스 한도")
    gas_used = Column(Numeric(20, 0), comment="사용된 가스")
    gas_price = Column(Numeric(20, 0), comment="가스 가격 (SUN)")
    gas_fee_trx = Column(Numeric(18, 6), comment="가스비 (TRX)")
    
    # 상태 관리
    status = Column(String(20), default="pending", comment="상태 (pending/confirmed/failed)")
    error_message = Column(String(1000), comment="에러 메시지")
    error_code = Column(String(50), comment="에러 코드")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")
    max_retries = Column(Integer, default=3, comment="최대 재시도 횟수")
    
    # 시간 정보
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), comment="확인 시간")
    failed_at = Column(DateTime(timezone=True), comment="실패 시간")
    next_retry_at = Column(DateTime(timezone=True), comment="다음 재시도 시간")
    
    # 메타데이터
    batch_id = Column(String(36), comment="배치 ID")
    priority = Column(Integer, default=1, comment="우선순위")
    notes = Column(String(500), comment="메모")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    configuration = relationship("SweepConfiguration", back_populates="sweep_logs")
    deposit_address = relationship("UserDepositAddress", back_populates="sweep_logs")
    
    # 인덱스
    __table_args__ = (
        Index("idx_sweep_log_status", "status"),
        Index("idx_sweep_log_batch", "batch_id"),
        Index("idx_sweep_log_retry", "status", "next_retry_at"),
        Index("idx_sweep_log_date", "initiated_at"),
    )


class SweepQueue(Base):
    """Sweep 대기열
    
    Sweep 대상 주소들을 우선순위별로 관리합니다.
    """
    __tablename__ = "sweep_queues"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_address_id = Column(Integer, ForeignKey("user_deposit_addresses.id"), nullable=False)
    
    # 큐 정보
    queue_type = Column(String(20), default="normal", comment="큐 유형 (normal/priority/emergency)")
    priority = Column(Integer, default=1, comment="우선순위 (1-10, 높을수록 우선)")
    expected_amount = Column(Numeric(18, 6), comment="예상 Sweep 금액")
    
    # 상태
    status = Column(String(20), default="queued", comment="상태 (queued/processing/completed/failed)")
    attempts = Column(Integer, default=0, comment="처리 시도 횟수")
    
    # 스케줄링
    scheduled_at = Column(DateTime(timezone=True), comment="예약 실행 시간")
    expires_at = Column(DateTime(timezone=True), comment="만료 시간")
    
    # 메타데이터
    reason = Column(String(200), comment="큐 등록 사유")
    queue_metadata = Column(JSON, comment="추가 메타데이터")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    deposit_address = relationship("UserDepositAddress")
    
    # 인덱스
    __table_args__ = (
        Index("idx_sweep_queue_status", "status"),
        Index("idx_sweep_queue_priority", "priority", "scheduled_at"),
        Index("idx_sweep_queue_type", "queue_type"),
    )
