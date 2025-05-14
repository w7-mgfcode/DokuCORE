import logging
from typing import List, Dict, Any, Optional
from fastapi_mcp import FastApiMCP

from .services.document_service import DocumentService
from .services.task_service import TaskService
from .services.search_service import SearchService

logger = logging.getLogger(__name__)

class MCPTools:
    """MCP tools for AI integration."""
    
    def __init__(self, mcp: FastApiMCP, document_service: DocumentService, task_service: TaskService, search_service: SearchService):
        """
        Initialize MCP tools.
        
        Args:
            mcp: FastApiMCP instance.
            document_service: Document service.
            task_service: Task service.
            search_service: Search service.
        """
        self.mcp = mcp
        self.document_service = document_service
        self.task_service = task_service
        self.search_service = search_service
        
        # Register MCP tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools."""
        
        @self.mcp.tool()
        def list_docs() -> List[Dict[str, Any]]:
            """List all available markdown documentation files."""
            logger.info("list_docs MCP function called")
            try:
                return self.document_service.list_documents()
            except Exception as e:
                logger.error(f"Error executing list_docs function: {str(e)}")
                return [{"error": str(e)}]

        @self.mcp.tool()
        def get_doc_content(doc_id: int) -> str:
            """Get content of a specific markdown documentation file."""
            logger.info(f"get_doc_content MCP function called: {doc_id}")
            try:
                content = self.document_service.get_document_content(doc_id)
                if not content:
                    return f"Error: Document with ID {doc_id} not found"
                return content
            except Exception as e:
                logger.error(f"Error executing get_doc_content function: {str(e)}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        def search_docs(query: str, limit: int = 5) -> List[Dict[str, Any]]:
            """Intelligent, hierarchical search in documentation based on the query."""
            logger.info(f"search_docs MCP function called: {query}")
            try:
                return self.search_service.search_docs(query, limit)
            except Exception as e:
                logger.error(f"Error executing search_docs function: {str(e)}")
                return [{"error": str(e)}]

        @self.mcp.tool()
        def get_document_structure(doc_id: int) -> Dict[str, Any]:
            """Get hierarchical structure of a document."""
            logger.info(f"get_document_structure MCP function called: {doc_id}")
            try:
                return self.document_service.get_document_structure(doc_id)
            except Exception as e:
                logger.error(f"Error executing get_document_structure function: {str(e)}")
                return {"error": str(e)}

        @self.mcp.tool()
        def update_document(doc_id: int, new_content: str, changed_by: str = "AI") -> Dict[str, Any]:
            """Update content of a document and reindex it."""
            logger.info(f"update_document MCP function called: {doc_id}")
            try:
                return self.document_service.update_document(doc_id, new_content, changed_by)
            except Exception as e:
                logger.error(f"Error executing update_document function: {str(e)}")
                return {"status": "error", "message": str(e)}

        @self.mcp.tool()
        def create_task(title: str, description: str, doc_id: Optional[int] = None, code_path: Optional[str] = None) -> Dict[str, Any]:
            """Create a new task related to documentation update."""
            logger.info(f"create_task MCP function called: {title}")
            try:
                return self.task_service.create_task(title, description, doc_id, code_path)
            except Exception as e:
                logger.error(f"Error executing create_task function: {str(e)}")
                return {"status": "error", "message": str(e)}

        @self.mcp.tool()
        def get_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
            """Get tasks, optionally filtered by status."""
            logger.info(f"get_tasks MCP function called: {status}")
            try:
                return self.task_service.get_tasks(status)
            except Exception as e:
                logger.error(f"Error executing get_tasks function: {str(e)}")
                return [{"error": str(e)}]