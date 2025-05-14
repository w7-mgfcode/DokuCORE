"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-05-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the vector extension if it doesn't exist
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        # For the vector column, we need to use raw SQL
        sa.Column('embedding', sa.Text()),  # This will be altered below
        sa.Column('last_modified', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), default=1)
    )
    # Alter the embedding column to the vector type
    op.execute('ALTER TABLE documents ALTER COLUMN embedding TYPE vector(1536) USING NULL;')
    
    # Create document_history table
    op.create_table(
        'document_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id')),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('changed_by', sa.Text()),
        sa.Column('version', sa.Integer(), nullable=False)
    )
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('code_path', sa.Text(), nullable=True)
    )
    
    # Create document_hierarchy table
    op.create_table(
        'document_hierarchy',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id')),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('document_hierarchy.id'), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text()),  # This will be altered below
        sa.Column('doc_level', sa.Integer(), nullable=False),
        sa.Column('seq_num', sa.Integer(), nullable=False)
    )
    # Alter the embedding column to the vector type
    op.execute('ALTER TABLE document_hierarchy ALTER COLUMN embedding TYPE vector(1536) USING NULL;')
    
    # Create document_relationships table
    op.create_table(
        'document_relationships',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('document_hierarchy.id')),
        sa.Column('target_id', sa.Integer(), sa.ForeignKey('document_hierarchy.id')),
        sa.Column('relationship_type', sa.Text(), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False)
    )
    
    # Create document_keywords table
    op.create_table(
        'document_keywords',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('node_id', sa.Integer(), sa.ForeignKey('document_hierarchy.id')),
        sa.Column('keyword', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text()),  # This will be altered below
        sa.Column('importance', sa.Float(), nullable=False)
    )
    # Alter the embedding column to the vector type
    op.execute('ALTER TABLE document_keywords ALTER COLUMN embedding TYPE vector(1536) USING NULL;')
    
    # Create similarity search indices
    op.execute('CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);')
    op.execute('CREATE INDEX ON document_hierarchy USING hnsw (embedding vector_cosine_ops);')
    op.execute('CREATE INDEX ON document_keywords USING hnsw (embedding vector_cosine_ops);')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('document_keywords')
    op.drop_table('document_relationships')
    op.drop_table('document_hierarchy')
    op.drop_table('tasks')
    op.drop_table('document_history')
    op.drop_table('documents')
    
    # Drop the vector extension
    op.execute('DROP EXTENSION IF EXISTS vector;')