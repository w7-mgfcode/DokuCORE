# DokuCORE: AI Integration User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [MCP Protocol Overview](#mcp-protocol-overview)
3. [Setting Up AI Tools with DokuCORE](#setting-up-ai-tools-with-dokucre)
   - [ClaudeCode Setup](#claudecode-setup)
   - [Other AI Tool Integrations](#other-ai-tool-integrations)
4. [Available MCP Tools](#available-mcp-tools)
   - [Document Management Tools](#document-management-tools)
   - [Search Tools](#search-tools)
   - [Task Management Tools](#task-management-tools)
   - [Version Management Tools](#version-management-tools)
   - [Approval Workflow Tools](#approval-workflow-tools)
5. [Common Usage Patterns](#common-usage-patterns)
   - [Searching Documentation](#searching-documentation)
   - [Updating Documentation](#updating-documentation)
   - [Creating Documentation Tasks](#creating-documentation-tasks)
   - [Managing Document Versions](#managing-document-versions)
6. [Advanced Usage Scenarios](#advanced-usage-scenarios)
   - [Automated Documentation Updates](#automated-documentation-updates)
   - [AI-Assisted Documentation Review](#ai-assisted-documentation-review)
   - [Code Analysis and Documentation Generation](#code-analysis-and-documentation-generation)
7. [Best Practices](#best-practices)
   - [Efficient Token Usage](#efficient-token-usage)
   - [Hierarchical Document Structure](#hierarchical-document-structure)
   - [Managing Document Relationships](#managing-document-relationships)
8. [Troubleshooting](#troubleshooting)
9. [Reference](#reference)

## Introduction

DokuCORE is an AI-supported documentation system designed to help maintain, search, and update documentation efficiently. One of its key features is integration with AI tools through the Model Context Protocol (MCP). This user guide provides detailed instructions and best practices for integrating and using AI tools with DokuCORE.

DokuCORE's AI integrations enable powerful capabilities such as:

- **Semantic Documentation Search**: Find relevant document sections using natural language queries
- **Hierarchical Document Understanding**: Access document structure and relationships
- **Automated Documentation Updates**: Generate and implement documentation updates
- **Task Creation and Management**: Create and track documentation tasks
- **Version Management**: Access and manage document version history

This guide assumes you have a working DokuCORE installation. If you haven't set up DokuCORE yet, please refer to the main installation documentation.

## MCP Protocol Overview

The Model Context Protocol (MCP) is a standardized interface for AI tools to interact with external systems. DokuCORE implements MCP endpoints that allow AI tools like ClaudeCode to:

1. **Query the system**: Search and retrieve documents and their structure
2. **Manipulate the system**: Update documents and create tasks
3. **View system state**: Access version history and task status

MCP tools are registered with the FastAPI-MCP server and exposed through a unified endpoint. Each tool is a function that can be called by an AI assistant, with parameters and return values defined in the API.

## Setting Up AI Tools with DokuCORE

### ClaudeCode Setup

[ClaudeCode](https://claude.ai/code) is Anthropic's AI-powered coding assistant that can interact with DokuCORE via the MCP protocol. To set up ClaudeCode with DokuCORE:

1. Make sure DokuCORE is running:

```bash
docker-compose up -d
```

2. Start ClaudeCode and connect it to DokuCORE's MCP endpoint:

```bash
claude code --mcp-server=docs=http://localhost:9000/mcp
```

3. Verify the connection by listing available documents:

```
> list_docs()
```

You should see a list of available documents in your DokuCORE instance:

```json
[
  {"id": 1, "title": "Getting Started", "path": "/docs/getting-started.md"},
  {"id": 2, "title": "API Reference", "path": "/docs/api-reference.md"}
]
```

### Other AI Tool Integrations

Any AI tool that supports the MCP protocol can be integrated with DokuCORE. The general approach is:

1. Configure the AI tool to connect to DokuCORE's MCP endpoint: `http://<dokucre-host>:<port>/mcp`
2. Use the available MCP tools to interact with the system

For custom AI integrations, you can make direct HTTP requests to the MCP endpoint. The endpoint accepts JSON-RPC style requests with the following structure:

```json
{
  "method": "tool_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## Available MCP Tools

DokuCORE provides a comprehensive set of MCP tools for AI integrations. These tools are categorized based on their functionality.

### Document Management Tools

#### `list_docs()`

Lists all available documents in the system.

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

**Example**:
```
> list_docs()
[
  {"id": 1, "title": "Getting Started", "path": "/docs/getting-started.md"},
  {"id": 2, "title": "API Reference", "path": "/docs/api-reference.md"}
]
```

#### `get_doc_content(doc_id)`

Gets the content of a specific document.

**Parameters**:
- `doc_id`: Document ID (integer)

**Returns**: Document content as string (markdown format)

**Example**:
```
> get_doc_content(1)
"# Getting Started

This guide will help you get started with DokuCORE.

## Installation

Follow these steps to install DokuCORE:

1. Clone the repository
2. Configure environment variables
3. Run the setup script
..."
```

#### `get_document_structure(doc_id)`

Gets the hierarchical structure of a document.

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
        // Recursive structure
      ]
    }
  ]
}
```

**Example**:
```
> get_document_structure(1)
{
  "title": "Getting Started",
  "path": "/docs/getting-started.md",
  "structure": [
    {
      "id": 1,
      "title": "Getting Started",
      "level": 1,
      "children": [
        {
          "id": 2,
          "title": "Installation",
          "level": 2,
          "children": []
        },
        {
          "id": 3,
          "title": "Configuration",
          "level": 2,
          "children": []
        }
      ]
    }
  ]
}
```

#### `update_document(doc_id, new_content, changed_by="AI")`

Updates the content of a document and reindexes it.

**Parameters**:
- `doc_id`: Document ID (integer)
- `new_content`: New document content (string)
- `changed_by`: User who made the change (string, default: "AI")

**Returns**:
```json
{
  "status": "string",
  "message": "string"
}
```

**Example**:
```
> update_document(1, "# Getting Started\n\nThis guide will help you get started with DokuCORE v2.0.\n\n## Installation\n...", "ClaudeAI")
{
  "status": "success",
  "message": "Document updated to version 2"
}
```

### Search Tools

#### `search_docs(query, limit=5)`

Performs an intelligent, hierarchical search in the documentation.

**Parameters**:
- `query`: Search query (string)
- `limit`: Maximum number of results (integer, default: 5)

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

**Example**:
```
> search_docs("how to install")
[
  {
    "id": "Getting Started",
    "title": "Installation",
    "path": "/docs/getting-started.md",
    "preview": "## Installation\n\nFollow these steps to install DokuCORE:\n\n1. Clone the repository\n2. Configure environment variables\n3. Run the setup script",
    "relevance": "95%",
    "match_type": "Semantic match",
    "document_id": 1
  }
]
```

### Task Management Tools

#### `create_task(title, description, doc_id=None, code_path=None)`

Creates a new task related to documentation update.

**Parameters**:
- `title`: Task title (string)
- `description`: Task description (string)
- `doc_id`: Related document ID (integer, optional)
- `code_path`: Related code path (string, optional)

**Returns**:
```json
{
  "status": "string",
  "message": "string",
  "task_id": "integer"
}
```

**Example**:
```
> create_task("Update Installation Instructions", "Update the installation instructions to include Docker setup", 1)
{
  "status": "success",
  "message": "Task created with ID 5",
  "task_id": 5
}
```

#### `get_tasks(status=None)`

Gets tasks, optionally filtered by status.

**Parameters**:
- `status`: Filter by status (string, optional: "pending", "in-progress", "completed")

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

**Example**:
```
> get_tasks("pending")
[
  {
    "id": 5,
    "title": "Update Installation Instructions",
    "description": "Update the installation instructions to include Docker setup",
    "status": "pending",
    "created_at": "2025-05-15T10:30:00",
    "updated_at": "2025-05-15T10:30:00",
    "document_id": 1,
    "code_path": null
  }
]
```

### Version Management Tools

#### `get_document_versions(doc_id)`

Gets the version history of a document.

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

**Example**:
```
> get_document_versions(1)
[
  {
    "id": 3,
    "document_id": 1,
    "content": "# Getting Started\n\nThis guide will help you get started with DokuCORE v2.0...",
    "changed_at": "2025-05-15T11:20:00",
    "changed_by": "ClaudeAI",
    "version": 2
  },
  {
    "id": 1,
    "document_id": 1,
    "content": "# Getting Started\n\nThis guide will help you get started with DokuCORE...",
    "changed_at": "2025-05-10T09:15:00",
    "changed_by": "admin",
    "version": 1
  }
]
```

#### `get_document_version(doc_id, version)`

Gets a specific version of a document.

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

**Example**:
```
> get_document_version(1, 1)
{
  "id": 1,
  "document_id": 1,
  "content": "# Getting Started\n\nThis guide will help you get started with DokuCORE...",
  "changed_at": "2025-05-10T09:15:00",
  "changed_by": "admin",
  "version": 1
}
```

#### `restore_document_version(doc_id, version, user)`

Restores a document to a previous version.

**Parameters**:
- `doc_id`: Document ID (integer)
- `version`: Version to restore (integer)
- `user`: User performing the restoration (string)

**Returns**:
```json
{
  "status": "string",
  "message": "string"
}
```

**Example**:
```
> restore_document_version(1, 1, "ClaudeAI")
{
  "status": "success",
  "message": "Document restored to version 1"
}
```

### Approval Workflow Tools

#### `get_approval_requests(status=None)`

Gets document approval requests, optionally filtered by status.

**Parameters**:
- `status`: Filter by status (string, optional: "pending", "approved", "rejected")

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

**Example**:
```
> get_approval_requests("pending")
[
  {
    "id": 2,
    "document_id": 1,
    "version": 2,
    "status": "pending",
    "requested_by": "ClaudeAI",
    "approved_by": null,
    "requested_at": "2025-05-15T11:25:00",
    "resolved_at": null,
    "comments": "Updated installation instructions with Docker setup"
  }
]
```

#### `get_approval_request(approval_id)`

Gets a specific approval request.

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

**Example**:
```
> get_approval_request(2)
{
  "id": 2,
  "document_id": 1,
  "version": 2,
  "status": "pending",
  "requested_by": "ClaudeAI",
  "approved_by": null,
  "requested_at": "2025-05-15T11:25:00",
  "resolved_at": null,
  "comments": "Updated installation instructions with Docker setup"
}
```

#### `create_approval_request(document_id, version, requested_by, comments=None)`

Creates a document approval request.

**Parameters**:
- `document_id`: Document ID (integer)
- `version`: Version number (integer)
- `requested_by`: User requesting approval (string)
- `comments`: Additional comments (string, optional)

**Returns**:
```json
{
  "status": "string",
  "message": "string",
  "approval_id": "integer"
}
```

**Example**:
```
> create_approval_request(1, 2, "ClaudeAI", "Updated installation instructions with Docker setup")
{
  "status": "success",
  "message": "Approval request created with ID 2",
  "approval_id": 2
}
```

#### `update_approval_request(approval_id, status, approved_by, comments=None)`

Updates an approval request (approve or reject).

**Parameters**:
- `approval_id`: Approval request ID (integer)
- `status`: New status ("approved" or "rejected")
- `approved_by`: User approving or rejecting (string)
- `comments`: Additional comments (string, optional)

**Returns**:
```json
{
  "status": "string",
  "message": "string"
}
```

**Example**:
```
> update_approval_request(2, "approved", "admin", "Looks good, approved")
{
  "status": "success",
  "message": "Approval request updated"
}
```

## Common Usage Patterns

This section covers common usage patterns and workflows for AI integrations with DokuCORE.

### Searching Documentation

Efficient documentation search is one of the primary use cases for AI integration with DokuCORE. The hierarchical indexing allows AI tools to find relevant sections of documentation without loading the entire corpus.

#### Basic Search

```
> search_docs("docker installation")
```

#### Limiting Results

```
> search_docs("API endpoints", 3)
```

#### Navigating Search Results

After finding a relevant document, you can get its content and structure:

```
> results = search_docs("docker installation")
> doc_id = results[0]["document_id"]
> get_doc_content(doc_id)
> get_document_structure(doc_id)
```

### Updating Documentation

AI tools can update documentation based on new information or changes in the codebase.

#### Workflow for Updating a Document

1. Find the document to update:
```
> results = search_docs("installation guide")
> doc_id = results[0]["document_id"]
```

2. Get the current content:
```
> current_content = get_doc_content(doc_id)
```

3. Make the necessary changes to the content.

4. Update the document:
```
> update_document(doc_id, updated_content, "ClaudeAI")
```

5. Create an approval request (if required):
```
> create_approval_request(doc_id, 2, "ClaudeAI", "Updated Docker installation instructions")
```

### Creating Documentation Tasks

AI tools can create tasks for documentation updates that can't be performed immediately or need human review.

#### Creating a Task Based on Code Changes

```
> create_task(
    "Update API Documentation for new endpoints",
    "The following endpoints were added to api/routers/user_router.py and need documentation:\n- GET /users/profile\n- PUT /users/profile",
    doc_id=2,
    code_path="api/routers/user_router.py"
)
```

#### Tracking Task Status

```
> get_tasks("pending")
```

### Managing Document Versions

AI tools can work with document version history to compare changes or restore previous versions.

#### Comparing Document Versions

```
> current_version = get_doc_content(doc_id)
> previous_version = get_document_version(doc_id, 1)["content"]
# Compare the versions
```

#### Restoring a Previous Version

```
> restore_document_version(doc_id, 1, "ClaudeAI")
```

## Advanced Usage Scenarios

### Automated Documentation Updates

AI tools can automatically update documentation based on code changes. Here's a typical workflow:

1. The code monitor detects changes in the codebase.
2. The AI tool receives a notification or periodically checks for pending tasks.
3. For each task, the AI tool:
   - Analyzes the code changes.
   - Finds the relevant documentation.
   - Updates the documentation to reflect the changes.
   - Creates an approval request for the changes.

Example code for automated updates:

```python
# Get pending tasks related to code changes
tasks = get_tasks("pending")
for task in tasks:
    if task["code_path"]:
        # Analyze the code changes
        # ... (code analysis logic) ...
        
        # Find relevant documentation
        search_results = search_docs(f"documentation for {task['code_path']}")
        if search_results:
            doc_id = search_results[0]["document_id"]
            current_content = get_doc_content(doc_id)
            
            # Update the documentation
            updated_content = update_documentation_based_on_code_changes(
                current_content, 
                task["code_path"]
            )
            
            # Submit the update
            update_document(doc_id, updated_content, "AutoDocBot")
            
            # Create approval request
            create_approval_request(
                doc_id, 
                get_document_versions(doc_id)[0]["version"],
                "AutoDocBot",
                f"Automated update based on changes in {task['code_path']}"
            )
            
            # Mark task as completed
            # ... (update task status) ...
```

### AI-Assisted Documentation Review

AI tools can assist in the documentation review process by checking for clarity, completeness, and accuracy.

Example workflow:

1. Get documents that need review:
```
approval_requests = get_approval_requests("pending")
```

2. For each request, review the document:
```
for request in approval_requests:
    doc_id = request["document_id"]
    version = request["version"]
    content = get_document_version(doc_id, version)["content"]
    
    # Analyze the documentation for issues
    issues = review_documentation(content)
    
    if issues:
        # Create comments with suggestions
        comments = format_review_comments(issues)
        
        # Update the approval request with comments
        update_approval_request(
            request["id"],
            "pending",  # Keep it pending for human review
            "ReviewBot",
            comments
        )
    else:
        # Approve if no issues found
        update_approval_request(
            request["id"],
            "approved",
            "ReviewBot",
            "Automatically approved - no issues found"
        )
```

### Code Analysis and Documentation Generation

AI tools can analyze code and generate documentation automatically.

Example workflow:

1. Analyze a code file to identify undocumented components.
2. Generate documentation for those components.
3. Update existing documentation or create a new document.

```python
# Analyze code file
code_path = "api/routers/document_router.py"
# ... (code analysis logic) ...

# Check if documentation exists
search_results = search_docs(f"documentation for {code_path}")

if search_results:
    # Update existing documentation
    doc_id = search_results[0]["document_id"]
    current_content = get_doc_content(doc_id)
    updated_content = update_documentation_with_new_code_info(current_content, code_analysis)
    update_document(doc_id, updated_content, "DocGenBot")
else:
    # Create new documentation
    new_content = generate_documentation_from_code(code_analysis)
    # ... (create new document) ...
```

## Best Practices

### Efficient Token Usage

DokuCORE's hierarchical indexing is designed to minimize token usage for AI tools by only loading relevant document sections. To make the most of this feature:

1. **Use specific search queries**: More specific queries result in more relevant sections being returned.
2. **Access document structure first**: Get the document structure before requesting specific sections.
3. **Work with document sections**: When possible, work with sections rather than entire documents.

Example of efficient token usage:

```
# Instead of loading all documents
# docs = [get_doc_content(doc_id) for doc_id in all_doc_ids]  # Inefficient

# Use search to find relevant sections
results = search_docs("authentication API", 3)

# Get the structure of the most relevant document
doc_id = results[0]["document_id"]
structure = get_document_structure(doc_id)

# Find the relevant section
auth_section = find_section_by_title(structure, "Authentication")

# Now you can work with just the relevant section
```

### Hierarchical Document Structure

DokuCORE works best with well-structured Markdown documents. When creating or updating documents, follow these guidelines:

1. **Use clear header hierarchy**: Start with a single H1 (`#`) and use nested headers (H2, H3, etc.) for subsections.
2. **Keep sections focused**: Each section should cover a specific topic or concept.
3. **Use consistent terminology**: Consistent terminology improves search and relationship detection.

Example of well-structured Markdown:

```markdown
# API Reference

This document describes the API endpoints available in the system.

## Authentication

Authentication is handled using JWT tokens.

### Obtaining a Token

To obtain a token, send a POST request to the `/auth/token` endpoint.

## Endpoints

This section describes all available endpoints.

### User Endpoints

This section covers user-related endpoints.

#### GET /users

Get a list of all users.
```

### Managing Document Relationships

DokuCORE automatically detects relationships between document sections based on content similarity and hierarchical structure. To improve relationship detection:

1. **Use cross-references**: Mention related sections explicitly.
2. **Use consistent terminology**: Use the same terms for the same concepts across documents.
3. **Structure related documents similarly**: Use similar heading structures for related documents.

Example of cross-references in documentation:

```markdown
# Authentication

For details on specific authentication endpoints, see the [Authentication Endpoints](api-reference.md#authentication-endpoints) section in the API Reference.
```

## Troubleshooting

### Common Issues and Solutions

1. **Connection Issues**

   **Problem**: Unable to connect to the MCP endpoint.
   
   **Solution**: 
   - Ensure DokuCORE is running.
   - Check the MCP endpoint URL.
   - Verify network connectivity.

2. **Search Returns No Results**

   **Problem**: Search queries return no results even when the information exists.
   
   **Solution**:
   - Try broader search terms.
   - Check if the document has been indexed properly.
   - Verify the embedding model is working correctly by checking the `/health/embedding` endpoint.

3. **Document Updates Fail**

   **Problem**: Document updates return an error.
   
   **Solution**:
   - Check if the document ID is valid.
   - Ensure the document content is valid Markdown.
   - Verify you have the necessary permissions.

4. **Hierarchical Indexing Issues**

   **Problem**: Document structure doesn't reflect the Markdown headers.
   
   **Solution**:
   - Check if the Markdown formatting is correct.
   - Try reindexing the document by updating it with its current content.
   - Verify the document has a clear header hierarchy.

### Logging and Debugging

DokuCORE provides detailed logging for debugging AI integrations:

1. **API Logs**: Check the API logs for request and response details.
   ```bash
   docker-compose logs api
   ```

2. **MCP Tool Logs**: MCP tool calls are logged with their parameters and results.
   ```bash
   docker-compose logs api | grep "MCP function called"
   ```

3. **Health Checks**: Use health check endpoints to verify system components.
   ```
   GET /health
   GET /health/db
   GET /health/embedding
   ```

## Reference

### MCP Tool Reference

See the [Available MCP Tools](#available-mcp-tools) section for detailed information on each tool.

### API Reference

For the complete REST API reference, see the API documentation:
- Swagger UI: `http://localhost:9000/api/docs`
- ReDoc: `http://localhost:9000/api/redoc`

### Model Context Protocol (MCP)

For more information on the Model Context Protocol (MCP):
- [FastMCP GitHub Repository](https://github.com/GermanMT/fastmcp)
- [MCP Protocol Specification](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp)

### Additional Resources

- [DokuCORE GitHub Repository](https://github.com/your-org/dokucre)
- [Anthropic Claude Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-claude)
- [SentenceTransformers Documentation](https://www.sbert.net/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)