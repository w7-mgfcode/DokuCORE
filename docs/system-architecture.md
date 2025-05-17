# DokuCORE System Architecture Documentation

## 1. Introduction

DokuCORE is an AI-supported documentation system designed to help maintain, search, and update documentation efficiently. The system leverages modern technologies like FastAPI, PostgreSQL with pgvector, and hierarchical indexing to enable large language models (LLMs) to efficiently search, update, and generate tasks for documentation maintenance.

This document provides a detailed overview of the system architecture, describing the key components, their interactions, and the underlying technologies.

## 2. System Overview

### 2.1. Key Features

DokuCORE offers a robust set of features for documentation management:

- **Semantic Understanding**: Hierarchical indexing for semantic understanding of content
- **Efficient Token Usage**: Only loads relevant document sections (70-95% token savings)
- **Enhanced Code Monitoring**: Detects code changes and suggests documentation updates
- **AI Integration**: MCP protocol for AI tools like ClaudeCode
- **Vector Search**: Semantic search using pgvector in PostgreSQL
- **Hierarchical Structure**: Maintains document relationships and context
- **Authentication & Authorization**: JWT token-based authentication with role-based access control
- **Document Versioning**: Complete version history for all documents
- **Approval Workflow**: Formal document approval process with status tracking
- **Responsive UI**: Modern React-based UI for document management
- **Health Monitoring**: Comprehensive health check endpoints for system monitoring
- **Advanced Vector Indices**: Fine-tuned pgvector HNSW indices for faster similarity search

### 2.2. High-Level Architecture

The system follows a modular architecture with the following main components:

1. **FastAPI MCP Server**: Provides REST API endpoints and MCP protocol integration
2. **PostgreSQL + pgvector Database**: Stores documents and vector embeddings
3. **Hierarchical Indexing Engine**: Creates semantic document indices
4. **Code Monitor Service**: Tracks code changes and generates documentation tasks
5. **Version History System**: Maintains document revisions
6. **Approval Workflow**: Manages document approval process
7. **React UI**: Web interface for document management

![High-Level Architecture](https://placeholder.com/high-level-architecture.png)

## 3. Component Architecture

### 3.1. API Server

The API server is built with FastAPI and serves as the central component of the system. It provides:

- REST API endpoints for document management
- MCP protocol integration for AI tools
- Business logic for document indexing, searching, and versioning

#### 3.1.1. Key Components

- **FastAPI Application**: The main application entry point (`main.py`)
- **MCP Tools**: Tools for AI integration via the Model Context Protocol (`mcp_tools.py`)
- **Routers**: API endpoint handlers organized by functionality
- **Services**: Business logic services for documents, tasks, search, and versioning
- **Models**: Data models and validators using Pydantic
- **Indexing Engine**: Components for hierarchical document indexing
- **Utilities**: Database connections, configuration, and helper functions

#### 3.1.2. API Endpoints

The API server provides the following endpoint groups:

- **/documents/**: Document management endpoints
- **/tasks/**: Task management endpoints
- **/search/**: Search functionality endpoints
- **/auth/**: Authentication and user management
- **/versions/**: Document versioning and approval
- **/visualization/**: Index visualization tools
- **/health/**: Health check endpoints

### 3.2. Database Schema

The system uses PostgreSQL with the pgvector extension for vector similarity search. The database schema includes:

#### 3.2.1. Core Tables

- **documents**: Stores document metadata and content
  - `id`: Primary key
  - `title`: Document title
  - `path`: Document path
  - `content`: Document content
  - `embedding`: Vector embedding of the document content
  - `last_modified`: Last modification timestamp
  - `version`: Document version number

- **document_history**: Tracks document version history
  - `id`: Primary key
  - `document_id`: Reference to documents table
  - `content`: Historical document content
  - `changed_at`: Timestamp of the change
  - `changed_by`: User who made the change
  - `version`: Version number of this historical entry

- **tasks**: Stores documentation tasks
  - `id`: Primary key
  - `title`: Task title
  - `description`: Task description
  - `status`: Task status (pending, in-progress, completed)
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp
  - `document_id`: Reference to documents table (optional)
  - `code_path`: Path to related code file (optional)

#### 3.2.2. Hierarchical Index Tables

- **document_hierarchy**: Stores hierarchical document structure
  - `id`: Primary key
  - `document_id`: Reference to documents table
  - `parent_id`: Reference to parent node (self-referential)
  - `title`: Section title
  - `content`: Section content
  - `embedding`: Vector embedding of the section
  - `doc_level`: Hierarchical level (h1, h2, h3, etc.)
  - `seq_num`: Sequence number for ordering

- **document_relationships**: Stores relationships between document sections
  - `id`: Primary key
  - `source_id`: Reference to source node
  - `target_id`: Reference to target node
  - `relationship_type`: Type of relationship (sibling, semantic)
  - `strength`: Relationship strength (0.0-1.0)

- **document_keywords**: Stores keywords extracted from document sections
  - `id`: Primary key
  - `node_id`: Reference to document_hierarchy table
  - `keyword`: Extracted keyword
  - `embedding`: Vector embedding of the keyword
  - `importance`: Keyword importance score (0.0-1.0)

#### 3.2.3. User Management Tables

- **users**: Stores user information
  - `id`: Primary key
  - `username`: Username
  - `email`: Email address
  - `hashed_password`: Hashed password
  - `full_name`: User's full name
  - `disabled`: User status flag
  - `scopes`: User permission scopes

#### 3.2.4. Approval Workflow Tables

- **document_approvals**: Stores document approval requests
  - `id`: Primary key
  - `document_id`: Reference to documents table
  - `version`: Document version to approve
  - `status`: Approval status (pending, approved, rejected)
  - `requested_by`: User who requested approval
  - `approved_by`: User who approved/rejected
  - `requested_at`: Request timestamp
  - `resolved_at`: Resolution timestamp
  - `comments`: Additional comments

### 3.3. Hierarchical Indexing Engine

The hierarchical indexing engine is a key component that enables semantic understanding of document content. It:

1. Parses Markdown documents into hierarchical sections
2. Generates vector embeddings for each section
3. Establishes relationships between sections
4. Extracts and indexes keywords

#### 3.3.1. Key Components

- **HierarchicalIndexer**: Main indexing component (`hierarchical_indexer.py`)
- **MarkdownParser**: Parses Markdown into hierarchical structure (`markdown_parser.py`)
- **KeywordExtractor**: Extracts keywords with importance scores (`keyword_extractor.py`)
- **HierarchicalSearch**: Performs multi-stage hierarchical search (`hierarchical_search.py`)
- **EmbeddingConfig**: Manages embedding model configuration (`embedding_config.py`)
- **RelationshipManager**: Handles relationship thresholds (`relationship_thresholds.py`)

#### 3.3.2. Indexing Process

1. **Document Parsing**:
   - Markdown content is parsed into hierarchical sections based on headers
   - Each section includes title, content, level, and sequence number

2. **Embedding Generation**:
   - Vector embeddings are generated for each section
   - Embeddings are normalized and optimized for search
   - Sentence Transformers models (e.g., all-MiniLM-L6-v2) are used

3. **Relationship Building**:
   - Parent-child relationships based on document structure
   - Sibling relationships between sections at the same level
   - Semantic relationships based on content similarity
   - Keyword-based relationships

4. **Keyword Extraction**:
   - Keywords are extracted from each section
   - Importance scores are calculated
   - Keywords are embedded for semantic search

### 3.4. Code Monitor Service

The code monitor service tracks changes in a Git repository and generates tasks for updating documentation. It:

1. Periodically checks for code changes
2. Identifies modified files that might require documentation updates
3. Creates tasks for updating related documentation

#### 3.4.1. Key Components

- **CodeMonitor**: Main monitoring component (`code_monitor.py`)
- **GitIntegration**: Interfaces with Git repositories
- **TaskGeneration**: Creates documentation update tasks

#### 3.4.2. Monitoring Process

1. **Repository Checking**:
   - Pulls latest changes from the Git repository
   - Identifies files modified since the last check

2. **Task Generation**:
   - For each modified file, checks if there is related documentation
   - Creates a task for updating the documentation
   - Assigns the task to relevant personnel (if applicable)

### 3.5. MCP Integration

The Model Context Protocol (MCP) integration allows AI tools like ClaudeCode to interact with the documentation system. It provides:

1. A standardized interface for AI tools
2. Tools for document retrieval, search, and update
3. Task management capabilities

#### 3.5.1. MCP Tools

The system provides the following MCP tools:

- **list_docs()**: List all available documents
- **get_doc_content(doc_id)**: Get document content
- **search_docs(query, limit=5)**: Search documentation
- **get_document_structure(doc_id)**: Get document structure
- **update_document(doc_id, new_content, changed_by="AI")**: Update document
- **create_task(title, description, doc_id=None, code_path=None)**: Create task
- **get_tasks(status=None)**: List tasks
- **get_document_versions(doc_id)**: Get document version history
- **get_document_version(doc_id, version)**: Get specific document version
- **restore_document_version(doc_id, version, user)**: Restore document to previous version
- **get_approval_requests(status=None)**: List document approval requests
- **get_approval_request(approval_id)**: Get specific approval request
- **create_approval_request(document_id, version, requested_by, comments=None)**: Create approval request
- **update_approval_request(approval_id, status, approved_by, comments=None)**: Approve or reject document

## 4. Data Flow

### 4.1. Document Creation and Indexing

1. A document is created via the API or uploaded through the UI
2. The document content is stored in the `documents` table
3. The hierarchical indexer parses the document into sections
4. Vector embeddings are generated for each section
5. Sections are stored in the `document_hierarchy` table
6. Relationships between sections are created
7. Keywords are extracted and stored in the `document_keywords` table

### 4.2. Document Search

1. A search query is received via the API or MCP
2. The query is embedded using the same model as the documents
3. A multi-stage search is performed:
   - Keyword search finds direct matches
   - Semantic search finds conceptually related content
   - Relationship expansion finds contextually related sections
4. Results are ranked by relevance
5. The most relevant sections are returned with document metadata

### 4.3. Code Change Monitoring

1. The code monitor service pulls the latest changes from the Git repository
2. Changed files are identified
3. For each changed file, the service:
   - Looks for related documentation
   - Creates a task for updating the documentation
   - Assigns the task to the appropriate team member
4. Task information is stored in the `tasks` table
5. Users can view and manage tasks through the UI

### 4.4. Document Update and Versioning

1. A document update is received via the API or MCP
2. The old version is stored in the `document_history` table
3. The document is updated in the `documents` table
4. The document version number is incremented
5. The hierarchical index is regenerated
6. If approval is required:
   - An approval request is created
   - The approval status is tracked
   - Once approved, the document is marked as "approved"

## 5. Technology Stack

### 5.1. Backend

- **FastAPI**: Web framework for building APIs
- **FastMCP**: MCP protocol integration for FastAPI
- **PostgreSQL**: Relational database
- **pgvector**: Vector similarity search extension for PostgreSQL
- **SentenceTransformers**: Neural network models for text embeddings
- **LlamaIndex**: Data framework for LLM applications
- **PyJWT**: JSON Web Token implementation in Python
- **Passlib**: Password hashing library for Python
- **Alembic**: Database migration tool for SQLAlchemy
- **pytest**: Testing framework for Python

### 5.2. Frontend

- **React**: JavaScript library for building user interfaces
- **Material-UI**: React UI framework
- **React Router**: Routing library for React
- **Axios**: Promise-based HTTP client
- **React Markdown**: Markdown parser and renderer for React

### 5.3. DevOps

- **Docker**: Containerization platform
- **Docker Compose**: Multi-container Docker applications
- **Git**: Version control system
- **Alembic**: Database migration tool

## 6. Deployment Architecture

### 6.1. Docker Containers

The system is deployed using Docker Compose with the following containers:

- **db**: PostgreSQL with pgvector extension
- **api**: FastAPI API server
- **code-monitor**: Code monitoring service
- **ui**: React UI (optional)

### 6.2. Configuration

Configuration is managed through environment variables defined in the `.env` file:

- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name
- `API_PORT`: Port for the API server
- `DATABASE_URL`: PostgreSQL connection string
- `REPO_PATH`: Path to the Git repository
- `API_URL`: URL of the API server
- `CHECK_INTERVAL`: Interval for checking code changes (in seconds)
- `EMBEDDING_MODEL`: Name of the SentenceTransformer model
- `EMBEDDING_DIM`: Dimension of the embeddings
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `JWT_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes

## 7. Security Considerations

### 7.1. Authentication and Authorization

- JWT token-based authentication
- Role-based access control with scopes
- Secure password hashing with bcrypt

### 7.2. API Security

- CORS middleware with configurable origins
- Input validation through Pydantic models
- Error handling that doesn't expose sensitive information
- Request logging with unique request IDs

## 8. Performance Considerations

### 8.1. Vector Search Optimization

- Optimized pgvector HNSW index parameters (m=16, ef_construction=128, ef=100)
- Normalized embeddings for consistent cosine similarity calculations
- Hybrid search approach combining keyword matching and vector similarity

### 8.2. Caching

- In-memory caching system for frequently accessed searches
- Search result caching with expiration
- Configurable cache size and expiration times

### 8.3. Token Efficiency

- Hierarchical indexing reduces token usage by 70-95%
- Document sections are loaded only as needed
- Relationship strength thresholds prevent noise in search results

## 9. Scalability Considerations

### 9.1. Database Scalability

- Optimized database queries for large document collections
- Connection pooling for handling multiple concurrent requests
- Index optimization for large vector collections

### 9.2. API Scalability

- Stateless API design for horizontal scaling
- Asynchronous handling of long-running operations
- Load balancing across multiple API instances (in production)

## 10. Monitoring and Maintenance

### 10.1. Health Checks

The system provides comprehensive health check endpoints:

- `/health`: Overall system status
- `/health/db`: Database connection status
- `/health/embedding`: Embedding model status

### 10.2. Logging

- Structured logging with severity levels
- Request ID tracking for request tracing
- Component-based logging for easier debugging

### 10.3. Backup and Recovery

- Database backup and restore procedures
- Document version history for content recovery
- Alembic migrations for schema versioning

## 11. Future Enhancements

Potential future enhancements to the system include:

- **Enhanced UI**: More advanced document management interface
- **Real-time Collaboration**: Collaborative editing of documents
- **Advanced Visualization**: Interactive visualization of document relationships
- **Integration with CI/CD**: Automatic documentation updates based on code changes
- **Multi-Repository Support**: Monitoring multiple Git repositories
- **Advanced Search**: Faceted search and filtering options
- **Document Templates**: Templates for different types of documentation
- **Enhanced Security**: Single Sign-On (SSO) integration
- **Multi-Language Support**: Support for multilingual documentation

## 12. Conclusion

DokuCORE provides a robust foundation for AI-supported documentation management. Its hierarchical indexing engine and semantic search capabilities enable efficient document retrieval and maintenance. The MCP integration allows AI tools like ClaudeCode to interact with the documentation system, enhancing the capabilities of LLMs for documentation tasks.

The modular architecture allows for easy extension and customization, while the Docker-based deployment enables straightforward installation and configuration.
