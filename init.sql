-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Markdown documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Document change history
CREATE TABLE document_history (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT,
    version INTEGER NOT NULL
);

-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    document_id INTEGER REFERENCES documents(id),
    code_path TEXT
);

-- Hierarchical document index table
CREATE TABLE document_hierarchy (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    parent_id INTEGER REFERENCES document_hierarchy(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    doc_level INTEGER NOT NULL,
    seq_num INTEGER NOT NULL
);

-- Document relationships table
CREATE TABLE document_relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES document_hierarchy(id),
    target_id INTEGER REFERENCES document_hierarchy(id),
    relationship_type TEXT NOT NULL,
    strength FLOAT NOT NULL
);

-- Keywords and connection points
CREATE TABLE document_keywords (
    id SERIAL PRIMARY KEY,
    node_id INTEGER REFERENCES document_hierarchy(id),
    keyword TEXT NOT NULL,
    embedding VECTOR(1536),
    importance FLOAT NOT NULL
);

-- Similarity search indices with optimized parameters
-- The HNSW algorithm parameters are optimized for better search performance:
-- m: Maximum number of connections per node (higher = more accuracy but slower build)
-- ef_construction: Size of the dynamic candidate list during index construction (higher = more accuracy but slower build)
-- ef: Size of the dynamic candidate list during search (higher = more accuracy but slower search)

-- Documents index
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 128);

-- Document hierarchy index
CREATE INDEX ON document_hierarchy USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);

-- Document keywords index
CREATE INDEX ON document_keywords USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);

-- Set the ef search parameter for each index
-- This affects search performance at query time
ALTER INDEX documents_embedding_idx SET (ef = 100);
ALTER INDEX document_hierarchy_embedding_idx SET (ef = 100);
ALTER INDEX document_keywords_embedding_idx SET (ef = 100);