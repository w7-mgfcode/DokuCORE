import pytest
from fastapi.testclient import TestClient
import json
import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the MCP tools
from api.mcp_tools import MCPTools
from api.main import mcp

def test_list_docs_tool():
    """Test the list_docs MCP tool."""
    # Get the tool function
    list_docs_tool = None
    for tool in mcp.registered_tools:
        if tool.name == "list_docs":
            list_docs_tool = tool.function
            break
    
    assert list_docs_tool is not None
    
    # Execute the tool
    result = list_docs_tool()
    
    # Check the result
    assert isinstance(result, list)
    # If there are any documents, check their structure
    if len(result) > 0:
        assert "id" in result[0]
        assert "title" in result[0]
        assert "path" in result[0]

def test_search_docs_tool():
    """Test the search_docs MCP tool."""
    # Get the tool function
    search_docs_tool = None
    for tool in mcp.registered_tools:
        if tool.name == "search_docs":
            search_docs_tool = tool.function
            break
    
    assert search_docs_tool is not None
    
    # Execute the tool
    result = search_docs_tool("test")
    
    # Check the result
    assert isinstance(result, list)
    # If there are any results, check their structure
    if len(result) > 0:
        assert "id" in result[0]
        assert "title" in result[0]
        assert "path" in result[0]
        assert "preview" in result[0]
        assert "relevance" in result[0]
        assert "match_type" in result[0]