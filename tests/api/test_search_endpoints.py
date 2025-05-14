import pytest
from fastapi.testclient import TestClient

def test_search_docs(test_client: TestClient):
    """Test the search endpoint."""
    # First create a document that can be searched
    document_data = {
        "title": "Test Search Document",
        "path": "/docs/test-search.md",
        "content": "# Test Search Document\n\nThis document contains specific keywords for testing search functionality. It mentions artificial intelligence, documentation systems, and vector embeddings."
    }
    
    create_response = test_client.post(
        "/documents/",
        json=document_data
    )
    
    assert create_response.status_code == 200
    
    # Now search for a keyword
    response = test_client.get("/search/?query=artificial+intelligence&limit=5")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # There should be at least one result
    if len(response.json()) > 0:
        # The first result should be relevant
        assert "relevance" in response.json()[0]
        assert "title" in response.json()[0]
        assert "preview" in response.json()[0]
        
        # The relevance should be high (format is "XX%")
        relevance = int(response.json()[0]["relevance"].replace("%", ""))
        assert relevance > 50