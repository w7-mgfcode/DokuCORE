"""Add document approval

Revision ID: 004
Revises: 003
Create Date: 2025-05-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document_approval table
    op.create_table(
        'document_approval',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('requested_by', sa.String(100), nullable=False),
        sa.Column('requested_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True)
    )
    
    # Add index for document_id and version
    op.create_index(
        'ix_document_approval_document_id_version',
        'document_approval',
        ['document_id', 'version']
    )
    
    # Add an approval_status column to the documents table
    op.add_column(
        'documents',
        sa.Column('approval_status', sa.String(20), server_default='draft', nullable=False)
    )
    
    # Add an approved_version column to the documents table
    op.add_column(
        'documents',
        sa.Column('approved_version', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    # Drop document_approval table
    op.drop_index('ix_document_approval_document_id_version')
    op.drop_table('document_approval')
    
    # Remove columns from documents table
    op.drop_column('documents', 'approval_status')
    op.drop_column('documents', 'approved_version')