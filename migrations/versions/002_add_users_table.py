"""Add users table

Revision ID: 002
Revises: 001
Create Date: 2025-05-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.Text(), nullable=False, unique=True),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('full_name', sa.Text(), nullable=True),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('disabled', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('scopes', sa.ARRAY(sa.Text()), server_default="{'documents:read', 'tasks:read'}")
    )


def downgrade() -> None:
    # Drop users table
    op.drop_table('users')