import logging
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer

from ..utils.db import get_db_connection
from .markdown_parser import extract_hierarchy_from_markdown
from .keyword_extractor import extract_keywords
from .embedding_config import EmbeddingOptimizer, EmbeddingModelType, EmbeddingConfig
from .relationship_thresholds import RelationshipManager, RelationshipType

logger = logging.getLogger(__name__)

class HierarchicalIndexer:
    """Hierarchical indexing engine for documents."""
    
    def __init__(self, embedding_model: SentenceTransformer, embedding_config: Optional[EmbeddingConfig] = None):
        """
        Initialize the hierarchical indexer.
        
        Args:
            embedding_model: SentenceTransformer model for text embeddings.
            embedding_config: Optional configuration for the embedding model.
        """
        self.model = embedding_model
        
        if embedding_config is None:
            # Get default optimized config
            self.config = EmbeddingOptimizer.get_optimal_config(
                EmbeddingModelType.MINILM, 
                use_case="hierarchical_indexing"
            )
        else:
            self.config = embedding_config
            
        # Apply configuration to the model
        self._configure_model()
    
    def _configure_model(self):
        """Configure the embedding model with optimal parameters."""
        # Set max sequence length
        self.model.max_seq_length = self.config.max_sequence_length
        
        # Set device
        if hasattr(self.model, '_target_device'):
            self.model._target_device = self.config.device
        
        # Configure batch size for encoding
        self.encode_batch_size = self.config.batch_size
        
        # Log configuration
        logger.info(f"Configured embedding model: {self.config.model_name}")
        logger.info(f"Max sequence length: {self.config.max_sequence_length}")
        logger.info(f"Batch size: {self.config.batch_size}")
        logger.info(f"Device: {self.config.device}")
    
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
                text_to_encode = f"{node['title']} {node['content']}"
                
                # Apply document prefix if configured
                if self.config.document_prefix:
                    text_to_encode = self.config.document_prefix + text_to_encode
                
                embedding = self.model.encode(
                    text_to_encode,
                    batch_size=self.encode_batch_size,
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=False
                ).tolist()

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
                    # Apply query prefix for keyword embeddings if configured
                    keyword_text = keyword
                    if self.config.query_prefix:
                        keyword_text = self.config.query_prefix + keyword
                    
                    keyword_embedding = self.model.encode(
                        keyword_text,
                        batch_size=self.encode_batch_size,
                        normalize_embeddings=self.config.normalize_embeddings,
                        show_progress_bar=False
                    ).tolist()
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
                    
                    # Calculate sibling strength based on sequence distance
                    level_distance = 0  # Same level
                    sequence_distance = abs(node1_key[1] - node2_key[1])
                    
                    strength = RelationshipManager.calculate_sibling_strength(
                        level_distance, sequence_distance
                    )
                    
                    # Only create relationship if strength is above threshold
                    if RelationshipManager.should_create_relationship(
                        RelationshipType.SIBLING, strength
                    ):
                        cursor.execute(
                            """INSERT INTO document_relationships (source_id, target_id, relationship_type, strength)
                            VALUES (%s, %s, %s, %s)""",
                            (node1_id, node2_id, "sibling", strength)
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
                cosine_similarity = cursor.fetchone()[0]
                
                # Calculate semantic strength using threshold manager
                strength = RelationshipManager.calculate_semantic_strength(cosine_similarity)
                
                # Only create relationship if strength is above threshold
                if RelationshipManager.should_create_relationship(
                    RelationshipType.SEMANTIC, strength
                ):
                    cursor.execute(
                        """INSERT INTO document_relationships (source_id, target_id, relationship_type, strength)
                        VALUES (%s, %s, %s, %s)""",
                        (node1_id, node2_id, "semantic", strength)
                    )