from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentBase(BaseModel):
    """Base document model with common fields."""
    title: str
    path: str
    content: str

class DocumentCreate(DocumentBase):
    """Input model for document creation."""
    pass

class Document(DocumentBase):
    """Output model for document retrieval."""
    id: int
    last_modified: datetime
    version: int

class DocumentUpdate(BaseModel):
    """Input model for document update."""
    content: str
    changed_by: str = Field(default="AI")

class HierarchyNode(BaseModel):
    """Model for document hierarchy node."""
    id: int
    title: str
    content: str
    doc_level: int
    seq_num: int
    parent_id: Optional[int] = None
    document_id: int

class DocumentRelationship(BaseModel):
    """Model for document relationship."""
    source_id: int
    target_id: int
    relationship_type: str
    strength: float

class KeywordModel(BaseModel):
    """Model for document keyword."""
    node_id: int
    keyword: str
    importance: float