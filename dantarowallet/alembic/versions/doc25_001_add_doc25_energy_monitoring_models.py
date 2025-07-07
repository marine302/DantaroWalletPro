"""add_doc25_energy_monitoring_models

Revision ID: doc25_001
Revises: tronlink_001
Create Date: 2025-07-08 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "doc25_001"
down_revision: Union[str, None] = "tronlink_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Doc #25: 에너지 풀 고급 관리 시스템 테이블 추가"""
    
    # 1. 파트너 에너지 풀 테이블 생성
    op.create_table(
        "partner_energy_pools",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partner_id", sa.Integer(), nullable=False, unique=True, comment="파트너사 ID"),
        sa.Column("wallet_address", sa.String(42), nullable=False, comment="모니터링 지갑 주소"),
        
        # 에너지 상태
        sa.Column("total_energy", sa.Numeric(20, 0), default=0, comment="총 에너지"),
        sa.Column("available_energy", sa.Numeric(20, 0), default=0, comment="사용 가능 에너지"),
        sa.Column("used_energy", sa.Numeric(20, 0), default=0, comment="사용된 에너지"),
        sa.Column("energy_limit", sa.Numeric(20, 0), default=0, comment="에너지 한도"),
        
        # 대역폭 상태
        sa.Column("total_bandwidth", sa.Numeric(20, 0), default=0, comment="총 대역폭"),
        sa.Column("available_bandwidth", sa.Numeric(20, 0), default=0, comment="사용 가능 대역폭"),
        
        # TRX 스테이킹 정보
        sa.Column("frozen_trx_amount", sa.Numeric(18, 6), default=0, comment="동결된 TRX"),
        sa.Column("frozen_for_energy", sa.Numeric(18, 6), default=0, comment="에너지용 동결 TRX"),
        sa.Column("frozen_for_bandwidth", sa.Numeric(18, 6), default=0, comment="대역폭용 동결 TRX"),
        
        # 상태 및 예측
        sa.Column("status", sa.String(20), default="sufficient", comment="현재 상태"),
        sa.Column("depletion_estimated_at", sa.DateTime(timezone=True), comment="예상 고갈 시간"),
        sa.Column("daily_average_usage", sa.Numeric(20, 0), default=0, comment="일평균 사용량"),
        sa.Column("peak_usage_hour", sa.Integer(), comment="피크 사용 시간"),
        
        # 임계값 설정
        sa.Column("warning_threshold", sa.Integer(), default=30, comment="경고 임계값 (%)"),
        sa.Column("critical_threshold", sa.Integer(), default=10, comment="위험 임계값 (%)"),
        sa.Column("auto_response_enabled", sa.Boolean(), default=True, comment="자동 대응 활성화"),
        
        # 메타데이터
        sa.Column("last_checked_at", sa.DateTime(timezone=True), comment="마지막 확인 시간"),
        sa.Column("last_alert_sent_at", sa.DateTime(timezone=True), comment="마지막 알림 시간"),
        sa.Column("metrics_history", sa.JSON(), comment="과거 지표 (최근 24시간)"),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        
        sa.Index("idx_partner_energy_pools_partner", "partner_id"),
        sa.Index("idx_partner_energy_pools_status", "status"),
    )
    
    # 2. 에너지 알림 테이블 생성  
    op.create_table(
        "energy_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("energy_pool_id", sa.Integer(), sa.ForeignKey("partner_energy_pools.id"), nullable=False, comment="에너지 풀 ID"),
        
        # 알림 정보
        sa.Column("alert_type", sa.String(50), nullable=False, comment="알림 유형"),
        sa.Column("severity", sa.String(20), nullable=False, comment="심각도"),
        sa.Column("title", sa.String(200), nullable=False, comment="알림 제목"),
        sa.Column("message", sa.Text(), nullable=False, comment="알림 메시지"),
        sa.Column("threshold_value", sa.Numeric(10, 2), comment="임계값"),
        sa.Column("current_value", sa.Numeric(10, 2), comment="현재값"),
        sa.Column("estimated_hours_remaining", sa.Integer(), comment="예상 잔여 시간"),
        
        # 알림 전송 정보
        sa.Column("sent_via", sa.JSON(), comment="전송 채널 (email, telegram, webhook)"),
        sa.Column("sent_to", sa.JSON(), comment="수신자 목록"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("acknowledged", sa.Boolean(), default=False, comment="확인 여부"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), comment="확인 시간"),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        sa.Index("idx_energy_alerts_pool", "energy_pool_id"),
        sa.Index("idx_energy_alerts_type", "alert_type"),
        sa.Index("idx_energy_alerts_severity", "severity"),
    )
    
    # 3. 파트너별 에너지 사용 로그 테이블 생성
    op.create_table(
        "partner_energy_usage_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("energy_pool_id", sa.Integer(), sa.ForeignKey("partner_energy_pools.id"), nullable=False, comment="에너지 풀 ID"),
        
        # 사용 정보
        sa.Column("transaction_type", sa.String(50), nullable=False, comment="트랜잭션 유형"),
        sa.Column("transaction_hash", sa.String(66), comment="트랜잭션 해시"),
        sa.Column("energy_consumed", sa.Numeric(20, 0), nullable=False, comment="소비된 에너지"),
        sa.Column("bandwidth_consumed", sa.Numeric(20, 0), default=0, comment="소비된 대역폭"),
        
        # 비용 정보
        sa.Column("energy_unit_price", sa.Numeric(10, 6), comment="에너지 단가 (TRX)"),
        sa.Column("total_cost", sa.Numeric(18, 6), comment="총 비용 (TRX)"),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        sa.Index("idx_partner_energy_usage_logs_pool", "energy_pool_id"),
        sa.Index("idx_partner_energy_usage_logs_type", "transaction_type"),
        sa.Index("idx_partner_energy_usage_logs_hash", "transaction_hash"),
    )
    
    # 4. 에너지 예측 데이터 테이블 생성
    op.create_table(
        "energy_predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("energy_pool_id", sa.Integer(), sa.ForeignKey("partner_energy_pools.id"), nullable=False, comment="에너지 풀 ID"),
        
        # 예측 정보
        sa.Column("prediction_date", sa.DateTime(timezone=True), nullable=False, comment="예측 날짜"),
        sa.Column("predicted_usage", sa.Numeric(20, 0), nullable=False, comment="예측 사용량"),
        sa.Column("predicted_depletion", sa.DateTime(timezone=True), comment="예측 고갈 시간"),
        sa.Column("confidence_score", sa.Numeric(5, 2), comment="신뢰도 점수 (0-100)"),
        
        # 예측 기반 데이터
        sa.Column("historical_pattern", sa.JSON(), comment="과거 패턴 데이터"),
        sa.Column("trend_factors", sa.JSON(), comment="트렌드 요인"),
        sa.Column("seasonal_adjustments", sa.JSON(), comment="계절성 조정"),
        
        # 예측 결과
        sa.Column("recommended_action", sa.String(100), comment="권장 조치"),
        sa.Column("action_priority", sa.String(20), comment="조치 우선순위"),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        sa.Index("idx_energy_predictions_pool", "energy_pool_id"),
        sa.Index("idx_energy_predictions_date", "prediction_date"),
    )


def downgrade() -> None:
    """Doc #25 테이블 삭제"""
    op.drop_table("energy_predictions")
    op.drop_table("partner_energy_usage_logs")
    op.drop_table("energy_alerts")
    op.drop_table("partner_energy_pools")
