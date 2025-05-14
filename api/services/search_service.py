import logging
from typing import List, Dict, Any
import psycopg2.extras
import hashlib
from sentence_transformers import SentenceTransformer

from ..indexing.hierarchical_search import HierarchicalSearch
from ..utils import cache, cached, config

logger = logging.getLogger(__name__)

class SearchService:
    """Service for search operations."""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize the search service.
        
        Args:
            embedding_model: SentenceTransformer model for query embeddings.
        """
        self.model = embedding_model
        self.search_engine = HierarchicalSearch(embedding_model)
    
    # Use the cached decorator to cache search results
    # Reason: Search operations are expensive and results often reused
    @cached(
        ttl_seconds=300,  # Cache for 5 minutes
        key_prefix="search",
        key_func=lambda self, query, limit=5: f"search:{hashlib.md5(query.encode()).hexdigest()}:{limit}"
    )
    def search_docs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search documentation with hierarchical context.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            
        Returns:
            List[Dict[str, Any]]: Search results formatted for display.
        """
        try:
            # Execute hierarchical search
            search_results = self.search_engine.search(query, limit)

            # Transform results for display
            results = []
            for result in search_results:
                # Transform relevance score to percentage (clamp to 0-1 range to be safe)
                relevance_pct = int(max(0, min(1, result.get("relevance", 0))) * 100)

                # Generate preview from content
                preview = result.get("content", "")
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                else:
                    preview = preview  # Use full content if shorter than 200 chars

                # Readable match type format
                match_type = result.get("match_type", "unknown")
                match_type_display = "Unknown match"
                if match_type == "keyword":
                    match_type_display = "Keyword match"
                elif match_type == "semantic":
                    match_type_display = "Semantic match"
                elif match_type.startswith("related"):
                    rel_type = match_type.split("-")[1]
                    match_type_display = f"Related content ({rel_type})"

                # Add result
                results.append({
                    # Use doc_title for 'id' field as requested in the example
                    "id": result.get("doc_title", "N/A"),
                    "title": result.get("title", "N/A"),
                    "path": result.get("doc_path", "N/A"),
                    "preview": preview,
                    "relevance": f"{relevance_pct}%",
                    "match_type": match_type_display,
                    "document_id": result.get("document_id")
                })

            return results
        except Exception as e:
            logger.error(f"Error searching docs: {str(e)}")
            return [{"error": str(e)}]
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get search cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics.
        """
        return cache.stats()