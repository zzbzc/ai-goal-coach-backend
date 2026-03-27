"""数据库迁移初始版本"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 启用 UUID 扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])

    # 创建目标表
    op.create_table(
        'goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), default='🎯'),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('current_day', sa.Integer(), default=0),
        sa.Column('daily_time_available', sa.String(50)),
        sa.Column('experience_level', sa.String(20)),
        sa.Column('ai_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_goals_user_id', 'goals', ['user_id'])
    op.create_index('idx_goals_status', 'goals', ['status'])
    op.create_index('idx_goals_user_status', 'goals', ['user_id', 'status'])

    # 创建每日任务表
    op.create_table(
        'daily_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('goal_id', 'day_number', name='uq_goal_day'),
    )
    op.create_index('idx_daily_tasks_goal_id', 'daily_tasks', ['goal_id'])
    op.create_index('idx_daily_tasks_status', 'daily_tasks', ['status'])

    # 创建打卡记录表
    op.create_table(
        'checkins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('mood_rating', sa.Integer(), sa.CheckConstraint('mood_rating >= 1 AND mood_rating <= 5')),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('ai_suggestion', sa.Text(), nullable=True),
        sa.Column('streak_count', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('idx_checkins_user_id', 'checkins', ['user_id'])
    op.create_index('idx_checkins_goal_id', 'checkins', ['goal_id'])
    op.create_index('idx_checkins_created_at', 'checkins', ['created_at'])

    # 创建学习伙伴表
    op.create_table(
        'partners',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('partner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('idx_partners_user_id', 'partners', ['user_id'])

    # 创建挑战表
    op.create_table(
        'challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), default='🎯'),
        sa.Column('challenge_type', sa.String(50), default='streak'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('max_participants', sa.Integer(), default=100),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_challenges_status', 'challenges', ['status'])

    # 创建挑战参与者表
    op.create_table(
        'challenge_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('challenge_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('goals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('progress_score', sa.Integer(), default=0),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('idx_challenge_participants_challenge', 'challenge_participants', ['challenge_id'])
    op.create_index('idx_challenge_participants_user', 'challenge_participants', ['user_id'])


def downgrade() -> None:
    op.drop_table('challenge_participants')
    op.drop_table('challenges')
    op.drop_table('partners')
    op.drop_table('checkins')
    op.drop_table('daily_tasks')
    op.drop_table('goals')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
