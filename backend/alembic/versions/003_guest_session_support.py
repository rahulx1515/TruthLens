"""guest_session_support

Revision ID: 003_guest_session_support
Revises: 002_evidence_verification_tables
Create Date: 2026-10-30 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_guest_session_support'
down_revision: Union[str, None] = '002_evidence_verification_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add guest_session_id column to verification_jobs
    with op.batch_alter_table('verification_jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('guest_session_id', sa.String(length=64), nullable=True))
        batch_op.create_index('ix_verification_jobs_guest_session_id', ['guest_session_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('verification_jobs', schema=None) as batch_op:
        batch_op.drop_index('ix_verification_jobs_guest_session_id')
        batch_op.drop_column('guest_session_id')

