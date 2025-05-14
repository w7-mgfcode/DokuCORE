import pytest
from fastapi.testclient import TestClient
import json

def test_list_documents(test_client: TestClient):
    """Test the list documents endpoint."""
    response = test_client.get("/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_document(test_client: TestClient):
    """Test the create document endpoint."""
    document_data = {
        "title": "Test Document",
        "path": "/docs/test.md",
        "content": "# Test Document\n\nThis is a test document."
    }
    
    response = test_client.post(
        "/documents/",
        json=document_data
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == document_data["title"]
    assert response.json()["path"] == document_data["path"]
    assert response.json()["content"] == document_data["content"]
    
    # Cleanup - Delete the document
    doc_id = response.json()["id"]
    # Note: We would need a delete endpoint to clean up after the test

def test_get_document(test_client: TestClient):
    """Test the get document endpoint."""
    # First create a document
    document_data = {
        "title": "Test Get Document",
        "path": "/docs/test-get.md",
        "content": "# Test Get Document\n\nThis is a test document for getting."
    }
    
    create_response = test_client.post(
        "/documents/",
        json=document_data
    )
    
    assert create_response.status_code == 200
    doc_id = create_response.json()["id"]
    
    # Now get the document
    response = test_client.get(f"/documents/{doc_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == doc_id
    assert response.json()["title"] == document_data["title"]
    assert response.json()["path"] == document_data["path"]
    assert response.json()["content"] == document_data["content"]

def test_update_document(test_client: TestClient):
    """Test the update document endpoint."""
    # First create a document
    document_data = {
        "title": "Test Update Document",
        "path": "/docs/test-update.md",
        "content": "# Test Update Document\n\nThis is a test document for updating."
    }
    
    create_response = test_client.post(
        "/documents/",
        json=document_data
    )
    
    assert create_response.status_code == 200
    doc_id = create_response.json()["id"]
    
    # Now update the document
    update_data = {
        "content": "# Updated Test Document\n\nThis document has been updated.",
        "changed_by": "Test"
    }
    
    response = test_client.put(
        f"/documents/{doc_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == doc_id
    assert response.json()["content"] == update_data["content"]
    assert response.json()["version"] == 2  # Version should be incremented

def test_get_document_structure(test_client: TestClient):
    """Test the get document structure endpoint."""
    # First create a document with a structure
    document_data = {
        "title": "Test Structure Document",
        "path": "/docs/test-structure.md",
        "content": "# Test Structure Document\n\nTop level content.\n\n## Section 1\n\nSection 1 content.\n\n### Subsection 1.1\n\nSubsection 1.1 content.\n\n## Section 2\n\nSection 2 content."
    }
    
    create_response = test_client.post(
        "/documents/",
        json=document_data
    )
    
    assert create_response.status_code == 200
    doc_id = create_response.json()["id"]
    
    # Now get the document structure
    response = test_client.get(f"/documents/{doc_id}/structure")
    
    assert response.status_code == 200
    assert response.json()["title"] == document_data["title"]
    assert response.json()["path"] == document_data["path"]
    assert "structure" in response.json()
    assert len(response.json()["structure"]) > 0