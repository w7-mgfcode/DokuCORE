import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer

from ..utils.db import get_db_connection
from ..indexing.hierarchical_indexer import HierarchicalIndexer

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document operations."""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize the document service.
        
        Args:
            embedding_model: SentenceTransformer model for text embeddings.
        """
        self.model = embedding_model
        self.indexer = HierarchicalIndexer(embedding_model)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all available documents.
        
        Returns:
            List[Dict[str, Any]]: List of documents.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT id, title, path FROM documents")
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            return [{"id": row["id"], "title": row["title"], "path": row["path"]} for row in results]
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def get_document_content(self, doc_id: int) -> Optional[str]:
        """
        Get content of a specific document.
        
        Args:
            doc_id (int): Document ID.
            
        Returns:
            Optional[str]: Document content or None if not found.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT content FROM documents WHERE id = %s", (doc_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result:
                return None
            return result["content"]
        except Exception as e:
            logger.error(f"Error getting document content: {str(e)}")
            return None
    
    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            doc_id (int): Document ID.
            
        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT id, title, path, content, last_modified, version FROM documents WHERE id = %s", (doc_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result:
                return None
            return dict(result)
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
    
    def create_document(self, title: str, path: str, content: str) -> Optional[Dict[str, Any]]:
        """
        Create a new document.
        
        Args:
            title (str): Document title.
            path (str): Document path.
            content (str): Document content.
            
        Returns:
            Optional[Dict[str, Any]]: Created document data or None if failed.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Generate embedding
            embedding = self.model.encode(content).tolist()

            cursor.execute(
                """INSERT INTO documents (title, path, content, embedding)
                VALUES (%s, %s, %s, %s) RETURNING id, title, path, content, last_modified, version""",
                (title, path, content, embedding)
            )

            result = cursor.fetchone()
            doc_id = result["id"]
            conn.commit()
            cursor.close()
            conn.close()

            # Generate hierarchical index for the document
            self.indexer.generate_hierarchical_index(doc_id, content)

            return dict(result)
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return None
    
    def update_document(self, doc_id: int, new_content: str, changed_by: str = "AI") -> Dict[str, Any]:
        """
        Update a document's content.
        
        Args:
            doc_id (int): Document ID.
            new_content (str): New document content.
            changed_by (str): Who made the change.
            
        Returns:
            Dict[str, Any]: Result of the update operation.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Get current version
            cursor.execute("SELECT version, content FROM documents WHERE id = %s", (doc_id,))
            result = cursor.fetchone()

            if not result:
                conn.close()
                return {"status": "error", "message": f"Document with ID {doc_id} not found"}

            current_version = result["version"]
            old_content = result["content"]

            # Generate new embedding
            embedding = self.model.encode(new_content).tolist()

            # Add to history
            cursor.execute(
                "INSERT INTO document_history (document_id, content, changed_by, version) VALUES (%s, %s, %s, %s)",
                (doc_id, old_content, changed_by, current_version)
            )

            # Update document
            cursor.execute(
                """UPDATE documents
                SET content = %s, embedding = %s, last_modified = CURRENT_TIMESTAMP, version = %s
                WHERE id = %s""",
                (new_content, embedding, current_version + 1, doc_id)
            )

            conn.commit()
            cursor.close()
            conn.close()

            # Regenerate hierarchical index for the document
            success = self.indexer.generate_hierarchical_index(doc_id, new_content)

            status = "success" if success else "warning"
            message = f"Document updated to version {current_version + 1}"
            if not success:
                message += ", but error occurred while regenerating hierarchical index"

            return {"status": status, "message": message}
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_document_structure(self, doc_id: int) -> Dict[str, Any]:
        """
        Get hierarchical structure of a document.
        
        Args:
            doc_id (int): Document ID.
            
        Returns:
            Dict[str, Any]: Document structure or error message.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Get document basic data
            cursor.execute("SELECT title, path FROM documents WHERE id = %s", (doc_id,))
            doc = cursor.fetchone()

            if not doc:
                conn.close()
                return {"error": f"Document with ID {doc_id} not found"}

            # Get hierarchy
            cursor.execute(
                """SELECT id, title, doc_level, parent_id, seq_num
                FROM document_hierarchy
                WHERE document_id = %s
                ORDER BY doc_level, seq_num""",
                (doc_id,)
            )

            nodes = cursor.fetchall()
            cursor.close()
            conn.close()

            # Build hierarchical structure
            node_dict = {node["id"]: {
                "id": node["id"],
                "title": node["title"],
                "level": node["doc_level"],
                "children": []
            } for node in nodes}

            # Organize root and child nodes
            root_nodes = []
            for node in nodes:
                if node["parent_id"] is None:
                    root_nodes.append(node_dict[node["id"]])
                else:
                    parent_id = node["parent_id"]
                    # Check if parent_id exists in node_dict before appending
                    if parent_id in node_dict:
                        parent = node_dict[parent_id]
                        parent["children"].append(node_dict[node["id"]])
                    else:
                        logger.warning(f"Parent node with id {parent_id} not found for node {node['id']}")

            return {
                "title": doc["title"],
                "path": doc["path"],
                # Sort root nodes by seq_num
                "structure": sorted(root_nodes, key=lambda x: [n for n in nodes if n['id'] == x['id']][0]['seq_num'])
            }
        except Exception as e:
            logger.error(f"Error getting document structure: {str(e)}")
            return {"error": str(e)}