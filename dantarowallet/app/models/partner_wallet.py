"""파트너사 외부 지갑 관련 모델"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum


class WalletType(enum.Enum):
    """지갑 유형"""
    TRONLINK = "tronlink"
    LEDGER = "ledger"
    WALLET_CONNECT = "wallet_connect"
    INTERNAL = "internal"  # 시스템 내부 지갑 (기존)


class WalletPurpose(enum.Enum):
    """지갑 용도"""
    HOT = "hot"  # 실시간 출금용
    COLD = "cold"  # 대량 보관용
    SWEEP_DESTINATION = "sweep_destination"  # Sweep 목적지
    FEE = "fee"  # 수수료 지불용


class TransactionStatus(enum.Enum):
    """트랜잭션 상태"""
    PENDING = "pending"
    SIGNED = "signed"
    BROADCASTED = "broadcasted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REJECTED = "rejected"


class PartnerWallet(Base):
    """파트너사 외부 지갑 테이블"""
    __tablename__ = "partner_wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, comment="파트너사 ID")
    wallet_type = Column(Enum(WalletType), nullable=False, comment="지갑 유형")
    wallet_address = Column(String(42), nullable=False, unique=True, comment="지갑 주소")
    wallet_name = Column(String(100), comment="지갑 별칭")
    is_primary = Column(Boolean, default=False, comment="주 지갑 여부")
    purpose = Column(Enum(WalletPurpose), nullable=False, comment="지갑 용도")
    
    # 연결 정보
    connection_metadata = Column(JSON, comment="연결 메타데이터")
    last_connected_at = Column(DateTime(timezone=True), comment="마지막 연결 시간")
    is_connected = Column(Boolean, default=False, comment="현재 연결 상태")
    
    # 권한 설정
    can_sign_withdrawal = Column(Boolean, default=True, comment="출금 서명 가능")
    can_sign_sweep = Column(Boolean, default=True, comment="Sweep 서명 가능")
    daily_limit = Column(Numeric(18, 6), comment="일일 한도")
    
    # 화이트리스트
    whitelist_addresses = Column(JSON, comment="허용된 출금 주소 목록")
    require_whitelist = Column(Boolean, default=False, comment="화이트리스트 필수 여부")
    
    # 활성화 상태
    is_active = Column(Boolean, default=True, comment="활성화 상태")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="wallets")
    transactions = relationship("WalletTransaction", back_populates="wallet")


class WalletTransaction(Base):
    """지갑 트랜잭션 요청 테이블"""
    __tablename__ = "wallet_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("partner_wallets.id"), nullable=False, comment="지갑 ID")
    transaction_type = Column(String(50), nullable=False, comment="트랜잭션 유형")
    
    # 트랜잭션 데이터
    from_address = Column(String(42), nullable=False, comment="발신 주소")
    to_address = Column(String(42), nullable=False, comment="수신 주소")
    amount = Column(Numeric(18, 6), nullable=False, comment="금액")
    token_address = Column(String(42), comment="토큰 컨트랙트 주소")
    
    # 서명 정보
    unsigned_tx = Column(JSON, comment="서명 전 트랜잭션")
    signed_tx = Column(JSON, comment="서명된 트랜잭션")
    tx_hash = Column(String(66), comment="트랜잭션 해시")
    
    # 상태 관리
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, comment="상태")
    sign_requested_at = Column(DateTime(timezone=True), comment="서명 요청 시간")
    signed_at = Column(DateTime(timezone=True), comment="서명 완료 시간")
    broadcasted_at = Column(DateTime(timezone=True), comment="브로드캐스트 시간")
    confirmed_at = Column(DateTime(timezone=True), comment="확인 시간")
    
    # 에러 처리
    error_message = Column(String(500), comment="에러 메시지")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")
    
    # 메타데이터
    gas_limit = Column(Integer, comment="가스 한도")
    gas_price = Column(Numeric(18, 6), comment="가스 가격")
    nonce = Column(Integer, comment="논스")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    wallet = relationship("PartnerWallet", back_populates="transactions")
