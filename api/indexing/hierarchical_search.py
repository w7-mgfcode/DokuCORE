import logging
from typing import List, Dict, Any, Optional
import psycopg2.extras
import re
from sentence_transformers import SentenceTransformer

from ..utils.db import get_db_connection
from ..utils.config import config
from .search_optimizer import SearchOptimizer, SearchConfig, SearchStrategy

logger = logging.getLogger(__name__)

class HierarchicalSearch:
    """Search engine for hierarchical document index."""
    
    def __init__(self, embedding_model: SentenceTransformer, search_config: Optional[SearchConfig] = None):
        """
        Initialize the hierarchical search engine.
        
        Args:
            embedding_model: SentenceTransformer model for query embeddings.
            search_config: Optional search configuration for optimization.
        """
        self.model = embedding_model
        self.optimizer = SearchOptimizer()
        self.search_config = search_config
    
    def search(self, query: str, limit: int = 5, strategy: Optional[SearchStrategy] = None) -> List[Dict[str, Any]]:
        """
        Perform hierarchical search in the document index.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            strategy (Optional[SearchStrategy]): Search strategy to use.
            
        Returns:
            List[Dict[str, Any]]: Search results sorted by relevance.
        """
        try:
            # Get optimized configuration
            if self.search_config:
                config = self.search_config
            elif strategy:
                config = self.optimizer.get_config_for_strategy(strategy)
            else:
                config = self.optimizer.optimize_for_query_type(query)
            
            # Override limit if needed
            config.top_k = limit
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Query expansion if enabled
            expansion_terms = []
            if config.enable_query_expansion:
                expansion_terms = self.optimizer.get_query_expansion_terms(query, config=config)
            
            # Generate embedding for query with optimized parameters
            # Reason: Using normalized embeddings improves search consistency
            query_embedding = self.model.encode(
                query, 
                normalize_embeddings=True,  # Ensures consistent similarity calculation
                show_progress_bar=False     # Reduces overhead for short queries
            ).tolist()

            # Step 1: Extract and clean keywords from query
            # Reason: Breaking the query into individual keywords improves text search accuracy
            # Remove special chars and get words with appropriate length
            clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
            keywords = [kw.strip() for kw in clean_query.split() if len(kw.strip()) > 2]
            
            # Add expansion terms to keywords
            if expansion_terms:
                keywords.extend(expansion_terms)
            
            # Step 2: Hybrid search approach - combining exact match and vector search
            # Reason: This optimized query uses a hybrid approach that combines:
            # 1. Text search for exact matches (faster for common keywords)
            # 2. Vector similarity search for semantic understanding
            # The combined approach is faster and more accurate
            
            if keywords:
                # Build dynamic SQL conditions for keywords
                keyword_conditions = " OR ".join([f"k.keyword ILIKE '%{kw}%'" for kw in keywords[:5]])
                
                cursor.execute(
                    f"""SELECT k.node_id, k.keyword, k.importance, h.title, h.content, h.document_id,
                            1 - (k.embedding <=> %s) as similarity
                    FROM document_keywords k
                    JOIN document_hierarchy h ON k.node_id = h.id
                    WHERE ({keyword_conditions})
                    ORDER BY similarity DESC
                    LIMIT %s""",
                    (query_embedding, limit)
                )
            else:
                # Fallback to just vector search if no good keywords
                cursor.execute(
                    """SELECT k.node_id, k.keyword, k.importance, h.title, h.content, h.document_id,
                            1 - (k.embedding <=> %s) as similarity
                    FROM document_keywords k
                    JOIN document_hierarchy h ON k.node_id = h.id
                    ORDER BY similarity DESC
                    LIMIT %s""",
                    (query_embedding, limit)
                )

            keyword_results = cursor.fetchall()

            # Step 3: Semantic search in hierarchical index with improved performance
            # Reason: Add a similarity threshold to filter out low-relevance results early
            # This improves performance by reducing the number of results to process
            similarity_threshold = config.similarity_threshold
            
            cursor.execute(
                """SELECT h.id, h.title, h.content, h.document_id, h.doc_level, h.parent_id,
                        1 - (h.embedding <=> %s) as similarity
                FROM document_hierarchy h
                WHERE 1 - (h.embedding <=> %s) > %s
                ORDER BY similarity DESC
                LIMIT %s""",
                (query_embedding, query_embedding, similarity_threshold, config.top_k)
            )

            semantic_results = cursor.fetchall()

            # Step 3: Combine and rank results
            combined_results = self._combine_search_results(
                keyword_results, 
                semantic_results, 
                config,
                cursor
            )
            
            # Apply result diversity optimization if needed
            if len(combined_results) > 1:
                combined_results = self.optimizer.optimize_result_diversity(combined_results)

            cursor.close()
            conn.close()

            return combined_results
        except Exception as e:
            logger.error(f"Error during hierarchical search: {str(e)}")
            return []

    def _combine_search_results(self, keyword_results, semantic_results, config: SearchConfig, cursor) -> List[Dict[str, Any]]:
        """
        Combine keyword and semantic search results, add related nodes.
        
        Args:
            keyword_results: Keyword search results.
            semantic_results: Semantic search results.
            config: Search configuration.
            cursor: Database cursor.
            
        Returns:
            List[Dict[str, Any]]: Combined search results.
        """
        combined_results = set()
        ranked_results = []

        # Add keyword matches with optimized scoring
        # Reason: Keyword matches are generally more precise and should be weighted higher
        for row in keyword_results:
            node_id = row["node_id"]
            if node_id not in combined_results:
                combined_results.add(node_id)
                
                # Use optimizer for relevance calculation
                metadata = {
                    "has_keywords": True,
                    "importance": row["importance"]
                }
                
                relevance = self.optimizer.calculate_relevance_score(
                    row["similarity"],
                    "keyword",
                    config,
                    metadata
                )
                
                ranked_results.append({
                    "id": node_id,
                    "title": row["title"],
                    "content": row["content"],
                    "document_id": row["document_id"],
                    "relevance": relevance,
                    "match_type": "keyword",
                    "keyword": row["keyword"]
                })

        # Add semantic matches with optimized scoring
        # Reason: Filter low-quality semantic matches to improve result quality
        min_semantic_relevance = config.similarity_threshold
        
        for row in semantic_results:
            node_id = row["id"]
            if node_id not in combined_results and row["similarity"] >= min_semantic_relevance:
                combined_results.add(node_id)
                
                # Use optimizer for relevance calculation
                metadata = {
                    "is_title": row["title"].lower() in query.lower() if hasattr(self, 'query') else False,
                    "level": row["doc_level"]
                }
                
                relevance = self.optimizer.calculate_relevance_score(
                    row["similarity"],
                    "semantic",
                    config,
                    metadata
                )
                
                ranked_results.append({
                    "id": node_id,
                    "title": row["title"],
                    "content": row["content"],
                    "document_id": row["document_id"],
                    "relevance": relevance,
                    "match_type": "semantic",
                    "parent_id": row["parent_id"],
                    "level": row["doc_level"]
                })

        # Get parent/child relationships for top results
        # Reason: Add hierarchical context to improve result quality
        if ranked_results:
            # Sort results by relevance
            ranked_results = sorted(ranked_results, key=lambda x: x["relevance"], reverse=True)
            
            # Take only top results to optimize performance based on config
            # Reason: Processing too many results is expensive and provides diminishing returns
            max_to_process = min(config.max_depth, len(ranked_results))
            top_results = ranked_results[:max_to_process]
            
            # Batch query for related nodes to reduce database roundtrips
            # Reason: A single query is more efficient than multiple queries
            if top_results:
                source_ids = [result["id"] for result in top_results]
                source_ids_str = ",".join(str(id) for id in source_ids)
                
                # Only run the query if we have source IDs
                if source_ids_str:
                    cursor.execute(
                        f"""SELECT r.source_id, r.target_id, r.relationship_type, r.strength,
                                h.title, h.content, h.document_id
                        FROM document_relationships r
                        JOIN document_hierarchy h ON r.target_id = h.id
                        WHERE r.source_id IN ({source_ids_str})
                        AND r.strength > 0.6
                        ORDER BY r.strength DESC
                        LIMIT 10"""
                    )
                    
                    # Create a mapping of source_id to result for easy lookup
                    source_result_map = {result["id"]: result for result in top_results}
                    
                    for rel_row in cursor.fetchall():
                        target_id = rel_row["target_id"]
                        source_id = rel_row["source_id"]
                        
                        if target_id not in combined_results:
                            combined_results.add(target_id)
                            source_result = source_result_map.get(source_id)
                            if source_result:
                                ranked_results.append({
                                    "id": target_id,
                                    "title": rel_row["title"],
                                    "content": rel_row["content"],
                                    "document_id": rel_row["document_id"],
                                    "relevance": source_result["relevance"] * rel_row["strength"],
                                    "match_type": f"related-{rel_row['relationship_type']}",
                                    "relation_to": source_id
                                })

        # Final sorting and limiting of results
        final_results = sorted(ranked_results, key=lambda x: x["relevance"], reverse=True)[:config.top_k]

        # Add document data
        for result in final_results:
            doc_id = result["document_id"]
            cursor.execute("SELECT title, path FROM documents WHERE id = %s", (doc_id,))
            doc_row = cursor.fetchone()
            if doc_row:
                result["doc_title"] = doc_row["title"]
                result["doc_path"] = doc_row["path"]
            else:
                result["doc_title"] = "Unknown Document"
                result["doc_path"] = "N/A"
                
        return final_results