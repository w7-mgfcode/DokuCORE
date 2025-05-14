import pytest
from fastapi.testclient import TestClient

def test_list_tasks(test_client: TestClient):
    """Test the list tasks endpoint."""
    response = test_client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_task(test_client: TestClient):
    """Test the create task endpoint."""
    task_data = {
        "title": "Test Task",
        "description": "This is a test task."
    }
    
    response = test_client.post(
        "/tasks/",
        json=task_data
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == task_data["title"]
    assert response.json()["description"] == task_data["description"]
    assert response.json()["status"] == "pending"  # Default status

def test_create_task_with_document(test_client: TestClient):
    """Test the create task endpoint with a document reference."""
    # First create a document
    document_data = {
        "title": "Test Task Document",
        "path": "/docs/test-task.md",
        "content": "# Test Task Document\n\nThis is a test document for task association."
    }
    
    create_doc_response = test_client.post(
        "/documents/",
        json=document_data
    )
    
    assert create_doc_response.status_code == 200
    doc_id = create_doc_response.json()["id"]
    
    # Now create a task associated with the document
    task_data = {
        "title": "Test Task with Document",
        "description": "This is a test task associated with a document.",
        "document_id": doc_id
    }
    
    response = test_client.post(
        "/tasks/",
        json=task_data
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == task_data["title"]
    assert response.json()["description"] == task_data["description"]
    assert response.json()["document_id"] == doc_id

def test_update_task_status(test_client: TestClient):
    """Test the update task status endpoint."""
    # First create a task
    task_data = {
        "title": "Test Status Task",
        "description": "This is a test task for status updates."
    }
    
    create_response = test_client.post(
        "/tasks/",
        json=task_data
    )
    
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]
    
    # Now update the task status
    new_status = "completed"
    response = test_client.put(
        f"/tasks/{task_id}?status={new_status}"
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["status"] == new_status