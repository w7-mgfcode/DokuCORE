import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, Path, Query
from sentence_transformers import SentenceTransformer

from ..models.version import (
    DocumentVersion,
    DocumentApproval,
    DocumentApprovalCreate,
    DocumentApprovalUpdate
)
from ..models.auth import User
from ..services.version_service import VersionService
from ..services.auth_service import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/versions", tags=["versions"])

def get_version_service():
    """Dependency to get version service."""
    return VersionService()

class VersionRouter:
    """Router for version and approval endpoints."""
    
    def __init__(self):
        """Initialize the version router."""
        
        # Register routes
        @router.get("/documents/{doc_id}")
        def get_document_versions(
            doc_id: int = Path(..., description="Document ID"),
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:read"])
        ):
            """Get version history for a document."""
            try:
                versions = service.get_document_versions(doc_id)
                if not versions:
                    return []
                return versions
            except Exception as e:
                logger.error(f"Error getting document versions: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/documents/{doc_id}/{version}")
        def get_document_version(
            doc_id: int = Path(..., description="Document ID"),
            version: int = Path(..., description="Version number"),
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:read"])
        ):
            """Get a specific version of a document."""
            try:
                version_data = service.get_document_version(doc_id, version)
                if not version_data:
                    raise HTTPException(status_code=404, detail=f"Version {version} not found for document {doc_id}")
                return version_data
            except Exception as e:
                logger.error(f"Error getting document version: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.post("/documents/{doc_id}/restore/{version}")
        def restore_document_version(
            doc_id: int = Path(..., description="Document ID"),
            version: int = Path(..., description="Version to restore"),
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:write"])
        ):
            """Restore a document to a previous version."""
            try:
                result = service.restore_document_version(doc_id, version, current_user.username)
                if result.get("status") == "error":
                    raise HTTPException(status_code=400, detail=result.get("message"))
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error restoring document version: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.post("/approvals")
        def create_approval_request(
            approval: DocumentApprovalCreate,
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:write"])
        ):
            """Create a document approval request."""
            try:
                # Set the requesting user
                approval.requested_by = current_user.username
                
                result = service.create_approval_request(approval)
                if result.get("status") == "error":
                    raise HTTPException(status_code=400, detail=result.get("message"))
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating approval request: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/approvals")
        def get_approval_requests(
            status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:read"])
        ):
            """Get document approval requests."""
            try:
                approvals = service.get_approval_requests(status)
                return approvals
            except Exception as e:
                logger.error(f"Error getting approval requests: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/approvals/{approval_id}")
        def get_approval_request(
            approval_id: int = Path(..., description="Approval request ID"),
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:read"])
        ):
            """Get a specific approval request."""
            try:
                approval = service.get_approval_request(approval_id)
                if not approval:
                    raise HTTPException(status_code=404, detail=f"Approval request {approval_id} not found")
                return approval
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting approval request: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.put("/approvals/{approval_id}")
        def update_approval_request(
            approval_id: int = Path(..., description="Approval request ID"),
            update: DocumentApprovalUpdate = None,
            service: VersionService = Depends(get_version_service),
            current_user: User = Security(get_current_active_user, scopes=["documents:approve"])
        ):
            """Update an approval request (approve or reject)."""
            try:
                # Set the approving user
                update.approved_by = current_user.username
                
                result = service.update_approval_request(approval_id, update)
                if result.get("status") == "error":
                    raise HTTPException(status_code=400, detail=result.get("message"))
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating approval request: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))