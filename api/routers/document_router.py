import logging
import tempfile
import shutil
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sentence_transformers import SentenceTransformer

from ..models import Document, DocumentCreate, DocumentUpdate
from ..services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

def get_document_service(model: SentenceTransformer = None):
    """Dependency to get document service."""
    return DocumentService(model)

class DocumentRouter:
    """Router for document endpoints."""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize the document router.
        
        Args:
            embedding_model: SentenceTransformer model for embeddings.
        """
        self.model = embedding_model
        
        # Use closure to pass model to the dependency
        def get_service():
            return get_document_service(self.model)
        
        # Register routes
        @router.post("/", response_model=Document)
        def create_document(document: DocumentCreate, service: DocumentService = Depends(get_service)):
            """Create a new document and index it."""
            try:
                result = service.create_document(document.title, document.path, document.content)
                if not result:
                    raise HTTPException(status_code=500, detail="Failed to create document")
                return result
            except Exception as e:
                logger.error(f"Error creating document: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.post("/upload/")
        async def upload_document(file: UploadFile = File(...), path: Optional[str] = None, service: DocumentService = Depends(get_service)):
            """Upload markdown file and index it."""
            try:
                # Create temporary file
                temp_dir = tempfile.mkdtemp()
                temp_file_path = os.path.join(temp_dir, file.filename)

                # Save file
                with open(temp_file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)

                # Read file content
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Delete temporary directory
                shutil.rmtree(temp_dir)

                # Set document path
                if not path:
                    path = f"/docs/{file.filename}"

                # Create document
                title = os.path.splitext(file.filename)[0]
                result = service.create_document(title, path, content)
                
                if not result:
                    raise HTTPException(status_code=500, detail="Failed to create document")

                return {"status": "success", "message": f"Document uploaded and indexed: {file.filename}", "document": result}
            except Exception as e:
                logger.error(f"Error uploading document: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/", response_model=List[Document])
        def read_documents(service: DocumentService = Depends(get_service)):
            """Get all documents."""
            try:
                results = service.list_documents()
                return results
            except Exception as e:
                logger.error(f"Error reading documents: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/{doc_id}", response_model=Document)
        def read_document(doc_id: int, service: DocumentService = Depends(get_service)):
            """Get a specific document."""
            try:
                result = service.get_document(doc_id)
                if not result:
                    raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
                return result
            except Exception as e:
                logger.error(f"Error reading document: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/{doc_id}/structure")
        def read_document_structure(doc_id: int, service: DocumentService = Depends(get_service)):
            """Get hierarchical structure of a document."""
            try:
                result = service.get_document_structure(doc_id)
                if "error" in result:
                    raise HTTPException(status_code=404, detail=result["error"])
                return result
            except Exception as e:
                logger.error(f"Error reading document structure: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.put("/{doc_id}", response_model=Document)
        def update_document_endpoint(doc_id: int, document_update: DocumentUpdate, service: DocumentService = Depends(get_service)):
            """Update a document."""
            try:
                # Use service for update
                result = service.update_document(doc_id, document_update.content, document_update.changed_by)

                if result.get("status") == "error":
                    raise HTTPException(status_code=404, detail=result.get("message"))

                # Get updated document
                updated_doc = service.get_document(doc_id)
                if not updated_doc:
                    # This case should theoretically not happen if update_document succeeded
                    raise HTTPException(status_code=500, detail=f"Failed to retrieve updated document with id {doc_id}")

                return updated_doc
            except Exception as e:
                logger.error(f"Error updating document: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))