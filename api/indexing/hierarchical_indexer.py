import logging
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer

from ..utils.db import get_db_connection
from .markdown_parser import extract_hierarchy_from_markdown
from .keyword_extractor import extract_keywords

logger = logging.getLogger(__name__)

class HierarchicalIndexer:
    """Hierarchical indexing engine for documents."""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize the hierarchical indexer.
        
        Args:
            embedding_model: SentenceTransformer model for text embeddings.
        """
        self.model = embedding_model
    
    def generate_hierarchical_index(self, doc_id: int, content: str) -> bool:
        """
        Generate hierarchical index for a document.
        
        Args:
            doc_id (int): Document ID.
            content (str): Document content in markdown format.
            
        Returns:
            bool: True if indexing was successful, False otherwise.
        """
        try:
            # Delete existing hierarchy
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_keywords WHERE node_id IN (SELECT id FROM document_hierarchy WHERE document_id = %s)", (doc_id,))
            cursor.execute("DELETE FROM document_relationships WHERE source_id IN (SELECT id FROM document_hierarchy WHERE document_id = %s) OR target_id IN (SELECT id FROM document_hierarchy WHERE document_id = %s)", (doc_id, doc_id))
            cursor.execute("DELETE FROM document_hierarchy WHERE document_id = %s", (doc_id,))
            conn.commit()

            # Extract hierarchy from markdown content
            hierarchy_nodes = extract_hierarchy_from_markdown(content)

            # Save hierarchy nodes
            node_ids = {}  # level+seq -> node_id mapping

            for node in hierarchy_nodes:
                # Generate embedding for the node
                # Reason: We combine title and content to create a more comprehensive embedding
                embedding = self.model.encode(f"{node['title']} {node['content']}").tolist()

                # Determine parent id
                # Reason: We need to find the closest parent node by level and sequence
                parent_id = None
                for potential_parent in sorted([(n["level"], n["seq_num"]) for n in hierarchy_nodes 
                                             if n["level"] < node["level"] and n["seq_num"] < node["seq_num"]], 
                                             reverse=True):
                    if potential_parent in node_ids:
                        parent_id = node_ids[potential_parent]
                        break

                # Save node
                cursor.execute(
                    """INSERT INTO document_hierarchy (document_id, parent_id, title, content, embedding, doc_level, seq_num)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (doc_id, parent_id, node["title"], node["content"], embedding, node["level"], node["seq_num"])
                )

                node_id = cursor.fetchone()[0]
                node_ids[(node["level"], node["seq_num"])] = node_id

                # Extract and save keywords
                keywords = extract_keywords(node["title"], node["content"])
                for keyword, importance in keywords.items():
                    keyword_embedding = self.model.encode(keyword).tolist()
                    cursor.execute(
                        """INSERT INTO document_keywords (node_id, keyword, embedding, importance)
                        VALUES (%s, %s, %s, %s)""",
                        (node_id, keyword, keyword_embedding, importance)
                    )

            # Generate relationships between nodes
            self._create_node_relationships(conn, cursor, doc_id, node_ids, hierarchy_nodes)

            conn.commit()
            cursor.close()
            conn.close()

            return True
        except Exception as e:
            logger.error(f"Error generating hierarchical index: {str(e)}")
            return False
            
    def _create_node_relationships(self, conn, cursor, doc_id: int, node_ids: Dict, hierarchy_nodes: List[Dict[str, Any]]):
        """
        Create relationships between document hierarchy nodes.
        
        Args:
            conn: Database connection.
            cursor: Database cursor.
            doc_id (int): Document ID.
            node_ids (Dict): Mapping of (level, seq_num) to node IDs.
            hierarchy_nodes (List[Dict[str, Any]]): List of hierarchy nodes.
        """
        for i, node1_key in enumerate(node_ids.keys()):
            node1_id = node_ids[node1_key]
            
            # Connect nodes at the same level with "sibling" relationship
            # Reason: Nodes at the same level are likely to be related
            for j, node2_key in enumerate(node_ids.keys()):
                if i != j and node1_key[0] == node2_key[0]:  # Same level
                    node2_id = node_ids[node2_key]
                    cursor.execute(
                        """INSERT INTO document_relationships (source_id, target_id, relationship_type, strength)
                        VALUES (%s, %s, %s, %s)""",
                        (node1_id, node2_id, "sibling", 0.5)
                    )

            # Connect semantically similar nodes
            # Reason: Find nodes with similar content regardless of hierarchy
            cursor.execute(
                """SELECT id, embedding FROM document_hierarchy
                WHERE document_id = %s AND id != %s""",
                (doc_id, node1_id)
            )

            for row in cursor.fetchall():
                node2_id, node2_embedding = row
                # Calculate cosine similarity
                cursor.execute(
                    """SELECT 1 - (embedding <=> %s) as similarity FROM document_hierarchy WHERE id = %s""",
                    (node2_embedding, node1_id)
                )
                similarity = cursor.fetchone()[0]

                # Only connect if similarity is high enough (0.7 or greater)
                if similarity > 0.7:
                    cursor.execute(
                        """INSERT INTO document_relationships (source_id, target_id, relationship_type, strength)
                        VALUES (%s, %s, %s, %s)""",
                        (node1_id, node2_id, "semantic", similarity)
                    )