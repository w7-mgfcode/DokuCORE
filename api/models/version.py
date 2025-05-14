from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class DocumentVersion(BaseModel):
    """Model for document version history."""
    id: int
    document_id: int
    content: str
    changed_at: datetime
    changed_by: str
    version: int
    
class DocumentVersionCreate(BaseModel):
    """Model for creating a document version."""
    document_id: int
    content: str
    changed_by: str
    version: int
    
class DocumentApproval(BaseModel):
    """Model for document approval workflow."""
    id: int
    document_id: int
    version: int
    status: str  # pending, approved, rejected
    requested_by: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None
    
class DocumentApprovalCreate(BaseModel):
    """Model for creating a document approval request."""
    document_id: int
    version: int
    requested_by: str
    comments: Optional[str] = None
    
class DocumentApprovalUpdate(BaseModel):
    """Model for updating a document approval."""
    status: str  # approved, rejected
    approved_by: str
    comments: Optional[str] = None