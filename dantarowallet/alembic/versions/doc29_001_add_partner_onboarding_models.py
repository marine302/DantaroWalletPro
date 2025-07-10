"""Add partner onboarding models for Doc #29

Revision ID: doc29_001
Revises: 93b2e4126195
Create Date: 2025-07-11 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'doc29_001'
down_revision: Union[str, None] = '93b2e4126195'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add partner onboarding tables"""
    
    # Partner Onboarding 메인 테이블
    op.create_table('partner_onboardings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('partner_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('current_step', sa.Integer(), nullable=False, default=1),
        sa.Column('total_steps', sa.Integer(), nullable=False, default=6),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('registration_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('account_setup_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('wallet_setup_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('system_config_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('deployment_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('testing_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('configuration_data', sa.JSON(), nullable=True),
        sa.Column('deployment_info', sa.JSON(), nullable=True),
        sa.Column('test_results', sa.JSON(), nullable=True),
        sa.Column('auto_proceed', sa.Boolean(), nullable=False, default=True),
        sa.Column('manual_approval_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('notification_email', sa.String(length=255), nullable=True),
        sa.Column('notification_webhook', sa.String(length=500), nullable=True),
        sa.Column('send_progress_updates', sa.Boolean(), nullable=False, default=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 인덱스 생성
    op.create_index('idx_partner_onboarding_partner_id', 'partner_onboardings', ['partner_id'])
    op.create_index('idx_partner_onboarding_status', 'partner_onboardings', ['status'])
    
    # Onboarding Steps 테이블
    op.create_table('onboarding_steps',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('onboarding_id', sa.Integer(), sa.ForeignKey('partner_onboardings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(length=100), nullable=False),
        sa.Column('step_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('auto_executable', sa.Boolean(), nullable=False, default=True),
        sa.Column('manual_intervention_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 인덱스 생성
    op.create_index('idx_onboarding_step_onboarding_id', 'onboarding_steps', ['onboarding_id'])
    op.create_index('idx_onboarding_step_number', 'onboarding_steps', ['step_number'])
    
    # Onboarding Checklist 테이블
    op.create_table('onboarding_checklists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('onboarding_id', sa.Integer(), sa.ForeignKey('partner_onboardings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=True),
        sa.Column('completed_by', sa.String(length=255), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('verification_status', sa.String(length=20), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('order_number', sa.Integer(), nullable=False, default=0),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 인덱스 생성
    op.create_index('idx_onboarding_checklist_onboarding_id', 'onboarding_checklists', ['onboarding_id'])
    op.create_index('idx_onboarding_checklist_category', 'onboarding_checklists', ['category'])
    
    # Onboarding Logs 테이블
    op.create_table('onboarding_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('onboarding_id', sa.Integer(), sa.ForeignKey('partner_onboardings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True)
    )
    
    # 인덱스 생성
    op.create_index('idx_onboarding_log_onboarding_id', 'onboarding_logs', ['onboarding_id'])
    op.create_index('idx_onboarding_log_level', 'onboarding_logs', ['level'])


def downgrade() -> None:
    """Remove partner onboarding tables"""
    op.drop_table('onboarding_logs')
    op.drop_table('onboarding_checklists')
    op.drop_table('onboarding_steps')
    op.drop_table('partner_onboardings')
