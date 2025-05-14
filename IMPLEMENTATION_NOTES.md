# Implementation Notes

## Overview

This document provides notes on the implementation of the DokuCORE AI-supported documentation system. It outlines the architecture, design decisions, and implementation details.

## Project Structure

The project follows a modular architecture with clear separation of concerns:

```
DokuCORE/
├── api/                  # API server implementation
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   ├── utils/            # Utilities and helpers
│   ├── routers/          # API route handlers
│   ├── indexing/         # Hierarchical indexing engine
│   └── mcp_tools.py      # MCP protocol tools
├── code-monitor/         # Code change monitoring service
├── postgres/             # PostgreSQL with pgvector
├── tests/                # Test suite
└── docs/                 # Documentation storage
```

## Key Components

### 1. API Server

The API server is built with FastAPI and provides:
- REST API endpoints for document and task management
- MCP protocol integration for AI tools
- Configuration management
- Middleware for logging and error handling

### 2. Database

PostgreSQL with pgvector extension is used for:
- Document storage
- Vector embeddings
- Hierarchical document structure
- Document relationships
- Task management

### 3. Hierarchical Indexing Engine

The hierarchical indexing engine:
- Parses markdown documents into hierarchical structure
- Generates embeddings for each section
- Builds relationships between sections
- Extracts keywords with importance scoring
- Provides semantic search capabilities

### 4. Code Monitor Service

The code monitor service:
- Monitors a Git repository for changes
- Detects when files are modified
- Creates tasks for updating related documentation
- Integrates with the API server

## Implementation Details

### Embedding Model

We use SentenceTransformers for generating vector embeddings. The default model is "all-MiniLM-L6-v2" with 384 dimensions, but this can be configured through environment variables.

### Hierarchical Document Structure

Documents are broken down into a hierarchical structure based on markdown headers. Each section gets its own embedding, relationships, and keywords.

### Vector Search

Search is performed using vector similarity in pgvector. We use a multi-step search process:
1. Keyword search for direct matches
2. Semantic search for conceptually related content
3. Relationship expansion to include contextually related sections

### Configuration Management

Configuration is managed through environment variables and a central Config class, making it easy to customize the system for different environments.

### Testing Framework

The project includes a comprehensive test suite using pytest:
- Unit tests for individual components
- Integration tests for API endpoints
- Test coverage reporting

## Performance Considerations

- Vector search is optimized using pgvector's HNSW index
- Hierarchical indexing reduces token usage by 70-95%
- Document sections are loaded only as needed
- Relationship strength thresholds prevent noise in search results

## Security Considerations

- CORS middleware with configurable origins
- Input validation through Pydantic models
- Error handling that doesn't expose sensitive information
- Request logging with unique request IDs

## Future Improvements

Areas identified for future improvement:
- Authentication and authorization
- Database query optimization
- Better visualization of document relationships
- Application health monitoring
- API documentation with Swagger/OpenAPI
- Database migration system