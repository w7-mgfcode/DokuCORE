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
                
        @router.get("/cache/stats")
        def cache_stats_endpoint(service: SearchService = Depends(get_service)):
            """Get search cache statistics."""
            return service.get_cache_stats()
            
        @router.post("/cache/clear")
        def clear_cache_endpoint(service: SearchService = Depends(get_service)):
            """Clear the search cache."""
            cache.clear()
            return {"status": "success", "message": "Search cache cleared"}
            
        @router.get("/benchmark")
        def benchmark_search(query: str, iterations: int = 5, service: SearchService = Depends(get_service)):
            """
            Benchmark search performance.
            
            This endpoint runs the search multiple times and returns timing information.
            Useful for performance testing and optimization.
            
            Args:
                query: Search query to benchmark
                iterations: Number of search iterations to run
            """
            import time
            
            # Clear cache before benchmarking
            cache.clear()
            
            # Run the initial search (cold start)
            start_time = time.time()
            initial_results = service.search_docs(query)
            initial_time = time.time() - start_time
            
            # Run multiple iterations for cached performance
            cached_times = []
            for _ in range(iterations):
                start_time = time.time()
                service.search_docs(query)
                cached_times.append(time.time() - start_time)
            
            avg_cached_time = sum(cached_times) / len(cached_times) if cached_times else 0
            
            return {
                "query": query,
                "initial_time_ms": round(initial_time * 1000, 2),
                "avg_cached_time_ms": round(avg_cached_time * 1000, 2),
                "iterations": iterations,
                "speedup_factor": round(initial_time / avg_cached_time, 2) if avg_cached_time > 0 else "N/A",
                "result_count": len(initial_results),
                "cache_stats": service.get_cache_stats()
            }