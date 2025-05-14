# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DokuCORE is an AI-supported documentation system that combines FastAPI-MCP, PostgreSQL-pgvector, and custom Python MCP servers to enable LLMs to search, update, and generate tasks for documentation maintenance. The system implements hierarchical indexing to provide semantic understanding of documentation content.

## System Architecture

The system consists of the following components:
1. **FastAPI-MCP Server**: Provides MCP endpoints for AI tools
2. **PostgreSQL + pgvector Database**: Stores documents and vector embeddings
3. **Code Monitor Service**: Tracks code changes and generates documentation tasks
4. **Hierarchical Index Engine**: Creates structured, semantic document indices

## Development Setup

### Docker Configuration
```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f api
docker-compose logs -f code-monitor

# Restart a specific service
docker-compose restart api
```

### Database Operations
```bash
# Access database
docker-compose exec db psql -U docuser -d docdb

# Database backup
docker-compose exec db pg_dump -U docuser docdb > backup.sql

# Database restore
cat backup.sql | docker-compose exec -T db psql -U docuser -d docdb
```

### API Testing
```bash
# Create a document
curl -X POST http://localhost:9000/documents/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Document",
    "path": "/docs/test.md",
    "content": "# Test Document\n\nThis is a test markdown document."
  }'

# List documents
curl http://localhost:9000/documents/

# List tasks
curl http://localhost:9000/tasks/
```

## AI Integration

### ClaudeCode Setup
```bash
# Connect ClaudeCode to the MCP server
claude code --mcp-server=docs=http://localhost:9000/mcp
```

### MCP Tools
- `list_docs()`: Lists all available documentation files
- `get_doc_content(doc_id)`: Gets content of a specific document
- `search_docs(query, limit=5)`: Searches documentation with hierarchical context
- `get_document_structure(doc_id)`: Gets hierarchical structure of a document
- `update_document(doc_id, new_content, changed_by="AI")`: Updates a document
- `create_task(title, description, doc_id=None, code_path=None)`: Creates a documentation task
- `get_tasks(status=None)`: Lists tasks, optionally filtered by status

## Implementation Tasks

High priority tasks:
1. Infrastructure setup
2. Database implementation
3. FastAPI-MCP server development

Medium priority tasks:
1. Hierarchical indexing engine 
2. Code monitor service
3. REST API endpoints

Refer to TASK.md for detailed task tracking and progress.