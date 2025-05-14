import logging
import psycopg2.extras
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.db import get_db_connection
from ..utils.config import config
from ..models.version import (
    DocumentVersion,
    DocumentVersionCreate,
    DocumentApproval,
    DocumentApprovalCreate,
    DocumentApprovalUpdate
)

logger = logging.getLogger(__name__)

class VersionService:
    """Service for document versioning and approval operations."""
    
    def get_document_versions(self, doc_id: int) -> List[Dict[str, Any]]:
        """
        Get version history for a document.
        
        Args:
            doc_id (int): Document ID.
            
        Returns:
            List[Dict[str, Any]]: List of document versions.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get document versions
            cursor.execute(
                """SELECT h.id, h.document_id, h.content, h.changed_at, h.changed_by, h.version,
                          d.title, d.path
                   FROM document_history h
                   JOIN documents d ON h.document_id = d.id
                   WHERE h.document_id = %s
                   ORDER BY h.version DESC""",
                (doc_id,)
            )
            
            versions = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(version) for version in versions]
        except Exception as e:
            logger.error(f"Error getting document versions: {str(e)}")
            return []
    
    def get_document_version(self, doc_id: int, version: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific version of a document.
        
        Args:
            doc_id (int): Document ID.
            version (int): Version number.
            
        Returns:
            Optional[Dict[str, Any]]: Document version data or None if not found.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get document version
            cursor.execute(
                """SELECT h.id, h.document_id, h.content, h.changed_at, h.changed_by, h.version,
                          d.title, d.path
                   FROM document_history h
                   JOIN documents d ON h.document_id = d.id
                   WHERE h.document_id = %s AND h.version = %s""",
                (doc_id, version)
            )
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return None
                
            return dict(result)
        except Exception as e:
            logger.error(f"Error getting document version: {str(e)}")
            return None
    
    def restore_document_version(self, doc_id: int, version: int, user: str) -> Dict[str, Any]:
        """
        Restore a document to a previous version.
        
        Args:
            doc_id (int): Document ID.
            version (int): Version to restore.
            user (str): User performing the restoration.
            
        Returns:
            Dict[str, Any]: Result of the operation.
        """
        try:
            # Get the version content
            old_version = self.get_document_version(doc_id, version)
            if not old_version:
                return {"status": "error", "message": f"Version {version} not found for document {doc_id}"}
            
            # Get current document data
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cursor.execute(
                "SELECT version, content FROM documents WHERE id = %s",
                (doc_id,)
            )
            
            current = cursor.fetchone()
            if not current:
                conn.close()
                return {"status": "error", "message": f"Document with ID {doc_id} not found"}
            
            current_version = current["version"]
            current_content = current["content"]
            
            # Add current version to history
            cursor.execute(
                "INSERT INTO document_history (document_id, content, changed_by, version) VALUES (%s, %s, %s, %s)",
                (doc_id, current_content, user, current_version)
            )
            
            # Update document with restored content
            cursor.execute(
                """UPDATE documents
                   SET content = %s, version = %s, last_modified = CURRENT_TIMESTAMP,
                       approval_status = 'draft', approved_version = NULL
                   WHERE id = %s""",
                (old_version["content"], current_version + 1, doc_id)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update the document in the search index
            # TODO: Update the document in the search index
            
            return {
                "status": "success", 
                "message": f"Document restored to version {version}",
                "new_version": current_version + 1
            }
        except Exception as e:
            logger.error(f"Error restoring document version: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def create_approval_request(self, approval: DocumentApprovalCreate) -> Dict[str, Any]:
        """
        Create a document approval request.
        
        Args:
            approval: Approval request data.
            
        Returns:
            Dict[str, Any]: Result of the operation.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Check if document exists
            cursor.execute(
                "SELECT id, version, approval_status FROM documents WHERE id = %s",
                (approval.document_id,)
            )
            
            document = cursor.fetchone()
            if not document:
                conn.close()
                return {"status": "error", "message": f"Document with ID {approval.document_id} not found"}
            
            # Check if version matches
            if document["version"] != approval.version:
                conn.close()
                return {
                    "status": "error", 
                    "message": f"Version mismatch. Document is at version {document['version']}, but approval request is for version {approval.version}"
                }
            
            # Check if document is already approved
            if document["approval_status"] == "approved":
                conn.close()
                return {
                    "status": "error", 
                    "message": f"Document is already approved"
                }
            
            # Check if there's already a pending approval request
            cursor.execute(
                """SELECT id FROM document_approval 
                   WHERE document_id = %s AND version = %s AND status = 'pending'""",
                (approval.document_id, approval.version)
            )
            
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return {
                    "status": "error", 
                    "message": f"There is already a pending approval request for this document version"
                }
            
            # Create approval request
            cursor.execute(
                """INSERT INTO document_approval 
                   (document_id, version, status, requested_by, requested_at, comments)
                   VALUES (%s, %s, 'pending', %s, CURRENT_TIMESTAMP, %s)
                   RETURNING id""",
                (approval.document_id, approval.version, approval.requested_by, approval.comments)
            )
            
            result = cursor.fetchone()
            
            # Update document status to under review
            cursor.execute(
                """UPDATE documents SET approval_status = 'under_review'
                   WHERE id = %s""",
                (approval.document_id,)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "status": "success", 
                "message": "Approval request created",
                "approval_id": result["id"]
            }
        except Exception as e:
            logger.error(f"Error creating approval request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_approval_requests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get document approval requests.
        
        Args:
            status (Optional[str]): Filter by status (pending, approved, rejected).
            
        Returns:
            List[Dict[str, Any]]: List of approval requests.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            if status:
                cursor.execute(
                    """SELECT a.*, d.title, d.path 
                       FROM document_approval a
                       JOIN documents d ON a.document_id = d.id
                       WHERE a.status = %s
                       ORDER BY a.requested_at DESC""",
                    (status,)
                )
            else:
                cursor.execute(
                    """SELECT a.*, d.title, d.path 
                       FROM document_approval a
                       JOIN documents d ON a.document_id = d.id
                       ORDER BY a.requested_at DESC"""
                )
            
            approvals = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(approval) for approval in approvals]
        except Exception as e:
            logger.error(f"Error getting approval requests: {str(e)}")
            return []
    
    def get_approval_request(self, approval_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific approval request.
        
        Args:
            approval_id (int): Approval request ID.
            
        Returns:
            Optional[Dict[str, Any]]: Approval request data or None if not found.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cursor.execute(
                """SELECT a.*, d.title, d.path 
                   FROM document_approval a
                   JOIN documents d ON a.document_id = d.id
                   WHERE a.id = %s""",
                (approval_id,)
            )
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return None
                
            return dict(result)
        except Exception as e:
            logger.error(f"Error getting approval request: {str(e)}")
            return None
    
    def update_approval_request(self, approval_id: int, update: DocumentApprovalUpdate) -> Dict[str, Any]:
        """
        Update an approval request (approve or reject).
        
        Args:
            approval_id (int): Approval request ID.
            update: Approval update data.
            
        Returns:
            Dict[str, Any]: Result of the operation.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get approval request
            cursor.execute(
                """SELECT document_id, version, status 
                   FROM document_approval 
                   WHERE id = %s""",
                (approval_id,)
            )
            
            approval = cursor.fetchone()
            if not approval:
                conn.close()
                return {"status": "error", "message": f"Approval request with ID {approval_id} not found"}
            
            # Check if approval is already processed
            if approval["status"] != "pending":
                conn.close()
                return {"status": "error", "message": f"Approval request is already {approval['status']}"}
            
            # Update approval request
            cursor.execute(
                """UPDATE document_approval 
                   SET status = %s, approved_by = %s, approved_at = CURRENT_TIMESTAMP, comments = %s
                   WHERE id = %s""",
                (update.status, update.approved_by, update.comments, approval_id)
            )
            
            # Update document status based on approval status
            if update.status == "approved":
                cursor.execute(
                    """UPDATE documents 
                       SET approval_status = 'approved', approved_version = %s
                       WHERE id = %s""",
                    (approval["version"], approval["document_id"])
                )
            else:  # rejected
                cursor.execute(
                    """UPDATE documents 
                       SET approval_status = 'rejected'
                       WHERE id = %s""",
                    (approval["document_id"],)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "status": "success", 
                "message": f"Approval request {update.status}"
            }
        except Exception as e:
            logger.error(f"Error updating approval request: {str(e)}")
            return {"status": "error", "message": str(e)}