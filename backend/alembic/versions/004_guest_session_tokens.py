"""add guest_sessions table

Revision ID: 004_guest_session_tokens
Revises: 003_guest_session_support
Create Date: 2026-10-31 00:32:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '004_guest_session_tokens'
down_revision = '003_guest_session_support'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'guest_sessions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('claim_secret_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_claimed', sa.Boolean(), nullable=False, default=False, server_default=sa.text('false')),
        sa.Column('claimed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False, default=0, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['claimed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guest_sessions_id'), 'guest_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_guest_sessions_expires_at'), 'guest_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_guest_sessions_is_claimed'), 'guest_sessions', ['is_claimed'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_guest_sessions_is_claimed'), table_name='guest_sessions')
    op.drop_index(op.f('ix_guest_sessions_expires_at'), table_name='guest_sessions')
    op.drop_index(op.f('ix_guest_sessions_id'), table_name='guest_sessions')
    op.drop_table('guest_sessions')

