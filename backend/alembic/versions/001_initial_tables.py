"""initial_tables

Revision ID: 001_initial_tables
Revises: 
Create Date: 2026-10-30 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('published_date', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_url'), 'articles', ['url'], unique=False)
    op.create_index(op.f('ix_articles_domain'), 'articles', ['domain'], unique=False)

    # 3. analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('prediction', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('prob_fake', sa.Float(), nullable=False),
        sa.Column('prob_real', sa.Float(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('processing_time_ms', sa.Float(), nullable=False),
        sa.Column('explanation_json', sa.Text(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_id'), 'analyses', ['id'], unique=False)
    op.create_index(op.f('ix_analyses_user_id'), 'analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_analyses_article_id'), 'analyses', ['article_id'], unique=False)
    op.create_index(op.f('ix_analyses_prediction'), 'analyses', ['prediction'], unique=False)
    op.create_index(op.f('ix_analyses_created_at'), 'analyses', ['created_at'], unique=False)

    # 4. model_versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('precision', sa.Float(), nullable=False),
        sa.Column('recall', sa.Float(), nullable=False),
        sa.Column('f1_score', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'], unique=False)
    op.create_index(op.f('ix_model_versions_name'), 'model_versions', ['name'], unique=True)


def downgrade() -> None:
    op.drop_table('model_versions')
    op.drop_table('analyses')
    op.drop_table('articles')
    op.drop_table('users')

