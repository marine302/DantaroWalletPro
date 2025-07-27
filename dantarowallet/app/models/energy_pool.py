"""
본사 에너지 풀 관리 모델
트론 에너지 대납서비스 기능 명세서 4.5절 멀티 에너지 공급원 관리 구현
"""

from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, Enum, Text, JSON
from sqlalchemy.sql import func
from app.models.base import BaseModel
import enum

class EnergySourceType(enum.Enum):
    """에너지 공급원 타입"""
    SELF_STAKING = "self_staking"    # 자체 스테이킹 (우선순위 1)
    TRONZAP = "tronzap"              # 외부 공급사 TronZap (우선순위 2)
    TRONNRG = "tronnrg"              # 외부 공급사 TronNRG (우선순위 3)

class EnergySourceStatus(enum.Enum):
    """에너지 공급원 상태"""
    ACTIVE = "active"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"

class EnergyPool(BaseModel):
    """
    에너지 공급원 관리 테이블
    문서 4.5절 멀티 에너지 공급원 관리에 따른 구현
    """

    source_type = Column(Enum(EnergySourceType), nullable=False, comment="공급원 타입")
    priority = Column(Integer, nullable=False, comment="우선순위 (1=최우선)")
    
    # 스테이킹 관련 필드
    wallet_address = Column(String(64), comment="스테이킹 지갑 주소 (자체 스테이킹용)")
    total_staked_trx = Column(Numeric(precision=20, scale=6), default=0, comment="총 스테이킹 TRX")
    
    # 에너지 관련 필드
    available_energy = Column(Numeric(precision=20, scale=0), default=0, comment="사용 가능 에너지")
    allocated_energy = Column(Numeric(precision=20, scale=0), default=0, comment="할당된 에너지")
    daily_energy_generation = Column(Numeric(precision=20, scale=0), default=0, comment="일일 에너지 생성량")
    
    # 비용 및 조건
    cost_per_energy = Column(Numeric(precision=10, scale=8), nullable=False, comment="에너지당 비용 (TRX)")
    min_order = Column(Numeric(precision=20, scale=0), default=0, comment="최소 주문량")
    
    # 상태 관리
    status = Column(Enum(EnergySourceStatus), default=EnergySourceStatus.ACTIVE, comment="공급원 상태")
    api_endpoint = Column(String(255), comment="외부 API 엔드포인트")
    api_key_hash = Column(String(255), comment="API 키 해시")
    
    # 성능 지표
    roi_percentage = Column(Numeric(precision=5, scale=2), comment="ROI 퍼센티지 (자체 스테이킹용)")
    last_health_check = Column(DateTime(timezone=True), comment="마지막 상태 확인")
    response_time_ms = Column(Integer, comment="응답 시간 (밀리초)")
    
    # 설정 및 메타데이터
    config = Column(JSON, comment="공급원별 설정 정보")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    memo = Column(Text, comment="비고")

    def __repr__(self):
        return f"<EnergyPool {self.source_type.value} priority:{self.priority} energy:{self.available_energy}>"

class EnergyRequest(BaseModel):
    """
    에너지 요청 관리 테이블
    문서 4.1절 에너지 계산 API 및 4.2절 에너지 충전 프로세스 구현
    """
    
    partner_id = Column(String(36), nullable=False, comment="파트너 ID")
    request_id = Column(String(64), nullable=False, unique=True, comment="요청 ID")
    
    # 요청 정보
    total_energy_required = Column(Numeric(precision=20, scale=0), nullable=False, comment="필요 총 에너지")
    withdrawal_requests = Column(JSON, nullable=False, comment="출금 요청 목록")
    batch_mode = Column(Boolean, default=False, comment="배치 모드 여부")
    
    # 비용 계산
    base_cost_trx = Column(Numeric(precision=10, scale=6), nullable=False, comment="기본 비용 (TRX)")
    margin_trx = Column(Numeric(precision=10, scale=6), nullable=False, comment="마진 (TRX)")
    saas_fee_trx = Column(Numeric(precision=10, scale=6), nullable=False, comment="SaaS 수수료 (TRX)")
    total_cost_trx = Column(Numeric(precision=10, scale=6), nullable=False, comment="총 비용 (TRX)")
    energy_price = Column(Numeric(precision=10, scale=8), nullable=False, comment="에너지 가격")
    fallback_burn_trx = Column(Numeric(precision=10, scale=6), comment="폴백 소각 TRX")
    
    # 처리 정보
    selected_source_type = Column(Enum(EnergySourceType), comment="선택된 공급원")
    target_address = Column(String(64), comment="타겟 주소 (파트너사 핫월렛)")
    
    # 트랜잭션 정보
    payment_tx_hash = Column(String(64), comment="TRX 송금 트랜잭션 해시")
    delegation_tx_hash = Column(String(64), comment="에너지 위임 트랜잭션 해시")
    delegated_energy = Column(Numeric(precision=20, scale=0), comment="실제 위임된 에너지")
    expires_at = Column(DateTime(timezone=True), comment="에너지 만료 시간")
    
    # 상태 관리
    status = Column(String(50), default="REQUESTED", comment="요청 상태")
    valid_until = Column(DateTime(timezone=True), nullable=False, comment="견적 유효 시간")
    
    # 폴백 정보
    fallback_mode = Column(Boolean, default=False, comment="파트너사 직접 처리 모드")
    actual_burned_trx = Column(Numeric(precision=10, scale=6), comment="실제 소각된 TRX")
    
    def __repr__(self):
        return f"<EnergyRequest {self.request_id} {self.partner_id} {self.status}>"

class StakingOperation(BaseModel):
    """
    스테이킹 운영 관리 테이블
    문서 3.8절 본사 스테이킹 프로세스 및 4.6절 자체 스테이킹 관리 구현
    """
    
    operation_id = Column(String(64), nullable=False, unique=True, comment="운영 ID")
    staking_wallet = Column(String(64), nullable=False, comment="스테이킹 지갑 주소")
    
    # 스테이킹 정보
    operation_type = Column(String(20), nullable=False, comment="운영 타입 (stake/unstake)")
    trx_amount = Column(Numeric(precision=20, scale=6), nullable=False, comment="TRX 금액")
    resource_type = Column(String(10), default="ENERGY", comment="리소스 타입")
    
    # 재투자 전략
    monthly_revenue = Column(Numeric(precision=20, scale=6), comment="월간 수익")
    reinvestment_ratio = Column(Numeric(precision=3, scale=2), default=0.5, comment="재투자 비율")
    target_self_supply_ratio = Column(Numeric(precision=3, scale=2), comment="목표 자체 공급 비율")
    
    # 트랜잭션 정보
    tx_hash = Column(String(64), comment="트랜잭션 해시")
    block_number = Column(Integer, comment="블록 번호")
    
    # 결과
    generated_energy = Column(Numeric(precision=20, scale=0), comment="생성된 에너지")
    status = Column(String(20), default="PENDING", comment="운영 상태")
    
    def __repr__(self):
        return f"<StakingOperation {self.operation_id} {self.operation_type} {self.trx_amount}>"
