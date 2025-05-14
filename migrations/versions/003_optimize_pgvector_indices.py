"""Optimize pgvector indices

Revision ID: 003
Revises: 002
Create Date: 2025-05-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First drop existing indices
    op.execute('DROP INDEX IF EXISTS documents_embedding_idx;')
    op.execute('DROP INDEX IF EXISTS document_hierarchy_embedding_idx;')
    op.execute('DROP INDEX IF EXISTS document_keywords_embedding_idx;')
    
    # Create optimized indices
    op.execute('''
    CREATE INDEX documents_embedding_idx 
    ON documents USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 128);
    ''')
    
    op.execute('''
    CREATE INDEX document_hierarchy_embedding_idx 
    ON document_hierarchy USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 128);
    ''')
    
    op.execute('''
    CREATE INDEX document_keywords_embedding_idx 
    ON document_keywords USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 128);
    ''')
    
    # Set the ef search parameter for each index
    op.execute('ALTER INDEX documents_embedding_idx SET (ef = 100);')
    op.execute('ALTER INDEX document_hierarchy_embedding_idx SET (ef = 100);')
    op.execute('ALTER INDEX document_keywords_embedding_idx SET (ef = 100);')


def downgrade() -> None:
    # Drop optimized indices
    op.execute('DROP INDEX IF EXISTS documents_embedding_idx;')
    op.execute('DROP INDEX IF EXISTS document_hierarchy_embedding_idx;')
    op.execute('DROP INDEX IF EXISTS document_keywords_embedding_idx;')
    
    # Create default indices
    op.execute('''
    CREATE INDEX documents_embedding_idx 
    ON documents USING hnsw (embedding vector_cosine_ops);
    ''')
    
    op.execute('''
    CREATE INDEX document_hierarchy_embedding_idx 
    ON document_hierarchy USING hnsw (embedding vector_cosine_ops);
    ''')
    
    op.execute('''
    CREATE INDEX document_keywords_embedding_idx 
    ON document_keywords USING hnsw (embedding vector_cosine_ops);
    ''')