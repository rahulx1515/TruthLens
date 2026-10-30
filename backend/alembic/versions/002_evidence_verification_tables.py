"""evidence_verification_tables

Revision ID: 002_evidence_verification_tables
Revises: 001_initial_tables
Create Date: 2026-10-30 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_evidence_verification_tables'
down_revision: Union[str, None] = '001_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. verification_jobs table
    op.create_table(
        'verification_jobs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('headline', sa.String(length=500), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('is_code_mixed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('current_step', sa.String(length=100), nullable=False, server_default='Queued for verification'),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('overall_verdict', sa.String(length=50), nullable=True),
        sa.Column('overall_confidence', sa.Float(), nullable=True),
        sa.Column('report_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_jobs_id'), 'verification_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_verification_jobs_user_id'), 'verification_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_verification_jobs_status'), 'verification_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_verification_jobs_overall_verdict'), 'verification_jobs', ['overall_verdict'], unique=False)
    op.create_index(op.f('ix_verification_jobs_created_at'), 'verification_jobs', ['created_at'], unique=False)

    # 2. verification_claims table
    op.create_table(
        'verification_claims',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('claim_type', sa.String(length=50), nullable=False, server_default='factual'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('verdict', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('supporting_sources_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contradicting_sources_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('evaluations_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['verification_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_claims_id'), 'verification_claims', ['id'], unique=False)
    op.create_index(op.f('ix_verification_claims_job_id'), 'verification_claims', ['job_id'], unique=False)
    op.create_index(op.f('ix_verification_claims_verdict'), 'verification_claims', ['verdict'], unique=False)

    # 3. search_cache table
    op.create_table(
        'search_cache',
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('results_json', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('query_hash')
    )
    op.create_index(op.f('ix_search_cache_query_hash'), 'search_cache', ['query_hash'], unique=False)
    op.create_index(op.f('ix_search_cache_expires_at'), 'search_cache', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_table('search_cache')
    op.drop_table('verification_claims')
    op.drop_table('verification_jobs')

