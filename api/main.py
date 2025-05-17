import os
import logging
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from sentence_transformers import SentenceTransformer

from .routers import (
    document_router, 
    task_router, 
    search_router,
    auth_router,
    version_router,
    visualization_router,
    DocumentRouter,
    TaskRouter,
    SearchRouter,
    VersionRouter
)
from .services.document_service import DocumentService
from .services.task_service import TaskService
from .services.search_service import SearchService
from .mcp_tools import MCPTools
from .utils import config, setup_middleware

# Setup logging (now handled by config)
logger = logging.getLogger(__name__)

# Create FastAPI application with OpenAPI documentation
app = FastAPI(
    title="AI Documentation System",
    description="An AI-supported documentation system that provides semantic understanding of documentation content",
    version="0.1.0",
    openapi_tags=[
        {"name": "documents", "description": "Operations with documentation"},
        {"name": "tasks", "description": "Operations with documentation tasks"},
        {"name": "search", "description": "Search functionality"},
        {"name": "visualization", "description": "Index visualization tools"},
        {"name": "health", "description": "Health check endpoints"},
    ],
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Initialize MCP server
mcp = FastApiMCP(app)

# Apply middleware
setup_middleware(app)

# Initialize embedding model
model = SentenceTransformer(config.embedding_model_name)

# Initialize services
document_service = DocumentService(model)
task_service = TaskService()
search_service = SearchService(model)

# Initialize MCP tools
mcp_tools = MCPTools(mcp, document_service, task_service, search_service)

# Initialize routers
document_router_instance = DocumentRouter(model)
task_router_instance = TaskRouter()
search_router_instance = SearchRouter(model)
version_router_instance = VersionRouter()

# Include routers
app.include_router(document_router)
app.include_router(task_router)
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(version_router)
app.include_router(visualization_router)

# Mount MCP server
mcp.mount()

# Application startup event
@app.on_event("startup")
async def startup_event():
    logger.info("AI Documentation System started")
    logger.info(f"Documentation API running on port: {os.environ.get('API_PORT', 9000)}")

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint that returns the overall system status.
    
    Returns:
        dict: System status and configuration information.
    """
    return {"status": "ok", "config": config.get_config_dict()}

@app.get("/health/db", tags=["health"])
async def db_health_check():
    """
    Database health check endpoint.
    
    Returns:
        dict: Database connection status.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            return {"status": "ok", "message": "Database connection successful"}
        else:
            return {"status": "error", "message": "Database returned unexpected result"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}

@app.get("/health/embedding", tags=["health"])
async def embedding_health_check():
    """
    Embedding model health check endpoint.
    
    Returns:
        dict: Embedding model status.
    """
    try:
        # Test the embedding model with a simple text
        test_text = "Test embedding model"
        embedding = model.encode(test_text)
        
        return {
            "status": "ok", 
            "message": "Embedding model is working correctly",
            "model": config.embedding_model_name,
            "embedding_dimension": len(embedding)
        }
    except Exception as e:
        logger.error(f"Embedding model health check failed: {str(e)}")
        return {"status": "error", "message": f"Embedding model failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)