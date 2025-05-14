# DokuCORE: AI-Supported Documentation System

DokuCORE is a comprehensive documentation system that uses AI to help maintain, search, and update documentation. The system combines FastAPI-MCP, PostgreSQL-pgvector, and hierarchical indexing to enable LLMs (Large Language Models) to efficiently search, update, and generate tasks for documentation maintenance.

## Features

- **Semantic Understanding**: Hierarchical indexing provides semantic understanding of documentation content
- **Efficient Token Usage**: Only loads relevant document sections, saving 70-95% on token usage
- **Code Monitoring**: Automatically monitors code changes to suggest documentation updates
- **AI Integration**: MCP protocol integration for AI tools like ClaudeCode
- **Vector Search**: Powerful semantic search using pgvector in PostgreSQL
- **Hierarchical Structure**: Maintains document relationships and context

## System Architecture

The system consists of the following components:

1. **FastAPI-MCP Server**: Provides MCP endpoints for AI tools
2. **PostgreSQL + pgvector Database**: Stores documents and vector embeddings
3. **Code Monitor Service**: Tracks code changes and generates documentation tasks
4. **Hierarchical Index Engine**: Creates structured, semantic document indices

## Installation

### Prerequisites

- Docker and Docker Compose
- Git
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

3. Build and start services:
```bash
docker-compose up -d --build
```

## Usage

### API Endpoints

The system provides the following REST API endpoints:

- `POST /documents/`: Create a new document
- `POST /documents/upload/`: Upload markdown file
- `GET /documents/`: List all documents
- `GET /documents/{doc_id}`: Get document details
- `GET /documents/{doc_id}/structure`: Get document structure
- `PUT /documents/{doc_id}`: Update document
- `POST /tasks/`: Create a new task
- `GET /tasks/`: List tasks
- `PUT /tasks/{task_id}`: Update task status
- `GET /search/`: Search documentation

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
│   ├── services/
│   ├── utils/
│   ├── routers/
│   └── indexing/
├── code-monitor/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── code_monitor.py
└── repo/         # Monitored git repository
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SentenceTransformers](https://www.sbert.net/)
- [LlamaIndex](https://www.llamaindex.ai/)
- [PostgreSQL](https://www.postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector)