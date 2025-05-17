# DokuCORE API Reference

This document provides comprehensive documentation for the DokuCORE API, including HTTP endpoints, request/response formats, and MCP (Model Context Protocol) tools for AI integration.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Documents](#documents)
- [Tasks](#tasks)
- [Search](#search)
- [Versions and Approvals](#versions-and-approvals)
- [Visualization](#visualization)
- [Health](#health)
- [MCP Tools](#mcp-tools)

## Base URL

All API endpoints are relative to the base URL of your DokuCORE installation:

```
http://{host}:{port}
```

By default, the API runs on port 9000 and the OpenAPI documentation is available at:

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

## Authentication

DokuCORE uses JWT (JSON Web Token) based authentication with role-based access control.

### Register User

Creates a new user in the system.

**Endpoint**: `POST /auth/users`

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "scopes": [
    "string"
  ]
}
```

**Available Scopes**:
- `documents:read`: Read documents
- `documents:write`: Create and update documents
- `documents:approve`: Approve document changes
- `tasks:read`: Read tasks
- `tasks:write`: Create and update tasks
- `users:read`: Read user information

**Response**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "disabled": "boolean",
  "scopes": [
    "string"
  ]
}
```

### Get Access Token

Obtains an access token for authentication.

**Endpoint**: `POST /auth/token`

**Request Form Data**:
```
username: string
password: string
```

**Response**:
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### Get Current User

Returns information about the currently authenticated user.

**Endpoint**: `GET /auth/users/me`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "disabled": "boolean",
  "scopes": [
    "string"
  ]
}
```

## Documents

Endpoints for document management.

### Create Document

Creates a new document and indexes it.

**Endpoint**: `POST /documents/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "title": "string",
  "path": "string",
  "content": "string"
}
```

**Response**:
```json
{
  "id": "integer",
  "title": "string",
  "path": "string",
  "content": "string",
  "last_modified": "string (ISO datetime)",
  "version": "integer"
}
```

### Upload Document

Uploads a markdown file and indexes it as a document.

**Endpoint**: `POST /documents/upload/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Form Data**:
```
file: file (markdown)
path: string (optional)
```

**Response**:
```json
{
  "status": "string",
  "message": "string",
  "document": {
    "id": "integer",
    "title": "string",
    "path": "string",
    "content": "string",
    "last_modified": "string (ISO datetime)",
    "version": "integer"
  }
}
```

### List Documents

Returns a list of all documents.

**Endpoint**: `GET /documents/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
[
  {
    "id": "integer",
    "title": "string",
    "path": "string",
    "content": "string",
    "last_modified": "string (ISO datetime)",
    "version": "integer"
  }
]
```

### Get Document

Returns details of a specific document.

**Endpoint**: `GET /documents/{doc_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `doc_id`: Document ID (integer)

**Response**:
```json
{
  "id": "integer",
  "title": "string",
  "path": "string",
  "content": "string",
  "last_modified": "string (ISO datetime)",
  "version": "integer"
}
```

### Get Document Structure

Returns the hierarchical structure of a document.

**Endpoint**: `GET /documents/{doc_id}/structure`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `doc_id`: Document ID (integer)

**Response**:
```json
{
  "title": "string",
  "path": "string",
  "structure": [
    {
      "id": "integer",
      "title": "string",
      "level": "integer",
      "children": [
        // Recursive structure with the same format
      ]
    }
  ]
}
```

### Update Document

Updates the content of a document and reindexes it.

**Endpoint**: `PUT /documents/{doc_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `doc_id`: Document ID (integer)

**Request Body**:
```json
{
  "content": "string",
  "changed_by": "string"
}
```

**Response**:
```json
{
  "id": "integer",
  "title": "string",
  "path": "string",
  "content": "string",
  "last_modified": "string (ISO datetime)",
  "version": "integer"
}
```

## Tasks

Endpoints for task management.

### Create Task

Creates a new documentation task.

**Endpoint**: `POST /tasks/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "title": "string",
  "description": "string",
  "document_id": "integer (optional)",
  "code_path": "string (optional)"
}
```

**Response**:
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "status": "string",
  "created_at": "string (ISO datetime)",
  "updated_at": "string (ISO datetime)",
  "document_id": "integer",
  "code_path": "string"
}
```

### List Tasks

Returns a list of tasks, optionally filtered by status.

**Endpoint**: `GET /tasks/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `status` (optional): Filter by status (e.g., "pending", "in-progress", "completed")

**Response**:
```json
[
  {
    "id": "integer",
    "title": "string",
    "description": "string",
    "status": "string",
    "created_at": "string (ISO datetime)",
    "updated_at": "string (ISO datetime)",
    "document_id": "integer",
    "code_path": "string"
  }
]
```

### Update Task Status

Updates the status of a task.

**Endpoint**: `PUT /tasks/{task_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `task_id`: Task ID (integer)

**Query Parameters**:
- `status`: New status (string)

**Response**:
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "status": "string",
  "created_at": "string (ISO datetime)",
  "updated_at": "string (ISO datetime)",
  "document_id": "integer",
  "code_path": "string"
}
```

## Search

Endpoints for searching documentation.

### Search Documents

Searches for documents based on a query.

**Endpoint**: `GET /search/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `query`: Search query (string)
- `limit` (optional): Maximum number of results (integer, default: 5)

**Response**:
```json
[
  {
    "id": "string",
    "title": "string",
    "path": "string",
    "preview": "string",
    "relevance": "string",
    "match_type": "string",
    "document_id": "integer"
  }
]
```

### Get Search Cache Statistics

Returns statistics about the search cache.

**Endpoint**: `GET /search/cache/stats`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "hits": "integer",
  "misses": "integer",
  "size": "integer",
  "max_size": "integer",
  "ttl": "integer"
}
```

### Clear Search Cache

Clears the search cache.

**Endpoint**: `POST /search/cache/clear`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "status": "string",
  "message": "string"
}
```

### Benchmark Search

Benchmarks search performance.

**Endpoint**: `GET /search/benchmark`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `query`: Search query (string)
- `iterations` (optional): Number of iterations (integer, default: 5)

**Response**:
```json
{
  "query": "string",
  "initial_time_ms": "number",
  "avg_cached_time_ms": "number",
  "iterations": "integer",
  "speedup_factor": "number",
  "result_count": "integer",
  "cache_stats": {
    "hits": "integer",
    "misses": "integer",
    "size": "integer",
    "max_size": "integer",
    "ttl": "integer"
  }
}
```

## Versions and Approvals

Endpoints for document versioning and approvals.

### Get Document Version History

Returns the version history of a document.

**Endpoint**: `GET /versions/documents/{doc_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `doc_id`: Document ID (integer)

**Response**:
```json
[
  {
    "id": "integer",
    "document_id": "integer",
    "content": "string",
    "changed_at": "string (ISO datetime)",
    "changed_by": "string",
    "version": "integer"
  }
]
```

### Get Document Version

Returns a specific version of a document.

**Endpoint**: `GET /versions/documents/{doc_id}/{version}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `doc_id`: Document ID (integer)
- `version`: Version number (integer)

**Response**:
```json
{
  "id": "integer",
  "document_id": "integer",
  "content": "string",
  "changed_at": "string (ISO datetime)",
  "changed_by": "string",
  "version": "integer"
}
```

### Restore Document Version

Restores a document to a previous version.

**Endpoint**: `POST /versions/documents/{doc_id}/restore/{version}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `doc_id`: Document ID (integer)
- `version`: Version number to restore (integer)

**Response**:
```json
{
  "status": "string",
  "message": "string"
}
```

### Create Approval Request

Creates a document approval request.

**Endpoint**: `POST /versions/approvals`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "document_id": "integer",
  "version": "integer",
  "requested_by": "string",
  "comments": "string (optional)"
}
```

**Response**:
```json
{
  "id": "integer",
  "document_id": "integer",
  "version": "integer",
  "status": "string",
  "requested_by": "string",
  "approved_by": "string",
  "requested_at": "string (ISO datetime)",
  "resolved_at": "string (ISO datetime)",
  "comments": "string"
}
```

### List Approval Requests

Returns a list of approval requests, optionally filtered by status.

**Endpoint**: `GET /versions/approvals`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `status` (optional): Filter by status (e.g., "pending", "approved", "rejected")

**Response**:
```json
[
  {
    "id": "integer",
    "document_id": "integer",
    "version": "integer",
    "status": "string",
    "requested_by": "string",
    "approved_by": "string",
    "requested_at": "string (ISO datetime)",
    "resolved_at": "string (ISO datetime)",
    "comments": "string"
  }
]
```

### Get Approval Request

Returns details of a specific approval request.

**Endpoint**: `GET /versions/approvals/{approval_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `approval_id`: Approval request ID (integer)

**Response**:
```json
{
  "id": "integer",
  "document_id": "integer",
  "version": "integer",
  "status": "string",
  "requested_by": "string",
  "approved_by": "string",
  "requested_at": "string (ISO datetime)",
  "resolved_at": "string (ISO datetime)",
  "comments": "string"
}
```

### Update Approval Request

Updates the status of an approval request (approve or reject).

**Endpoint**: `PUT /versions/approvals/{approval_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `approval_id`: Approval request ID (integer)

**Request Body**:
```json
{
  "status": "string",
  "approved_by": "string",
  "comments": "string (optional)"
}
```

**Response**:
```json
{
  "id": "integer",
  "document_id": "integer",
  "version": "integer",
  "status": "string",
  "requested_by": "string",
  "approved_by": "string",
  "requested_at": "string (ISO datetime)",
  "resolved_at": "string (ISO datetime)",
  "comments": "string"
}
```

## Visualization

Endpoints for visualizing document relationships and structure.

### Visualize Document Hierarchy

Returns a visualization of the document hierarchy.

**Endpoint**: `GET /api/visualization/hierarchy/{document_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `document_id`: Document ID (integer)

**Query Parameters**:
- `format` (optional): Output format ("html", "png", or "json", default: "html")

**Response**:
- If format is "html": HTML content
- If format is "png": Binary image/png
- If format is "json": JSON structure of the hierarchy

### Visualize Relationships

Returns a visualization of relationships between document sections.

**Endpoint**: `GET /api/visualization/relationships/{document_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `document_id`: Document ID (integer)

**Query Parameters**:
- `format` (optional): Output format ("html", "png", or "json", default: "html")
- `min_strength` (optional): Minimum relationship strength to show (float, default: 0.5)

**Response**:
- If format is "html": HTML content
- If format is "png": Binary image/png
- If format is "json": JSON structure of the relationships

### Visualize Search Results

Returns a visualization of search results with relevance scores.

**Endpoint**: `GET /api/visualization/search/{query}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `query`: Search query (string)

**Query Parameters**:
- `limit` (optional): Number of results to show (integer, default: 10)
- `format` (optional): Output format ("png" or "json", default: "png")

**Response**:
- If format is "png": Binary image/png
- If format is "json": JSON structure of the search results

### Visualize Keywords

Returns a visualization of keyword distribution for a document.

**Endpoint**: `GET /api/visualization/keywords/{document_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `document_id`: Document ID (integer)

**Query Parameters**:
- `limit` (optional): Number of keywords to show (integer, default: 20)
- `format` (optional): Output format ("png" or "json", default: "png")

**Response**:
- If format is "png": Binary image/png
- If format is "json": JSON structure of the keywords

### Generate Index Report

Generates a comprehensive report about the document index.

**Endpoint**: `GET /api/visualization/report`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**: HTML content with index report

## Health

Endpoints for monitoring system health.

### Overall Health Check

Returns the overall health status of the system.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "string",
  "config": {
    "api_host": "string",
    "api_port": "integer",
    "embedding_model_name": "string",
    "database_url": "string"
  }
}
```

### Database Health Check

Returns the health status of the database connection.

**Endpoint**: `GET /health/db`

**Response**:
```json
{
  "status": "string",
  "message": "string"
}
```

### Embedding Model Health Check

Returns the health status of the embedding model.

**Endpoint**: `GET /health/embedding`

**Response**:
```json
{
  "status": "string",
  "message": "string",
  "model": "string",
  "embedding_dimension": "integer"
}
```

## MCP Tools

Model Context Protocol (MCP) tools for AI integration. These tools can be accessed via the MCP protocol by AI assistants like ClaudeCode.

### list_docs()

Lists all available documents.

**Parameters**: None

**Returns**:
```json
[
  {
    "id": "integer",
    "title": "string",
    "path": "string"
  }
]
```

### get_doc_content(doc_id)

Returns the content of a specific document.

**Parameters**:
- `doc_id`: Document ID (integer)

**Returns**: Document content as string

### search_docs(query, limit=5)

Searches for documents based on a query.

**Parameters**:
- `query`: Search query (string)
- `limit` (optional): Maximum number of results (integer, default: 5)

**Returns**:
```json
[
  {
    "id": "string",
    "title": "string",
    "path": "string",
    "preview": "string",
    "relevance": "string",
    "match_type": "string",
    "document_id": "integer"
  }
]
```

### get_document_structure(doc_id)

Returns the hierarchical structure of a document.

**Parameters**:
- `doc_id`: Document ID (integer)

**Returns**:
```json
{
  "title": "string",
  "path": "string",
  "structure": [
    {
      "id": "integer",
      "title": "string",
      "level": "integer",
      "children": [
        // Recursive structure with the same format
      ]
    }
  ]
}
```

### update_document(doc_id, new_content, changed_by="AI")

Updates the content of a document and reindexes it.

**Parameters**:
- `doc_id`: Document ID (integer)
- `new_content`: New document content (string)
- `changed_by` (optional): User who made the change (string, default: "AI")

**Returns**:
```json
{
  "status": "string",
  "message": "string"
}
```

### create_task(title, description, doc_id=None, code_path=None)

Creates a new documentation task.

**Parameters**:
- `title`: Task title (string)
- `description`: Task description (string)
- `doc_id` (optional): Related document ID (integer)
- `code_path` (optional): Related code path (string)

**Returns**:
```json
{
  "status": "string",
  "message": "string",
  "task_id": "integer"
}
```

### get_tasks(status=None)

Returns a list of tasks, optionally filtered by status.

**Parameters**:
- `status` (optional): Filter by status (string)

**Returns**:
```json
[
  {
    "id": "integer",
    "title": "string",
    "description": "string",
    "status": "string",
    "created_at": "string (ISO datetime)",
    "updated_at": "string (ISO datetime)",
    "document_id": "integer",
    "code_path": "string"
  }
]
```

### get_document_versions(doc_id)

Returns the version history of a document.

**Parameters**:
- `doc_id`: Document ID (integer)

**Returns**:
```json
[
  {
    "id": "integer",
    "document_id": "integer",
    "content": "string",
    "changed_at": "string (ISO datetime)",
    "changed_by": "string",
    "version": "integer"
  }
]
```

### get_document_version(doc_id, version)

Returns a specific version of a document.

**Parameters**:
- `doc_id`: Document ID (integer)
- `version`: Version number (integer)

**Returns**:
```json
{
  "id": "integer",
  "document_id": "integer",
  "content": "string",
  "changed_at": "string (ISO datetime)",
  "changed_by": "string",
  "version": "integer"
}
```

### restore_document_version(doc_id, version, user)

Restores a document to a previous version.

**Parameters**:
- `doc_id`: Document ID (integer)
- `version`: Version number to restore (integer)
- `user`: User performing the restoration (string)

**Returns**:
```json
{
  "status": "string",
  "message": "string"
}
```

### get_approval_requests(status=None)

Returns a list of approval requests, optionally filtered by status.

**Parameters**:
- `status` (optional): Filter by status (string)

**Returns**:
```json
[
  {
    "id": "integer",
    "document_id": "integer",
    "version": "integer",
    "status": "string",
    "requested_by": "string",
    "approved_by": "string",
    "requested_at": "string (ISO datetime)",
    "resolved_at": "string (ISO datetime)",
    "comments": "string"
  }
]
```

### get_approval_request(approval_id)

Returns details of a specific approval request.

**Parameters**:
- `approval_id`: Approval request ID (integer)

**Returns**:
```json
{
  "id": "integer",
  "document_id": "integer",
  "version": "integer",
  "status": "string",
  "requested_by": "string",
  "approved_by": "string",
  "requested_at": "string (ISO datetime)",
  "resolved_at": "string (ISO datetime)",
  "comments": "string"
}
```

### create_approval_request(document_id, version, requested_by, comments=None)

Creates a document approval request.

**Parameters**:
- `document_id`: Document ID (integer)
- `version`: Version number to approve (integer)
- `requested_by`: User requesting approval (string)
- `comments` (optional): Additional comments (string)

**Returns**:
```json
{
  "status": "string",
  "message": "string",
  "approval_id": "integer"
}
```

### update_approval_request(approval_id, status, approved_by, comments=None)

Updates the status of an approval request (approve or reject).

**Parameters**:
- `approval_id`: Approval request ID (integer)
- `status`: New status ("approved" or "rejected")
- `approved_by`: User approving/rejecting (string)
- `comments` (optional): Additional comments (string)

**Returns**:
```json
{
  "status": "string",
  "message": "string"
}
```

## Examples

### Creating a New Document

```bash
curl -X POST "http://localhost:9000/documents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Reference",
    "path": "/docs/api-reference.md",
    "content": "# API Reference\n\nThis document describes the API endpoints..."
  }'
```

### Searching Documents

```bash
curl -X GET "http://localhost:9000/search/?query=API+endpoints&limit=3" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Creating a Task

```bash
curl -X POST "http://localhost:9000/tasks/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Update API Documentation",
    "description": "The API has been updated with new endpoints. Please update the documentation.",
    "document_id": 1
  }'
```

### Using MCP with ClaudeCode

```bash
claude code --mcp-server=docs=http://localhost:9000/mcp
```

Example ClaudeCode session:
```
> list_docs()
[
  {
    "id": 1,
    "title": "API Reference",
    "path": "/docs/api-reference.md"
  }
]

> search_docs("authentication")
[
  {
    "id": "API Reference",
    "title": "Authentication",
    "path": "/docs/api-reference.md",
    "preview": "## Authentication\n\nThe API uses JWT tokens for authentication...",
    "relevance": "98%",
    "match_type": "Keyword match",
    "document_id": 1
  }
]

> get_document_structure(1)
{
  "title": "API Reference",
  "path": "/docs/api-reference.md",
  "structure": [
    {
      "id": 1,
      "title": "API Reference",
      "level": 1,
      "children": [
        {
          "id": 2,
          "title": "Authentication",
          "level": 2,
          "children": []
        }
      ]
    }
  ]
}
```