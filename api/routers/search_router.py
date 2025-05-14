import logging
from fastapi import APIRouter, Depends
from sentence_transformers import SentenceTransformer

from ..services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

def get_search_service(model: SentenceTransformer = None):
    """Dependency to get search service."""
    return SearchService(model)

class SearchRouter:
    """Router for search endpoints."""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize the search router.
        
        Args:
            embedding_model: SentenceTransformer model for query embeddings.
        """
        self.model = embedding_model
        
        # Use closure to pass model to the dependency
        def get_service():
            return get_search_service(self.model)
        
        # Register routes
        @router.get("/")
        def search_endpoint(query: str, limit: int = 5, service: SearchService = Depends(get_service)):
            """Search in documentation."""
            try:
                return service.search_docs(query, limit)
            except Exception as e:
                logger.error(f"Error searching: {str(e)}")
                return [{"error": str(e)}]