"""add_partner_energy_allocation_and_fee_revenue_tables

Revision ID: sa002
Revises: sa001
Create Date: 2025-07-06 08:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "sa002"
down_revision: Union[str, None] = "sa001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """파트너별 에너지 할당 및 수수료 매출 테이블 추가"""
    
    # 1. 파트너별 에너지 할당 테이블 생성
    op.create_table(
        'partner_energy_allocations',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('energy_pool_id', sa.Integer, nullable=False, comment='에너지 풀 ID'),
        sa.Column('allocated_amount', sa.Numeric(18, 8), nullable=False, comment='할당된 에너지 양'),
        sa.Column('used_amount', sa.Numeric(18, 8), default=0, comment='사용된 에너지 양'),
        sa.Column('reserved_amount', sa.Numeric(18, 8), default=0, comment='예약된 에너지 양'),
        sa.Column('priority', sa.Integer, default=1, comment='할당 우선순위'),
        sa.Column('allocation_type', sa.String(50), nullable=False, comment='할당 유형'),
        sa.Column('allocation_date', sa.Date, nullable=False, comment='할당 날짜'),
        sa.Column('expiry_date', sa.Date, comment='만료 날짜'),
        sa.Column('is_active', sa.Boolean, default=True, comment='활성 상태'),
        sa.Column('notes', sa.Text, comment='할당 메모'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['energy_pool_id'], ['energy_pools.id'], ondelete='CASCADE'),
        sa.Index('idx_partner_energy_allocations_partner_pool', 'partner_id', 'energy_pool_id'),
        sa.Index('idx_partner_energy_allocations_date', 'allocation_date'),
    )

    # 2. 파트너별 에너지 사용 이력 테이블 생성
    op.create_table(
        'partner_energy_usage_history',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('allocation_id', sa.Integer, nullable=False, comment='에너지 할당 ID'),
        sa.Column('transaction_hash', sa.String(64), comment='관련 거래 해시'),
        sa.Column('energy_amount', sa.Numeric(18, 8), nullable=False, comment='사용된 에너지 양'),
        sa.Column('energy_cost', sa.Numeric(18, 8), comment='에너지 비용'),
        sa.Column('usage_type', sa.String(50), nullable=False, comment='사용 유형'),
        sa.Column('wallet_address', sa.String(50), comment='사용된 지갑 주소'),
        sa.Column('gas_used', sa.BigInteger, comment='사용된 가스'),
        sa.Column('bandwidth_used', sa.BigInteger, comment='사용된 대역폭'),
        sa.Column('success', sa.Boolean, default=True, comment='사용 성공 여부'),
        sa.Column('error_message', sa.Text, comment='오류 메시지'),
        sa.Column('extra_data', sa.JSON, default={}, comment='추가 메타데이터'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['allocation_id'], ['partner_energy_allocations.id'], ondelete='CASCADE'),
        sa.Index('idx_partner_energy_usage_partner_created', 'partner_id', 'created_at'),
        sa.Index('idx_partner_energy_usage_allocation', 'allocation_id'),
        sa.Index('idx_partner_energy_usage_transaction', 'transaction_hash'),
    )

    # 3. 파트너별 수수료 매출 테이블 생성
    op.create_table(
        'partner_fee_revenues',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('revenue_date', sa.Date, nullable=False, comment='매출 날짜'),
        sa.Column('transaction_type', sa.String(50), nullable=False, comment='거래 유형'),
        sa.Column('transaction_count', sa.Integer, default=0, comment='거래 건수'),
        sa.Column('total_volume', sa.Numeric(18, 8), default=0, comment='총 거래량'),
        sa.Column('base_fee_total', sa.Numeric(18, 8), default=0, comment='기본 수수료 합계'),
        sa.Column('percentage_fee_total', sa.Numeric(18, 8), default=0, comment='비율 수수료 합계'),
        sa.Column('total_fee_collected', sa.Numeric(18, 8), default=0, comment='총 수집된 수수료'),
        sa.Column('partner_commission', sa.Numeric(18, 8), default=0, comment='파트너 커미션'),
        sa.Column('platform_revenue', sa.Numeric(18, 8), default=0, comment='플랫폼 수익'),
        sa.Column('average_fee_rate', sa.Numeric(8, 6), comment='평균 수수료율'),
        sa.Column('settlement_status', sa.String(20), default='pending', comment='정산 상태'),
        sa.Column('settlement_date', sa.Date, comment='정산 날짜'),
        sa.Column('notes', sa.Text, comment='매출 메모'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('partner_id', 'revenue_date', 'transaction_type', name='uq_partner_fee_revenues'),
        sa.Index('idx_partner_fee_revenues_partner_date', 'partner_id', 'revenue_date'),
        sa.Index('idx_partner_fee_revenues_settlement', 'settlement_status'),
    )

    # 4. 파트너별 수수료 설정 이력 테이블 생성  
    op.create_table(
        'partner_fee_config_history',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('fee_config_id', sa.Integer, nullable=False, comment='수수료 설정 ID'),
        sa.Column('change_type', sa.String(20), nullable=False, comment='변경 유형'),
        sa.Column('old_values', sa.JSON, comment='이전 설정값'),
        sa.Column('new_values', sa.JSON, comment='새 설정값'),
        sa.Column('changed_by', sa.String(255), comment='변경자'),
        sa.Column('change_reason', sa.Text, comment='변경 사유'),
        sa.Column('effective_date', sa.DateTime(timezone=True), comment='적용 날짜'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fee_config_id'], ['fee_configs.id'], ondelete='CASCADE'),
        sa.Index('idx_partner_fee_config_history_partner', 'partner_id'),
        sa.Index('idx_partner_fee_config_history_config', 'fee_config_id'),
        sa.Index('idx_partner_fee_config_history_date', 'effective_date'),
    )

    # 5. 플랫폼 전체 매출 통계 테이블 생성
    op.create_table(
        'platform_revenue_statistics',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('stat_date', sa.Date, nullable=False, unique=True, comment='통계 날짜'),
        sa.Column('total_partners', sa.Integer, default=0, comment='총 파트너 수'),
        sa.Column('active_partners', sa.Integer, default=0, comment='활성 파트너 수'),
        sa.Column('total_transactions', sa.Integer, default=0, comment='총 거래 수'),
        sa.Column('total_volume', sa.Numeric(18, 8), default=0, comment='총 거래량'),
        sa.Column('total_fees_collected', sa.Numeric(18, 8), default=0, comment='총 수집된 수수료'),
        sa.Column('total_partner_commissions', sa.Numeric(18, 8), default=0, comment='총 파트너 커미션'),
        sa.Column('platform_revenue', sa.Numeric(18, 8), default=0, comment='플랫폼 순 수익'),
        sa.Column('energy_costs', sa.Numeric(18, 8), default=0, comment='에너지 비용'),
        sa.Column('operational_costs', sa.Numeric(18, 8), default=0, comment='운영 비용'),
        sa.Column('net_profit', sa.Numeric(18, 8), default=0, comment='순 이익'),
        sa.Column('average_fee_rate', sa.Numeric(8, 6), comment='평균 수수료율'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
        sa.Index('idx_platform_revenue_statistics_date', 'stat_date'),
    )

    # 6. 파트너 온보딩 단계 테이블 생성
    op.create_table(
        'partner_onboarding_steps',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('step_name', sa.String(100), nullable=False, comment='단계 이름'),
        sa.Column('step_order', sa.Integer, nullable=False, comment='단계 순서'),
        sa.Column('status', sa.String(20), default='pending', comment='단계 상태'),
        sa.Column('required', sa.Boolean, default=True, comment='필수 단계 여부'),
        sa.Column('completion_data', sa.JSON, default={}, comment='완료 데이터'),
        sa.Column('error_message', sa.Text, comment='오류 메시지'),
        sa.Column('started_at', sa.DateTime(timezone=True), comment='시작 시간'),
        sa.Column('completed_at', sa.DateTime(timezone=True), comment='완료 시간'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('partner_id', 'step_name', name='uq_partner_onboarding_steps'),
        sa.Index('idx_partner_onboarding_steps_partner_order', 'partner_id', 'step_order'),
        sa.Index('idx_partner_onboarding_steps_status', 'status'),
    )


def downgrade() -> None:
    """롤백 시 테이블 삭제"""
    
    # 6. 파트너 온보딩 단계 테이블 삭제
    op.drop_table('partner_onboarding_steps')
    
    # 5. 플랫폼 전체 매출 통계 테이블 삭제
    op.drop_table('platform_revenue_statistics')
    
    # 4. 파트너별 수수료 설정 이력 테이블 삭제
    op.drop_table('partner_fee_config_history')
    
    # 3. 파트너별 수수료 매출 테이블 삭제
    op.drop_table('partner_fee_revenues')
    
    # 2. 파트너별 에너지 사용 이력 테이블 삭제
    op.drop_table('partner_energy_usage_history')
    
    # 1. 파트너별 에너지 할당 테이블 삭제
    op.drop_table('partner_energy_allocations')
