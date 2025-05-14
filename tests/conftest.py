import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from api.main import app

# Import the database connection
from api.utils.db import get_db_connection


@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI application.
    
    Returns:
        TestClient: FastAPI test client.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_db_connection():
    """
    Create a test database connection.
    
    This should be replaced with a proper test database setup using
    something like Docker for isolated tests.
    
    Returns:
        Connection: Database connection for tests.
    """
    try:
        # For actual tests, this should connect to a test database, not the main one
        conn = get_db_connection()
        yield conn
    finally:
        conn.close()