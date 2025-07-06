"""add_super_admin_tables_and_partner_extensions

Revision ID: sa001
Revises: energy_pool_001
Create Date: 2025-07-06 08:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "sa001"
down_revision: Union[str, None] = "energy_pool_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """파트너 확장 및 슈퍼 어드민 기능을 위한 테이블 수정/추가"""
    
    # 1. partners 테이블이 이미 존재한다면 필드 추가, 없다면 새로 생성
    try:
        # partners 테이블 수정 - 새로운 필드들 추가
        op.add_column('partners', sa.Column('display_name', sa.String(100), comment='표시명'))
        op.add_column('partners', sa.Column('domain', sa.String(255), unique=True, comment='도메인'))
        op.add_column('partners', sa.Column('contact_phone', sa.String(50), comment='연락처 전화번호'))
        op.add_column('partners', sa.Column('business_type', sa.String(50), nullable=False, comment='비즈니스 유형'))
        
        # API 관리 필드들
        op.add_column('partners', sa.Column('api_key', sa.String(255), unique=True, nullable=False, comment='API 키'))
        op.add_column('partners', sa.Column('api_secret_hash', sa.String(255), nullable=False, comment='API 시크릿 해시'))
        op.add_column('partners', sa.Column('previous_api_key', sa.String(255), comment='이전 API 키'))
        op.add_column('partners', sa.Column('api_key_created_at', sa.DateTime(timezone=True), comment='API 키 생성일'))
        
        # 상태 관리 필드들
        op.add_column('partners', sa.Column('status', sa.String(20), default='pending', comment='파트너 상태'))
        op.add_column('partners', sa.Column('onboarding_status', sa.String(50), default='pending', comment='온보딩 상태'))
        
        # 구독 및 제한 필드들
        op.add_column('partners', sa.Column('subscription_plan', sa.String(50), default='basic', comment='구독 플랜'))
        op.add_column('partners', sa.Column('monthly_limit', sa.Numeric(18, 8), comment='월간 한도'))
        op.add_column('partners', sa.Column('commission_rate', sa.Numeric(5, 4), default=0, comment='수수료율'))
        
        # 에너지 관리 필드들
        op.add_column('partners', sa.Column('energy_balance', sa.Numeric(18, 8), default=0, comment='에너지 잔액'))
        
        # 설정 JSON 필드들
        op.add_column('partners', sa.Column('settings', sa.JSON, default={}, comment='파트너 설정'))
        op.add_column('partners', sa.Column('deployment_config', sa.JSON, default={}, comment='배포 설정'))
        
        # 활동 추적 필드들
        op.add_column('partners', sa.Column('last_activity_at', sa.DateTime(timezone=True), comment='마지막 활동 시간'))
        op.add_column('partners', sa.Column('activated_at', sa.DateTime(timezone=True), comment='활성화 시간'))
        op.add_column('partners', sa.Column('suspended_at', sa.DateTime(timezone=True), comment='정지 시간'))
        
    except Exception:
        # partners 테이블이 없다면 새로 생성
        op.create_table(
            'partners',
            sa.Column('id', sa.String(36), primary_key=True, index=True, comment='파트너 ID (UUID)'),
            sa.Column('name', sa.String(100), nullable=False, unique=True, comment='파트너사명'),
            sa.Column('display_name', sa.String(100), comment='표시명'),
            sa.Column('domain', sa.String(255), unique=True, comment='도메인'),
            sa.Column('contact_email', sa.String(255), nullable=False, unique=True, comment='연락처 이메일'),
            sa.Column('contact_phone', sa.String(50), comment='연락처 전화번호'),
            sa.Column('business_type', sa.String(50), nullable=False, comment='비즈니스 유형'),
            
            # API 관리
            sa.Column('api_key', sa.String(255), unique=True, nullable=False, comment='API 키'),
            sa.Column('api_secret_hash', sa.String(255), nullable=False, comment='API 시크릿 해시'),
            sa.Column('previous_api_key', sa.String(255), comment='이전 API 키'),
            sa.Column('api_key_created_at', sa.DateTime(timezone=True), comment='API 키 생성일'),
            
            # 상태 관리
            sa.Column('status', sa.String(20), default='pending', comment='파트너 상태'),
            sa.Column('onboarding_status', sa.String(50), default='pending', comment='온보딩 상태'),
            
            # 구독 및 제한
            sa.Column('subscription_plan', sa.String(50), default='basic', comment='구독 플랜'),
            sa.Column('monthly_limit', sa.Numeric(18, 8), comment='월간 한도'),
            sa.Column('commission_rate', sa.Numeric(5, 4), default=0, comment='수수료율'),
            
            # 에너지 관리
            sa.Column('energy_balance', sa.Numeric(18, 8), default=0, comment='에너지 잔액'),
            
            # 설정 (JSON)
            sa.Column('settings', sa.JSON, default={}, comment='파트너 설정'),
            sa.Column('deployment_config', sa.JSON, default={}, comment='배포 설정'),
            
            # 활동 추적
            sa.Column('last_activity_at', sa.DateTime(timezone=True), comment='마지막 활동 시간'),
            sa.Column('activated_at', sa.DateTime(timezone=True), comment='활성화 시간'),
            sa.Column('suspended_at', sa.DateTime(timezone=True), comment='정지 시간'),
            
            # 타임스탬프
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
        )

    # 2. 파트너 API 사용 이력 테이블 생성
    op.create_table(
        'partner_api_usage',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('endpoint', sa.String(255), nullable=False, comment='API 엔드포인트'),
        sa.Column('method', sa.String(10), nullable=False, comment='HTTP 메소드'),
        sa.Column('status_code', sa.Integer, nullable=False, comment='응답 상태 코드'),
        sa.Column('response_time', sa.Integer, comment='응답 시간 (ms)'),
        sa.Column('request_size', sa.BigInteger, comment='요청 크기 (bytes)'),
        sa.Column('response_size', sa.BigInteger, comment='응답 크기 (bytes)'),
        sa.Column('ip_address', sa.String(45), comment='클라이언트 IP 주소'),
        sa.Column('user_agent', sa.Text, comment='User Agent'),
        sa.Column('error_message', sa.Text, comment='오류 메시지'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.Index('idx_partner_api_usage_partner_created', 'partner_id', 'created_at'),
        sa.Index('idx_partner_api_usage_endpoint', 'endpoint'),
    )

    # 3. 파트너 통계 테이블 생성
    op.create_table(
        'partner_daily_statistics',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('stat_date', sa.Date, nullable=False, comment='통계 날짜'),
        sa.Column('total_transactions', sa.Integer, default=0, comment='총 거래 수'),
        sa.Column('total_volume', sa.Numeric(18, 8), default=0, comment='총 거래량'),
        sa.Column('total_fees', sa.Numeric(18, 8), default=0, comment='총 수수료'),
        sa.Column('api_calls', sa.Integer, default=0, comment='API 호출 수'),
        sa.Column('energy_consumed', sa.Numeric(18, 8), default=0, comment='소모된 에너지'),
        sa.Column('active_users', sa.Integer, default=0, comment='활성 사용자 수'),
        sa.Column('new_users', sa.Integer, default=0, comment='신규 사용자 수'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('partner_id', 'stat_date', name='uq_partner_daily_statistics_partner_date'),
        sa.Index('idx_partner_daily_statistics_date', 'stat_date'),
    )

    # 4. 시스템 모니터링 테이블 생성
    op.create_table(
        'system_monitoring',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('metric_name', sa.String(100), nullable=False, comment='메트릭 이름'),
        sa.Column('metric_value', sa.Numeric(18, 8), nullable=False, comment='메트릭 값'),
        sa.Column('metric_unit', sa.String(20), comment='메트릭 단위'),
        sa.Column('partner_id', sa.String(36), comment='파트너 ID (NULL이면 전체)'),
        sa.Column('node_id', sa.String(50), comment='노드 ID'),
        sa.Column('tags', sa.JSON, default={}, comment='추가 태그'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='측정 시각'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.Index('idx_system_monitoring_metric_timestamp', 'metric_name', 'timestamp'),
        sa.Index('idx_system_monitoring_partner', 'partner_id'),
    )

    # 5. 시스템 알림 테이블 생성
    op.create_table(
        'system_alerts',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('alert_type', sa.String(50), nullable=False, comment='알림 유형'),
        sa.Column('severity', sa.String(20), nullable=False, comment='심각도'),
        sa.Column('title', sa.String(255), nullable=False, comment='알림 제목'),
        sa.Column('message', sa.Text, nullable=False, comment='알림 메시지'),
        sa.Column('partner_id', sa.String(36), comment='관련 파트너 ID'),
        sa.Column('node_id', sa.String(50), comment='관련 노드 ID'),
        sa.Column('extra_data', sa.JSON, default={}, comment='추가 메타데이터'),
        sa.Column('is_resolved', sa.Boolean, default=False, comment='해결 여부'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), comment='해결 시간'),
        sa.Column('resolved_by', sa.String(255), comment='해결자'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.Index('idx_system_alerts_type_created', 'alert_type', 'created_at'),
        sa.Index('idx_system_alerts_severity', 'severity'),
        sa.Index('idx_system_alerts_resolved', 'is_resolved'),
    )

    # 6. 파트너 배포 이력 테이블 생성
    op.create_table(
        'partner_deployments',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('partner_id', sa.String(36), nullable=False, comment='파트너 ID'),
        sa.Column('deployment_type', sa.String(50), nullable=False, comment='배포 유형'),
        sa.Column('template_version', sa.String(20), comment='템플릿 버전'),
        sa.Column('instance_id', sa.String(100), comment='인스턴스 ID'),
        sa.Column('domain', sa.String(255), comment='배포된 도메인'),
        sa.Column('status', sa.String(50), nullable=False, comment='배포 상태'),
        sa.Column('config', sa.JSON, default={}, comment='배포 설정'),
        sa.Column('resources', sa.JSON, default={}, comment='리소스 정보'),
        sa.Column('logs', sa.Text, comment='배포 로그'),
        sa.Column('started_at', sa.DateTime(timezone=True), comment='배포 시작 시간'),
        sa.Column('completed_at', sa.DateTime(timezone=True), comment='배포 완료 시간'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.Index('idx_partner_deployments_partner_status', 'partner_id', 'status'),
        sa.Index('idx_partner_deployments_instance', 'instance_id'),
    )

    # 7. 슈퍼 어드민 사용자 테이블 생성
    op.create_table(
        'super_admin_users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, comment='사용자명'),
        sa.Column('email', sa.String(255), unique=True, nullable=False, comment='이메일'),
        sa.Column('hashed_password', sa.String(255), nullable=False, comment='해시된 비밀번호'),
        sa.Column('full_name', sa.String(100), comment='전체 이름'),
        sa.Column('role', sa.String(50), nullable=False, comment='역할'),
        sa.Column('permissions', sa.JSON, default=[], comment='권한 목록'),
        sa.Column('is_active', sa.Boolean, default=True, comment='활성 상태'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), comment='마지막 로그인'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), comment='수정일'),
    )

    # 8. 슈퍼 어드민 활동 로그 테이블 생성
    op.create_table(
        'super_admin_activity_logs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('admin_user_id', sa.Integer, nullable=False, comment='슈퍼 어드민 사용자 ID'),
        sa.Column('action', sa.String(100), nullable=False, comment='수행한 작업'),
        sa.Column('target_type', sa.String(50), comment='대상 유형'),
        sa.Column('target_id', sa.String(100), comment='대상 ID'),
        sa.Column('details', sa.JSON, default={}, comment='작업 세부사항'),
        sa.Column('ip_address', sa.String(45), comment='IP 주소'),
        sa.Column('user_agent', sa.Text, comment='User Agent'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='생성일'),
        sa.ForeignKeyConstraint(['admin_user_id'], ['super_admin_users.id'], ondelete='CASCADE'),
        sa.Index('idx_super_admin_activity_logs_admin_created', 'admin_user_id', 'created_at'),
        sa.Index('idx_super_admin_activity_logs_action', 'action'),
    )


def downgrade() -> None:
    """롤백 시 테이블 및 컬럼 삭제"""
    
    # 8. 슈퍼 어드민 활동 로그 테이블 삭제
    op.drop_table('super_admin_activity_logs')
    
    # 7. 슈퍼 어드민 사용자 테이블 삭제
    op.drop_table('super_admin_users')
    
    # 6. 파트너 배포 이력 테이블 삭제
    op.drop_table('partner_deployments')
    
    # 5. 시스템 알림 테이블 삭제
    op.drop_table('system_alerts')
    
    # 4. 시스템 모니터링 테이블 삭제
    op.drop_table('system_monitoring')
    
    # 3. 파트너 통계 테이블 삭제
    op.drop_table('partner_daily_statistics')
    
    # 2. 파트너 API 사용 이력 테이블 삭제
    op.drop_table('partner_api_usage')
    
    # 1. partners 테이블 확장 필드들 롤백 (기존 테이블이 있었다면)
    # 주의: 실제 운영에서는 데이터 손실을 방지하기 위해 신중하게 처리해야 합니다.
    try:
        op.drop_column('partners', 'suspended_at')
        op.drop_column('partners', 'activated_at') 
        op.drop_column('partners', 'last_activity_at')
        op.drop_column('partners', 'deployment_config')
        op.drop_column('partners', 'settings')
        op.drop_column('partners', 'energy_balance')
        op.drop_column('partners', 'commission_rate')
        op.drop_column('partners', 'monthly_limit')
        op.drop_column('partners', 'subscription_plan')
        op.drop_column('partners', 'onboarding_status')
        op.drop_column('partners', 'status')
        op.drop_column('partners', 'api_key_created_at')
        op.drop_column('partners', 'previous_api_key')
        op.drop_column('partners', 'api_secret_hash')
        op.drop_column('partners', 'api_key')
        op.drop_column('partners', 'business_type')
        op.drop_column('partners', 'contact_phone')
        op.drop_column('partners', 'domain')
        op.drop_column('partners', 'display_name')
    except Exception:
        # 새로 생성된 partners 테이블이었다면 완전히 삭제
        op.drop_table('partners')
