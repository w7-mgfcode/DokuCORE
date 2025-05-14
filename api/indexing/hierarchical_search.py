import logging
from typing import List, Dict, Any
import psycopg2.extras
from sentence_transformers import SentenceTransformer

from ..utils.db import get_db_connection

logger = logging.getLogger(__name__)

class HierarchicalSearch:
    """Search engine for hierarchical document index."""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize the hierarchical search engine.
        
        Args:
            embedding_model: SentenceTransformer model for query embeddings.
        """
        self.model = embedding_model
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hierarchical search in the document index.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            
        Returns:
            List[Dict[str, Any]]: Search results sorted by relevance.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Generate embedding for query
            query_embedding = self.model.encode(query).tolist()

            # Step 1: Keyword-based search
            # Reason: Direct keyword matches are often highly relevant
            cursor.execute(
                """SELECT k.node_id, k.keyword, k.importance, h.title, h.content, h.document_id,
                        1 - (k.embedding <=> %s) as similarity
                FROM document_keywords k
                JOIN document_hierarchy h ON k.node_id = h.id
                WHERE k.keyword ILIKE %s
                ORDER BY similarity DESC
                LIMIT %s""",
                (query_embedding, f"%{query}%", limit)
            )

            keyword_results = cursor.fetchall()

            # Step 2: Semantic search in hierarchical index
            # Reason: Find semantically related content even without exact keyword matches
            cursor.execute(
                """SELECT h.id, h.title, h.content, h.document_id, h.doc_level, h.parent_id,
                        1 - (h.embedding <=> %s) as similarity
                FROM document_hierarchy h
                ORDER BY similarity DESC
                LIMIT %s""",
                (query_embedding, limit)
            )

            semantic_results = cursor.fetchall()

            # Step 3: Combine and rank results
            combined_results = self._combine_search_results(
                keyword_results, 
                semantic_results, 
                limit,
                cursor
            )

            cursor.close()
            conn.close()

            return combined_results
        except Exception as e:
            logger.error(f"Error during hierarchical search: {str(e)}")
            return []

    def _combine_search_results(self, keyword_results, semantic_results, limit, cursor) -> List[Dict[str, Any]]:
        """
        Combine keyword and semantic search results, add related nodes.
        
        Args:
            keyword_results: Keyword search results.
            semantic_results: Semantic search results.
            limit (int): Maximum number of results to return.
            cursor: Database cursor.
            
        Returns:
            List[Dict[str, Any]]: Combined search results.
        """
        combined_results = set()
        ranked_results = []

        # Add keyword matches
        # Reason: Keyword matches get priority and are weighted by importance
        for row in keyword_results:
            node_id = row["node_id"]
            if node_id not in combined_results:
                combined_results.add(node_id)
                ranked_results.append({
                    "id": node_id,
                    "title": row["title"],
                    "content": row["content"],
                    "document_id": row["document_id"],
                    "relevance": row["similarity"] * (1 + row["importance"]),  # Weight by importance
                    "match_type": "keyword",
                    "keyword": row["keyword"]
                })

        # Add semantic matches
        # Reason: Add semantically related content
        for row in semantic_results:
            node_id = row["id"]
            if node_id not in combined_results:
                combined_results.add(node_id)
                ranked_results.append({
                    "id": node_id,
                    "title": row["title"],
                    "content": row["content"],
                    "document_id": row["document_id"],
                    "relevance": row["similarity"],
                    "match_type": "semantic",
                    "parent_id": row["parent_id"],
                    "level": row["doc_level"]
                })

        # Read related nodes for highest relevance results
        if ranked_results:
            # Sort results by relevance
            ranked_results = sorted(ranked_results, key=lambda x: x["relevance"], reverse=True)

            # Add related nodes for top N highest relevance results
            # Reason: Expand results with contextually related content
            top_n = min(3, len(ranked_results))
            for i in range(top_n):
                # Check if list is not empty and index is valid
                if i < len(ranked_results):
                    cursor.execute(
                        """SELECT r.target_id, r.relationship_type, r.strength,
                                h.title, h.content, h.document_id
                        FROM document_relationships r
                        JOIN document_hierarchy h ON r.target_id = h.id
                        WHERE r.source_id = %s
                        ORDER BY r.strength DESC
                        LIMIT 3""",
                        (ranked_results[i]["id"],)
                    )

                    for rel_row in cursor.fetchall():
                        target_id = rel_row["target_id"]
                        if target_id not in combined_results:
                            combined_results.add(target_id)
                            ranked_results.append({
                                "id": target_id,
                                "title": rel_row["title"],
                                "content": rel_row["content"],
                                "document_id": rel_row["document_id"],
                                "relevance": ranked_results[i]["relevance"] * rel_row["strength"],
                                "match_type": f"related-{rel_row['relationship_type']}",
                                "relation_to": ranked_results[i]["id"]
                            })

        # Final sorting and limiting of results
        final_results = sorted(ranked_results, key=lambda x: x["relevance"], reverse=True)[:limit]

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