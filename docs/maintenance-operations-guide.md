# DokuCORE: Maintenance and Operations Guide

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture Overview](#system-architecture-overview)
3. [Installation and Setup](#installation-and-setup)
4. [Configuration Management](#configuration-management)
5. [Operational Tasks](#operational-tasks)
   - [Starting and Stopping Services](#starting-and-stopping-services)
   - [Health Monitoring](#health-monitoring)
   - [Logs and Debugging](#logs-and-debugging)
   - [Backup and Restore](#backup-and-restore)
   - [Scaling Considerations](#scaling-considerations)
6. [Database Management](#database-management)
   - [Schema Migrations](#schema-migrations)
   - [Database Performance Optimization](#database-performance-optimization)
   - [Vector Index Maintenance](#vector-index-maintenance)
7. [Code Monitor Management](#code-monitor-management)
   - [Repository Configuration](#repository-configuration)
   - [Task Generation Settings](#task-generation-settings)
   - [Webhook Integration](#webhook-integration)
8. [Security Management](#security-management)
   - [Authentication Settings](#authentication-settings)
   - [User and Role Management](#user-and-role-management)
   - [Secret Management](#secret-management)
9. [Performance Optimization](#performance-optimization)
   - [Embedding Model Selection](#embedding-model-selection)
   - [Search Optimization](#search-optimization)
   - [Caching Strategy](#caching-strategy)
10. [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Diagnostic Procedures](#diagnostic-procedures)
    - [Recovery Procedures](#recovery-procedures)
11. [Upgrading DokuCORE](#upgrading-dokucre)
12. [Appendix](#appendix)
    - [Environment Variable Reference](#environment-variable-reference)
    - [Useful Commands](#useful-commands)
    - [Log Level Reference](#log-level-reference)

## Introduction

This document provides comprehensive guidelines for the maintenance and operations of DokuCORE, an AI-supported documentation system. It covers installation, configuration, routine maintenance tasks, troubleshooting, and optimization strategies. This guide is intended for system administrators, DevOps engineers, and technical personnel responsible for managing DokuCORE deployments.

## System Architecture Overview

DokuCORE consists of three primary components deployed as Docker containers:

1. **PostgreSQL Database (db)**: Stores documents, hierarchical indices, embeddings, and application data. Uses the pgvector extension for vector similarity search.

2. **API Server (api)**: A FastAPI application that provides:
   - REST API endpoints for document management
   - MCP (Model Context Protocol) for AI tool integration
   - Hierarchical document indexing
   - Search functionality
   - Authentication and authorization

3. **Code Monitor (code-monitor)**: Monitors Git repositories for changes and creates documentation tasks.

The components interact as follows:

```mermaid
graph TD
    A[API Server] <-->|Stores/Retrieves| B[PostgreSQL Database]
    C[Code Monitor] -->|Creates Tasks| A
    D[AI Tools] <-->|MCP Protocol| A
    E[UI] <-->|REST APIs| A
    F[Git Repository] -->|Code Changes| C
```

## Installation and Setup

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.10 or higher (for development and CLI tools)
- Linux/macOS/Windows with WSL (Windows Subsystem for Linux)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd DokuCORE
   ```

2. **Configure environment variables**:
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit the .env file with your configuration
   nano .env
   ```

3. **Run database migrations**:
   ```bash
   ./run_migrations.sh
   ```

4. **Build and start services**:
   ```bash
   docker-compose up -d --build
   ```

5. **Create an initial admin user**:
   ```bash
   curl -X POST http://localhost:9000/auth/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "password": "securepassword",
       "full_name": "Admin User",
       "scopes": ["documents:read", "documents:write", "tasks:read", "tasks:write", "users:read", "documents:approve"]
     }'
   ```

### Verifying Installation

1. **Check container status**:
   ```bash
   docker-compose ps
   ```
   All containers should show as "Up" and healthy.

2. **Verify API server**:
   ```bash
   curl http://localhost:9000/health
   ```
   Should return `{"status": "ok", "config": {...}}`.

3. **Check database connectivity**:
   ```bash
   curl http://localhost:9000/health/db
   ```
   Should return `{"status": "ok", "message": "Database connection successful"}`.

4. **Verify embedding model**:
   ```bash
   curl http://localhost:9000/health/embedding
   ```
   Should return information about the embedding model status.

## Configuration Management

DokuCORE uses environment variables for configuration. These are defined in the `.env` file and passed to Docker containers.

### Key Configuration Files

- **.env**: Main configuration file
- **docker-compose.yml**: Docker service definitions
- **api/utils/config.py**: Configuration loading and validation
- **code-monitor/config/**: Code monitor configuration files

### Critical Environment Variables

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| POSTGRES_USER | PostgreSQL username | docuser | Change in production |
| POSTGRES_PASSWORD | PostgreSQL password | docpassword | Change in production |
| POSTGRES_DB | PostgreSQL database name | docdb | |
| API_PORT | Port for API server | 9000 | |
| DATABASE_URL | PostgreSQL connection string | postgresql://docuser:docpassword@db:5432/docdb | Format: postgresql://username:password@host:port/dbname |
| REPO_PATH | Path to monitored Git repository | /app/repo | Inside code-monitor container |
| API_URL | URL for API server | http://api:9000 | Inside Docker network |
| CHECK_INTERVAL | Code monitor check interval (seconds) | 300 | |
| EMBEDDING_MODEL | Sentence transformer model | all-MiniLM-L6-v2 | See [SentenceTransformers models](https://www.sbert.net/docs/pretrained_models.html) |
| EMBEDDING_DIM | Embedding dimensions | 384 | Must match model output dimensions |
| SIMILARITY_THRESHOLD | Minimum similarity score for search | 0.7 | Range: 0.0-1.0 |
| JWT_SECRET_KEY | Secret key for JWT tokens | your-secret-key-change-in-production | Change in production |
| LOG_LEVEL | Logging level | INFO | Options: DEBUG, INFO, WARNING, ERROR, CRITICAL |

### Changing Configuration

1. **Edit the .env file**:
   ```bash
   nano .env
   ```

2. **Restart the affected services**:
   ```bash
   docker-compose restart api code-monitor
   ```
   
   For database-related changes:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Advanced Configuration

For advanced configurations:

1. **API Server**:
   Create a custom config file in `api/utils/custom_config.py` to override default configuration.

2. **Code Monitor**:
   Add JSON configuration files in `code-monitor/config/` for custom monitoring rules.

3. **Database Optimization**:
   Modify pgvector index parameters in `migrations/versions/003_optimize_pgvector_indices.py` and apply with `alembic upgrade head`.

## Operational Tasks

### Starting and Stopping Services

**Start all services**:
```bash
docker-compose up -d
```

**Stop all services**:
```bash
docker-compose down
```

**Restart a specific service**:
```bash
docker-compose restart api
```

**View logs from all services**:
```bash
docker-compose logs -f
```

**View logs from a specific service**:
```bash
docker-compose logs -f api
```

### Health Monitoring

DokuCORE provides health check endpoints:

1. **Overall health**: `GET /health`
2. **Database health**: `GET /health/db`
3. **Embedding model health**: `GET /health/embedding`

#### Setting Up External Monitoring

You can use tools like Prometheus, Grafana, or simple cron jobs to monitor these endpoints:

```bash
# Example cron job for basic monitoring
*/5 * * * * curl -s http://localhost:9000/health | grep -q '"status": "ok"' || echo "DokuCORE health check failed" | mail -s "DokuCORE Alert" admin@example.com
```

#### Docker Health Checks

The Docker Compose file includes health checks for the database. You can monitor container health with:

```bash
docker-compose ps
```

Look for "(healthy)" next to container names.

### Logs and Debugging

#### Accessing Logs

**API Server Logs**:
```bash
docker-compose logs -f api
```

**Code Monitor Logs**:
```bash
docker-compose logs -f code-monitor
```

**Database Logs**:
```bash
docker-compose logs -f db
```

#### Log Levels

Adjust log levels in the `.env` file:

```
LOG_LEVEL=DEBUG  # For more detailed logs
```

Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

#### Debugging API Server

For detailed API debugging:

1. Set `LOG_LEVEL=DEBUG` in `.env`
2. Restart the API service: `docker-compose restart api`
3. Check logs: `docker-compose logs -f api`

#### Debugging Code Monitor

For code monitor debugging:

1. Set `LOG_LEVEL=DEBUG` in `.env`
2. Add more verbose logging in code-monitor configuration
3. Restart code monitor: `docker-compose restart code-monitor`
4. Check logs: `docker-compose logs -f code-monitor`

### Backup and Restore

#### Database Backup

```bash
# Create a backup of the PostgreSQL database
docker-compose exec db pg_dump -U docuser docdb > backup_$(date +%Y%m%d).sql
```

#### Database Restore

```bash
# Restore from a backup file
cat backup_20250517.sql | docker-compose exec -T db psql -U docuser docdb
```

#### Configuration Backup

Back up the following files:
- `.env`
- Custom configuration files
- Docker volumes (if using named volumes)

```bash
# Create a backup directory
mkdir -p backups/$(date +%Y%m%d)

# Copy configuration files
cp .env backups/$(date +%Y%m%d)/
cp -r code-monitor/config backups/$(date +%Y%m%d)/
```

#### Full System Backup (Production)

For production environments, consider:
1. Regular database backups (daily/hourly)
2. Configuration backups
3. Docker volume backups
4. Infrastructure-as-code (if applicable)

### Scaling Considerations

#### Vertical Scaling

1. **Database**: Increase CPU/RAM allocation for PostgreSQL container
2. **API Server**: Increase CPU/RAM allocation for API container
3. **Code Monitor**: Typically doesn't require significant resources

Adjust resource limits in `docker-compose.yml`:

```yaml
services:
  db:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

#### Horizontal Scaling

For horizontal scaling (production environments):

1. **Database**: 
   - Consider PostgreSQL replication
   - Separate read/write operations
   
2. **API Server**:
   - Deploy multiple instances behind a load balancer
   - Use shared session storage
   
3. **Code Monitor**:
   - Can run multiple instances monitoring different repositories

## Database Management

### Schema Migrations

DokuCORE uses Alembic for database migrations.

#### Applying Migrations

```bash
# Run all migrations
./run_migrations.sh

# Or manually:
cd migrations
alembic upgrade head
```

#### Creating New Migrations

```bash
cd migrations
alembic revision -m "Description of changes"
```

Edit the generated migration file in `migrations/versions/`.

#### Rolling Back Migrations

```bash
cd migrations
alembic downgrade -1  # Roll back one migration
```

### Database Performance Optimization

#### pgvector Index Optimization

The pgvector extension uses HNSW indices for efficient vector search:

- **m**: Maximum connections per node (higher = more accurate but slower)
- **ef_construction**: Size of dynamic list during build (higher = more accurate but slower)
- **ef**: Size of dynamic list during search (higher = more accurate but slower)

Default values:
- m = 16
- ef_construction = 128
- ef = 100

To adjust these parameters:

1. Create a new migration:
   ```bash
   cd migrations
   alembic revision -m "Optimize pgvector indices"
   ```

2. Edit the migration file to recreate indices with new parameters:
   ```python
   def upgrade() -> None:
       # Drop existing indices
       op.execute('DROP INDEX IF EXISTS document_hierarchy_embedding_idx;')
       
       # Create optimized indices
       op.execute('''
       CREATE INDEX document_hierarchy_embedding_idx 
       ON document_hierarchy USING hnsw (embedding vector_cosine_ops) 
       WITH (m = 24, ef_construction = 200);
       ''')
       
       # Set the ef search parameter
       op.execute('ALTER INDEX document_hierarchy_embedding_idx SET (ef = 150);')
   ```

3. Apply the migration:
   ```bash
   alembic upgrade head
   ```

#### PostgreSQL Tuning

For production environments, consider tuning PostgreSQL settings:

1. Create a custom `postgresql.conf` in `postgres/`
2. Mount it in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
   command: postgres -c config_file=/etc/postgresql/postgresql.conf
   ```

Key settings to consider:
- `shared_buffers`: 25% of total RAM
- `effective_cache_size`: 50-75% of total RAM
- `maintenance_work_mem`: 256MB
- `work_mem`: 64MB
- `max_connections`: Based on expected load

### Vector Index Maintenance

Vector indices require periodic maintenance:

#### Reindexing Documents

If vector search quality degrades, consider reindexing documents:

```bash
# Connect to the database
docker-compose exec db psql -U docuser docdb

# Trigger reindexing by clearing embeddings
UPDATE documents SET embedding = NULL;
UPDATE document_hierarchy SET embedding = NULL;
UPDATE document_keywords SET embedding = NULL;
```

The API server will regenerate embeddings when documents are accessed.

#### Index Vacuuming

Regularly vacuum the database to maintain performance:

```bash
docker-compose exec db psql -U docuser docdb -c "VACUUM ANALYZE"
```

Consider setting up a weekly cron job for this task.

## Code Monitor Management

The code monitor service tracks changes in Git repositories and generates tasks for documentation updates.

### Repository Configuration

#### Single Repository Setup

1. Update `.env` file:
   ```
   REPO_PATH=/app/repo
   ```

2. Mount the repository in `docker-compose.yml`:
   ```yaml
   code-monitor:
     volumes:
       - /path/to/local/repo:/app/repo
   ```

#### Multi-Repository Setup

For monitoring multiple repositories:

1. Create a configuration file at `code-monitor/config/repositories.json`:
   ```json
   {
     "repositories": [
       {
         "path": "/app/repo/project1",
         "name": "Project 1",
         "branch": "main",
         "file_patterns": ["*.py", "*.js"]
       },
       {
         "path": "/app/repo/project2",
         "name": "Project 2",
         "branch": "master",
         "file_patterns": ["*.go", "*.md"]
       }
     ]
   }
   ```

2. Mount the repositories in `docker-compose.yml`:
   ```yaml
   code-monitor:
     volumes:
       - /path/to/project1:/app/repo/project1
       - /path/to/project2:/app/repo/project2
   ```

### Task Generation Settings

#### Change Detection Configuration

Customize change detection in `code-monitor/config/change_detection.json`:

```json
{
  "file_importance": {
    "src/core/": 5,
    "src/api/": 4,
    "src/utils/": 2,
    "tests/": 1
  },
  "file_extensions": {
    ".py": 5,
    ".js": 4,
    ".md": 3,
    ".sql": 3
  },
  "ignore_patterns": [
    "*.min.js",
    "*.test.js",
    "*.spec.ts",
    "__pycache__/"
  ]
}
```

#### LLM Integration

If using an LLM API for task generation:

1. Configure in `.env`:
   ```
   LLM_API_URL=https://api.example.com/v1/completions
   LLM_API_KEY=your-api-key
   ```

2. Create LLM prompt templates in `code-monitor/config/prompts.json`:
   ```json
   {
     "task_generation": "Analyze the following code changes and generate a documentation task description:\n\n{diff}\n\nTask description:",
     "task_priority": "Analyze the following code changes and rate their documentation priority from 1-5:\n\n{diff}"
   }
   ```

### Webhook Integration

Configure webhooks to notify external systems about documentation tasks:

1. Enable webhooks in `.env`:
   ```
   WEBHOOK_ENABLED=true
   WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```

2. Customize webhook payload in `code-monitor/config/webhook.json`:
   ```json
   {
     "slack": {
       "template": {
         "text": "New documentation task: {task_title}",
         "blocks": [
           {
             "type": "header",
             "text": {
               "type": "plain_text",
               "text": "Documentation Update Required"
             }
           },
           {
             "type": "section",
             "text": {
               "type": "mrkdwn",
               "text": "*Task:* {task_title}\n*Description:* {task_description}\n*Related Document:* {document_title}"
             }
           }
         ]
       }
     },
     "generic": {
       "template": {
         "taskId": "{task_id}",
         "title": "{task_title}",
         "description": "{task_description}",
         "documentId": "{document_id}"
       }
     }
   }
   ```

## Security Management

### Authentication Settings

#### JWT Configuration

Configure JWT settings in `.env`:

```
JWT_SECRET_KEY=your-secure-secret-key
JWT_TOKEN_EXPIRE_MINUTES=30
```

For production, use a strong, randomly generated key:

```bash
# Generate a secure random key
openssl rand -hex 32
```

#### Password Policy

User password policy is enforced at the API level. To modify:

1. Edit `api/services/auth_service.py`
2. Adjust the `verify_password` function

#### CORS Configuration

Configure Cross-Origin Resource Sharing in `api/utils/config.py`:

```python
# Default: Allow all origins in development
CORS_ORIGINS = ["*"]

# For production: Restrict to specific domains
CORS_ORIGINS = ["https://yourdomain.com", "https://admin.yourdomain.com"]
```

### User and Role Management

#### Creating Users

```bash
curl -X POST http://localhost:9000/auth/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "username",
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "User Name",
    "scopes": ["documents:read", "documents:write"]
  }'
```

#### Available Scopes

- `documents:read`: View documents
- `documents:write`: Create and update documents
- `documents:approve`: Approve document changes
- `tasks:read`: View tasks
- `tasks:write`: Create and update tasks
- `users:read`: View user information
- `users:write`: Create and update users (admin only)

#### Modifying User Permissions

Direct database modification (for emergency access):

```bash
docker-compose exec db psql -U docuser docdb -c "UPDATE users SET scopes = ARRAY['documents:read', 'documents:write', 'documents:approve', 'tasks:read', 'tasks:write', 'users:read'] WHERE username = 'admin';"
```

### Secret Management

#### Production Secrets

For production deployments:

1. **Use environment variables** instead of `.env` file
2. **Use a secrets management system** (HashiCorp Vault, AWS Secrets Manager, etc.)
3. **Rotate JWT secrets** periodically

#### Database Credentials

For production:

1. Create a dedicated database user with limited permissions
2. Use strong, randomly generated passwords
3. Consider using database connection pooling

## Performance Optimization

### Embedding Model Selection

The choice of embedding model affects search quality, performance, and resource usage.

#### Available Models

| Model | Dimensions | Size | Quality | Speed |
|-------|------------|------|---------|-------|
| all-MiniLM-L6-v2 | 384 | Small | Good | Fast |
| all-mpnet-base-v2 | 768 | Medium | Better | Medium |
| instructor-xl | 768 | Large | Best | Slow |

#### Changing Models

1. Update `.env`:
   ```
   EMBEDDING_MODEL=all-mpnet-base-v2
   EMBEDDING_DIM=768
   ```

2. Restart the API server:
   ```bash
   docker-compose restart api
   ```

3. Reindex documents (optional):
   ```bash
   # Clear embeddings to force regeneration
   docker-compose exec db psql -U docuser docdb -c "UPDATE documents SET embedding = NULL;"
   ```

### Search Optimization

#### Similarity Threshold

Adjust the similarity threshold in `.env`:

```
SIMILARITY_THRESHOLD=0.7
```

Lower values (e.g., 0.5) increase recall but may reduce precision.
Higher values (e.g., 0.8) increase precision but may reduce recall.

#### Maximum Results

Set the maximum search results:

```
MAX_SEARCH_RESULTS=10
```

#### Search Strategy

Configure search strategies in `api/services/search_service.py`:

```python
# Balance precision and recall (default)
SEARCH_STRATEGY = "balanced"

# Prioritize precision (exact matches)
SEARCH_STRATEGY = "precision"

# Prioritize recall (more results)
SEARCH_STRATEGY = "recall"

# Optimize for speed
SEARCH_STRATEGY = "speed"
```

### Caching Strategy

DokuCORE implements caching for search results to improve performance.

#### Cache Configuration

Configure caching in `.env`:

```
SEARCH_CACHE_ENABLED=true
SEARCH_CACHE_TTL=3600  # Time-to-live in seconds
SEARCH_CACHE_MAX_SIZE=1000  # Maximum items in cache
```

#### Cache Statistics

View cache performance:

```bash
curl http://localhost:9000/search/cache/stats
```

#### Clear Cache

If needed, clear the search cache:

```bash
curl -X POST http://localhost:9000/search/cache/clear
```

## Troubleshooting

### Common Issues

#### API Server Won't Start

**Symptoms:**
- `docker-compose ps` shows api container stopping immediately
- Logs show connection errors

**Possible causes and solutions:**

1. **Database connection issues**:
   ```
   Check database URL in .env
   Ensure database container is running
   ```

2. **Port conflicts**:
   ```
   Check if port 9000 is already in use
   Change API_PORT in .env if needed
   ```

3. **Missing dependencies**:
   ```
   Check api/requirements.txt
   Rebuild API container: docker-compose build api
   ```

#### Search Not Working Properly

**Symptoms:**
- Searches return no results or irrelevant results
- Embedding model errors in logs

**Possible causes and solutions:**

1. **Embedding model issues**:
   ```
   Check embedding model health: curl http://localhost:9000/health/embedding
   Verify EMBEDDING_MODEL and EMBEDDING_DIM in .env
   Restart API server: docker-compose restart api
   ```

2. **Index problems**:
   ```
   Clear embeddings to force regeneration: 
   docker-compose exec db psql -U docuser docdb -c "UPDATE documents SET embedding = NULL;"
   ```

#### Code Monitor Not Detecting Changes

**Symptoms:**
- Code changes not generating tasks
- No activity in code monitor logs

**Possible causes and solutions:**

1. **Repository path issues**:
   ```
   Check REPO_PATH in .env
   Verify repository is mounted correctly in docker-compose.yml
   ```

2. **Git configuration**:
   ```
   Ensure the repository is valid: docker-compose exec code-monitor git -C /app/repo status
   Check branch configuration
   ```

3. **API connectivity**:
   ```
   Verify API_URL in .env
   Check API server is running
   ```

### Diagnostic Procedures

#### Database Connectivity Check

```bash
docker-compose exec api python -c "
import psycopg2
from os import environ
try:
    conn = psycopg2.connect(environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### Embedding Model Check

```bash
docker-compose exec api python -c "
from sentence_transformers import SentenceTransformer
model_name = 'all-MiniLM-L6-v2'
try:
    model = SentenceTransformer(model_name)
    embedding = model.encode('Test sentence')
    print(f'Model loaded successfully. Embedding dimension: {len(embedding)}')
except Exception as e:
    print(f'Model loading failed: {e}')
"
```

#### API Endpoint Test

```bash
# Test health endpoint
curl http://localhost:9000/health

# Test authentication
TOKEN=$(curl -s -X POST http://localhost:9000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=securepassword" | jq -r '.access_token')

echo "Token: $TOKEN"

# Test document access
curl -H "Authorization: Bearer $TOKEN" http://localhost:9000/documents/
```

### Recovery Procedures

#### API Server Recovery

If the API server fails:

1. Check logs:
   ```bash
   docker-compose logs api
   ```

2. Repair configuration issues

3. Restart the service:
   ```bash
   docker-compose restart api
   ```

4. If problems persist, rebuild:
   ```bash
   docker-compose build api
   docker-compose up -d api
   ```

#### Database Recovery

For database issues:

1. Stop all services:
   ```bash
   docker-compose down
   ```

2. Restore from backup:
   ```bash
   # Start database only
   docker-compose up -d db
   
   # Wait for database to start
   sleep 10
   
   # Restore backup
   cat backup_20250517.sql | docker-compose exec -T db psql -U docuser docdb
   
   # Start other services
   docker-compose up -d
   ```

#### Complete System Recovery

For catastrophic failures:

1. Stop all services:
   ```bash
   docker-compose down -v  # Remove volumes if corrupted
   ```

2. Recreate from scratch:
   ```bash
   # Rebuild images
   docker-compose build
   
   # Start database
   docker-compose up -d db
   
   # Wait for database
   sleep 10
   
   # Run migrations
   ./run_migrations.sh
   
   # Start remaining services
   docker-compose up -d
   
   # Create admin user
   curl -X POST http://localhost:9000/auth/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "password": "securepassword",
       "full_name": "Admin User",
       "scopes": ["documents:read", "documents:write", "tasks:read", "tasks:write", "users:read", "documents:approve"]
     }'
   ```

## Upgrading DokuCORE

### Minor Upgrades

For minor version upgrades:

1. Pull the latest code:
   ```bash
   git pull origin main
   ```

2. Apply database migrations:
   ```bash
   ./run_migrations.sh
   ```

3. Rebuild and restart services:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

### Major Upgrades

For major version upgrades:

1. Back up your data:
   ```bash
   docker-compose exec db pg_dump -U docuser docdb > backup_pre_upgrade.sql
   cp .env .env.backup
   ```

2. Check release notes for breaking changes

3. Pull the new version:
   ```bash
   git fetch --tags
   git checkout v2.0.0  # Replace with target version
   ```

4. Update configuration:
   ```bash
   # Compare with example config
   diff .env.backup .env.example
   
   # Update .env
   nano .env
   ```

5. Run migrations:
   ```bash
   ./run_migrations.sh
   ```

6. Rebuild and restart:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

7. Verify upgrade:
   ```bash
   # Check health
   curl http://localhost:9000/health
   
   # Check version
   curl http://localhost:9000/health | jq '.config.version'
   ```

## Appendix

### Environment Variable Reference

| Variable | Description | Default | Required | 
|----------|-------------|---------|----------|
| POSTGRES_USER | PostgreSQL username | docuser | Yes |
| POSTGRES_PASSWORD | PostgreSQL password | docpassword | Yes |
| POSTGRES_DB | PostgreSQL database name | docdb | Yes |
| API_PORT | Port for API server | 9000 | Yes |
| DATABASE_URL | PostgreSQL connection string | postgresql://docuser:docpassword@db:5432/docdb | Yes |
| REPO_PATH | Path to monitored Git repository | /app/repo | Yes |
| API_URL | URL for API server | http://api:9000 | Yes |
| CHECK_INTERVAL | Code monitor check interval (seconds) | 300 | No |
| EMBEDDING_MODEL | Sentence transformer model | all-MiniLM-L6-v2 | No |
| EMBEDDING_DIM | Embedding dimensions | 384 | No |
| SIMILARITY_THRESHOLD | Minimum similarity score for search | 0.7 | No |
| MAX_SEARCH_RESULTS | Maximum search results | 10 | No |
| JWT_SECRET_KEY | Secret key for JWT tokens | your-secret-key-change-in-production | Yes |
| JWT_TOKEN_EXPIRE_MINUTES | JWT token expiration time | 30 | No |
| LOG_LEVEL | Logging level | INFO | No |
| SEARCH_CACHE_ENABLED | Enable search result caching | true | No |
| SEARCH_CACHE_TTL | Cache time-to-live (seconds) | 3600 | No |
| SEARCH_CACHE_MAX_SIZE | Maximum cache size (items) | 1000 | No |
| WEBHOOK_ENABLED | Enable webhook notifications | false | No |
| WEBHOOK_URL | Webhook target URL | | Only if webhooks enabled |
| LLM_API_URL | LLM API endpoint for code analysis | | No |
| LLM_API_KEY | LLM API authentication key | | No |

### Useful Commands

#### Docker Commands

```bash
# View container logs
docker-compose logs -f [service]

# Execute commands in containers
docker-compose exec api bash
docker-compose exec db psql -U docuser docdb

# View container resource usage
docker stats

# Restart specific service
docker-compose restart [service]

# Rebuild service
docker-compose build [service]
```

#### Database Commands

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U docuser docdb

# Backup database
docker-compose exec db pg_dump -U docuser docdb > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U docuser docdb

# Check PostgreSQL logs
docker-compose logs -f db

# View table sizes
docker-compose exec db psql -U docuser docdb -c "SELECT pg_size_pretty(pg_total_relation_size(relid)) AS size, relname FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
```

#### API Commands

```bash
# Get auth token
curl -X POST http://localhost:9000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=securepassword"

# Create document
curl -X POST http://localhost:9000/documents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Document",
    "path": "/docs/sample.md",
    "content": "# Sample Document\n\nThis is a sample document."
  }'

# Search documents
curl "http://localhost:9000/search/?query=sample+document&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### Log Level Reference

Adjust the `LOG_LEVEL` in `.env` to control logging verbosity:

| Level | Description | Use Case |
|-------|-------------|----------|
| DEBUG | Most detailed information | Development, troubleshooting specific issues |
| INFO | General operational information | Normal operation, monitoring |
| WARNING | Potential issues that don't affect operation | Production default, looking for potential problems |
| ERROR | Error events that allow continued operation | Minimal logging, error tracking |
| CRITICAL | Critical errors that may lead to failure | Minimal logging, critical alerts only |