import os
import logging
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from sentence_transformers import SentenceTransformer

from .routers import (
    document_router, 
    task_router, 
    search_router,
    DocumentRouter,
    TaskRouter,
    SearchRouter
)
from .services.document_service import DocumentService
from .services.task_service import TaskService
from .services.search_service import SearchService
from .mcp_tools import MCPTools

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(title="AI Documentation System")

# Initialize MCP server
mcp = FastApiMCP(app)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

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

# Include routers
app.include_router(document_router)
app.include_router(task_router)
app.include_router(search_router)

# Mount MCP server
mcp.mount()

# Application startup event
@app.on_event("startup")
async def startup_event():
    logger.info("AI Documentation System started")
    logger.info(f"Documentation API running on port: {os.environ.get('API_PORT', 9000)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("API_PORT", 9000)))