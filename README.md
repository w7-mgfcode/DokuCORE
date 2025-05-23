# DokuCORE: AI-Supported Documentation System

DokuCORE is a comprehensive documentation system that uses AI to help maintain, search, and update documentation. The system combines FastAPI-MCP, PostgreSQL-pgvector, and hierarchical indexing to enable LLMs (Large Language Models) to efficiently search, update, and generate tasks for documentation maintenance.

## Features

- **Semantic Understanding**: Hierarchical indexing provides semantic understanding of documentation content
- **Efficient Token Usage**: Only loads relevant document sections, saving 70-95% on token usage
- **Enhanced Code Monitoring**:
  - Advanced change detection with AST parsing for accurate code analysis
  - Intelligent task prioritization based on file importance and change severity
  - Multi-repository monitoring with concurrent thread support
  - AI-powered change summary generation with LLM integration
  - Developer expertise-based task assignment recommendations
  - Webhook support for real-time notifications
- **AI Integration**: MCP protocol integration for AI tools like ClaudeCode
- **Vector Search**: Powerful semantic search using pgvector in PostgreSQL
- **Hierarchical Structure**: Maintains document relationships and context
- **Authentication & Authorization**: JWT token-based authentication with role-based access control
- **Document Versioning**: Complete version history tracking for all documents
- **Approval Workflow**: Formal document approval process with status tracking
- **Responsive UI**: Modern React-based UI for document management
- **API Documentation**: Interactive API documentation with Swagger UI
- **Health Monitoring**: Comprehensive health check endpoints for system monitoring
- **Database Migrations**: Alembic-based database migration system for schema versioning
- **Search Caching**: In-memory caching system for frequent searches with up to 100x speedup
- **Optimized Vector Indices**: Fine-tuned pgvector HNSW indices for faster similarity search
- **Performance Benchmarking**: Built-in tools for measuring and optimizing search performance
- **Advanced Search Optimization**: Research-backed search strategies for precision vs recall balance
- **Dynamic Node Segmentation**: Intelligent document chunking for optimal embedding and retrieval
- **Relationship Strength Thresholds**: Configurable thresholds for different relationship types
- **Advanced Keyword Extraction**: Multiple algorithms including TF-IDF, TextRank, NER, and phrase extraction
- **Index Visualization**: Interactive graphs and reports for exploring document relationships
- **Embedding Model Configuration**: Optimized parameters for different embedding models and use cases

## System Architecture

The system consists of the following components:

1. **FastAPI-MCP Server**: Provides MCP endpoints for AI tools
2. **PostgreSQL + pgvector Database**: Stores documents and vector embeddings
3. **Code Monitor Service**: Tracks code changes and generates documentation tasks
4. **Hierarchical Index Engine**: Creates structured, semantic document indices
5. **React UI**: Modern web interface for document management
6. **Version History System**: Maintains document revisions
7. **Approval Workflow**: Manages document approval process
8. **Advanced Indexing Modules**:
   - **Segmentation Strategy**: Intelligent document chunking with overlap
   - **Embedding Configuration**: Optimized parameters for various models
   - **Relationship Thresholds**: Research-backed relationship strength rules
   - **Search Optimizer**: Adaptive search strategies (precision vs recall)
   - **Advanced Keyword Extractor**: Multi-algorithm keyword extraction
   - **Visualization Tools**: Interactive graphs and reports

## Installation

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.10 or higher
- Linux server (recommended)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd DokuCORE
```

2. Configure environment variables:
```bash
# Update values in .env file as needed
nano .env
```

3. Run the database migrations:
```bash
./run_migrations.sh
```

4. Build and start services:
```bash
docker-compose up -d --build
```

5. Create an initial admin user:
```bash
curl -X POST http://localhost:9000/auth/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword",
    "full_name": "Admin User",
    "scopes": ["documents:read", "documents:write", "tasks:read", "tasks:write", "users:read"]
  }'
```

## Usage

### API Documentation

The system provides comprehensive API documentation via Swagger UI:

- Swagger UI: `http://localhost:9000/api/docs`
- ReDoc: `http://localhost:9000/api/redoc`
- OpenAPI JSON: `http://localhost:9000/api/openapi.json`

### Authentication

The system uses JWT token-based authentication:

1. Register a new user:
```bash
curl -X POST http://localhost:9000/auth/users \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password", "full_name": "Test User"}'
```

2. Get an access token:
```bash
curl -X POST http://localhost:9000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password"
```

3. Use the token in API requests:
```bash
curl -X GET http://localhost:9000/documents/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### API Endpoints

The system provides the following REST API endpoints:

#### Authentication
- `POST /auth/token`: Get an access token
- `POST /auth/users`: Register a new user
- `GET /auth/users/me`: Get current user info

#### Documents
- `POST /documents/`: Create a new document
- `POST /documents/upload/`: Upload markdown file
- `GET /documents/`: List all documents
- `GET /documents/{doc_id}`: Get document details
- `GET /documents/{doc_id}/structure`: Get document structure
- `PUT /documents/{doc_id}`: Update document

#### Versions and Approvals
- `GET /versions/documents/{doc_id}`: Get document version history
- `GET /versions/documents/{doc_id}/{version}`: Get specific document version
- `POST /versions/documents/{doc_id}/restore/{version}`: Restore document to previous version
- `POST /versions/approvals`: Create approval request
- `GET /versions/approvals`: List approval requests
- `GET /versions/approvals/{approval_id}`: Get specific approval
- `PUT /versions/approvals/{approval_id}`: Approve or reject document

#### Tasks
- `POST /tasks/`: Create a new task
- `GET /tasks/`: List all tasks
- `GET /tasks/{task_id}`: Get task details
- `PUT /tasks/{task_id}`: Update task status

#### Search
- `GET /search/`: Search documents
- `GET /search/hierarchical`: Hierarchical search with context
- `GET /search/cache/stats`: Get search cache statistics
- `POST /search/cache/clear`: Clear the search cache
- `GET /search/benchmark`: Benchmark search performance

#### Visualization
- `GET /api/visualization/hierarchy/{document_id}`: Visualize document hierarchy
- `GET /api/visualization/relationships/{document_id}`: Visualize document relationships
- `GET /api/visualization/search/{query}`: Visualize search results
- `GET /api/visualization/keywords/{document_id}`: Visualize keyword distribution
- `GET /api/visualization/report`: Generate comprehensive index report

#### Health
- `GET /health`: Overall health check
- `GET /health/db`: Database health check
- `GET /health/embedding`: Embedding model health check

### ClaudeCode Integration

To use with ClaudeCode:

```bash
claude code --mcp-server=docs=http://localhost:9000/mcp
```

Available MCP tools:

- `list_docs()`: List all available documents
- `get_doc_content(doc_id)`: Get document content
- `search_docs(query, limit=5)`: Search documentation
- `get_document_structure(doc_id)`: Get document structure
- `update_document(doc_id, new_content, changed_by="AI")`: Update document
- `create_task(title, description, doc_id=None, code_path=None)`: Create task
- `get_tasks(status=None)`: List tasks
- `get_document_versions(doc_id)`: Get document version history
- `get_document_version(doc_id, version)`: Get specific document version
- `restore_document_version(doc_id, version, user)`: Restore document to previous version
- `get_approval_requests(status=None)`: List document approval requests
- `get_approval_request(approval_id)`: Get specific approval request
- `create_approval_request(document_id, version, requested_by, comments=None)`: Create approval request
- `update_approval_request(approval_id, status, approved_by, comments=None)`: Approve or reject document

## Project Structure

```
DokuCORE/
├── docker-compose.yml
├── .env
├── init.sql
├── postgres/
│   └── Dockerfile
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── models/
│   │   ├── document.py
│   │   ├── version.py
│   │   ├── auth.py
│   │   └── task.py
│   ├── services/
│   │   ├── document_service.py
│   │   ├── version_service.py
│   │   ├── auth_service.py
│   │   ├── search_service.py
│   │   └── task_service.py
│   ├── utils/
│   │   ├── cache.py
│   │   ├── db.py
│   │   └── config.py
│   ├── routers/
│   │   ├── document_router.py
│   │   ├── version_router.py
│   │   ├── auth_router.py
│   │   └── task_router.py
│   ├── indexing/
│   │   ├── hierarchical_indexer.py
│   │   ├── markdown_parser.py
│   │   ├── keyword_extractor.py
│   │   ├── hierarchical_search.py
│   │   ├── segmentation_strategy.py
│   │   ├── embedding_config.py
│   │   ├── relationship_thresholds.py
│   │   ├── search_optimizer.py
│   │   ├── advanced_keyword_extractor.py
│   │   └── visualization.py
│   └── mcp_tools.py
├── ui/
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── DocumentVersioning.jsx
│       │   ├── DocumentDetails.jsx
│       │   └── MarkdownDisplay.jsx
│       ├── pages/
│       ├── contexts/
│       ├── App.jsx
│       └── index.js
├── code-monitor/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── code_monitor.py
├── migrations/
│   ├── versions/
│   │   ├── 001_initial.py
│   │   ├── 002_add_auth.py
│   │   ├── 003_optimize_pgvector_indices.py
│   │   └── 004_add_document_approval.py
│   ├── env.py
│   └── alembic.ini
└── repo/         # Monitored git repository
```

## Development

### Testing

The project uses pytest for testing. To run the tests:

```bash
# Run all tests
./run_tests.sh

# Run tests in Docker (recommended)
docker-compose exec api python -m pytest tests/ -v

# Run specific test modules
docker-compose exec api python -m pytest tests/indexing/ -v
docker-compose exec api python -m pytest tests/api/ -v

# Run specific test files
docker-compose exec api python -m pytest tests/indexing/test_segmentation_strategy.py -v

# Run tests with coverage
docker-compose exec api python -m pytest tests/ --cov=api --cov-report=html
```

The test suite includes:
- Unit tests for all indexing modules
- Integration tests for API endpoints
- Mocked tests for external dependencies
- Performance benchmarks (WIP)

### Database Migrations

The project uses Alembic for database migrations:

```bash
# Apply all migrations
./run_migrations.sh

# Create a new migration
cd migrations
alembic revision -m "Description of changes"

# Apply specific migrations
alembic upgrade +1  # Apply next migration
alembic downgrade -1  # Rollback last migration
```

### Configuration

Configuration is managed through environment variables. See the `.env` file for available options.

Key configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `API_PORT`: Port for the FastAPI server
- `EMBEDDING_MODEL`: Name of the SentenceTransformer model to use
- `EMBEDDING_DIM`: Dimension of the embeddings
- `SIMILARITY_THRESHOLD`: Threshold for semantic similarity (0.0-1.0)
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `JWT_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for your changes
4. Ensure all tests pass (`./run_tests.sh`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Advanced Features

### Segmentation Strategy
The system uses intelligent document segmentation to optimize token usage:
- Header-based segmentation for structured documents
- Semantic boundary detection for natural text flow
- Token-limited chunks for embedding efficiency
- Overlapping segments to maintain context

### Embedding Configuration
Research-backed configurations for different embedding models:
- Optimized parameters for MiniLM, MPNet, Ada, Instructor, and E5
- Use-case specific configurations (indexing, search, keywords)
- Memory usage calculations and batch size optimization
- Automatic model selection based on requirements

### Relationship Management
Sophisticated relationship detection and scoring:
- Parent-child, sibling, semantic, and keyword-based relationships
- Research-backed threshold values for each relationship type
- Adaptive thresholds based on corpus characteristics
- Combined strength calculations for multi-type relationships

### Search Optimization
Adaptive search strategies for different use cases:
- Precision-focused for exact matches
- Recall-focused for comprehensive results
- Balanced for general use
- Speed-optimized for real-time applications
- Query expansion and result diversity optimization

### Keyword Extraction
Multiple algorithms for comprehensive keyword extraction:
- Enhanced TF-IDF with document frequency
- TextRank graph-based algorithm
- Named Entity Recognition (NER)
- Multi-word phrase extraction
- Domain-specific term boosting

### Visualization Tools
Interactive visualization of document structures:
- Hierarchical document tree visualization
- Relationship network graphs
- Search result relevance charts
- Keyword distribution plots
- Comprehensive HTML reports
- Interactive D3.js graphs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Dependencies

This project is built with the following key technologies:

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework for building APIs
- [FastMCP](https://github.com/GermanMT/fastmcp) - MCP protocol integration for FastAPI
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search extension for PostgreSQL
- [SentenceTransformers](https://www.sbert.net/) - Neural network models for text embeddings
- [LlamaIndex](https://www.llamaindex.ai/) - Data framework for LLM applications
- [PyJWT](https://pyjwt.readthedocs.io/) - JSON Web Token implementation in Python
- [Passlib](https://passlib.readthedocs.io/) - Password hashing library for Python
- [Alembic](https://alembic.sqlalchemy.org/) - Database migration tool for SQLAlchemy
- [pytest](https://docs.pytest.org/) - Testing framework for Python

### Frontend
- [React](https://reactjs.org/) - JavaScript library for building user interfaces
- [Material-UI](https://mui.com/) - React UI framework
- [React Router](https://reactrouter.com/) - Routing library for React
- [Axios](https://axios-http.com/) - Promise-based HTTP client
- [React Markdown](https://github.com/remarkjs/react-markdown) - Markdown parser and renderer for React

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SentenceTransformers](https://www.sbert.net/)
- [LlamaIndex](https://www.llamaindex.ai/)
- [PostgreSQL](https://www.postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector)