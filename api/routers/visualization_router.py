"""
API endpoints for index visualization.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import os
from datetime import datetime

from ..services.document_service import DocumentService
from ..utils.cache import cached_result
from ..indexing.visualization import IndexVisualizer, VisualizationConfig
from ..utils.db import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualization", tags=["visualization"])

def get_visualizer(config: Optional[VisualizationConfig] = None) -> IndexVisualizer:
    """Get visualizer instance."""
    return IndexVisualizer(config)

@router.get("/hierarchy/{document_id}")
async def visualize_document_hierarchy(
    document_id: int,
    format: str = Query("html", enum=["html", "png", "json"]),
    document_service: DocumentService = Depends()
) -> Any:
    """
    Visualize the hierarchical structure of a document.
    
    Args:
        document_id: ID of the document to visualize
        format: Output format (html, png, or json)
        
    Returns:
        Visualization in requested format
    """
    try:
        # Get document hierarchy
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, doc_level as level, parent_id, seq_num
            FROM document_hierarchy
            WHERE document_id = %s
            ORDER BY doc_level, seq_num
        """, (document_id,))
        
        hierarchy_data = []
        for row in cursor.fetchall():
            hierarchy_data.append({
                'id': row[0],
                'title': row[1],
                'content': row[2][:100] + '...' if len(row[2]) > 100 else row[2],
                'level': row[3],
                'parent_id': row[4],
                'seq_num': row[5]
            })
        
        cursor.close()
        conn.close()
        
        if not hierarchy_data:
            raise HTTPException(status_code=404, detail=f"No hierarchy found for document {document_id}")
        
        # Get document title
        document = await document_service.get_document(document_id)
        
        if format == "json":
            return hierarchy_data
        
        # Create visualization
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(save_path=temp_dir, show_labels=True)
            visualizer = get_visualizer(config)
            
            if format == "png":
                # Generate PNG
                visualizer.visualize_document_hierarchy(hierarchy_data, document.title)
                file_path = os.path.join(temp_dir, f"hierarchy_{document.title}.png")
                return FileResponse(file_path, media_type="image/png", 
                                  filename=f"hierarchy_{document_id}.png")
            else:  # html
                # Generate interactive HTML
                output_path = os.path.join(temp_dir, "hierarchy.html")
                visualizer.create_interactive_graph(hierarchy_data, [], output_path)
                
                with open(output_path, 'r') as f:
                    html_content = f.read()
                
                return HTMLResponse(content=html_content)
                
    except Exception as e:
        logger.error(f"Error visualizing hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relationships/{document_id}")
async def visualize_relationships(
    document_id: int,
    format: str = Query("html", enum=["html", "png", "json"]),
    min_strength: float = Query(0.5, description="Minimum relationship strength to show")
) -> Any:
    """
    Visualize relationships between document nodes.
    
    Args:
        document_id: ID of the document
        format: Output format
        min_strength: Minimum relationship strength to include
        
    Returns:
        Relationship visualization
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get relationships
        cursor.execute("""
            SELECT r.source_id, r.target_id, r.relationship_type, r.strength
            FROM document_relationships r
            JOIN document_hierarchy h1 ON r.source_id = h1.id
            JOIN document_hierarchy h2 ON r.target_id = h2.id
            WHERE h1.document_id = %s AND h2.document_id = %s
                AND r.strength >= %s
        """, (document_id, document_id, min_strength))
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'source_id': row[0],
                'target_id': row[1],
                'relationship_type': row[2],
                'strength': float(row[3])
            })
        
        # Get nodes
        cursor.execute("""
            SELECT id, title
            FROM document_hierarchy
            WHERE document_id = %s
        """, (document_id,))
        
        nodes = []
        for row in cursor.fetchall():
            nodes.append({
                'id': row[0],
                'title': row[1]
            })
        
        cursor.close()
        conn.close()
        
        if format == "json":
            return {"nodes": nodes, "relationships": relationships}
        
        # Create visualization
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(save_path=temp_dir)
            visualizer = get_visualizer(config)
            
            if format == "png":
                visualizer.visualize_relationship_network(relationships, nodes)
                file_path = os.path.join(temp_dir, "relationships.png")
                return FileResponse(file_path, media_type="image/png",
                                  filename=f"relationships_{document_id}.png")
            else:  # html
                output_path = os.path.join(temp_dir, "relationships.html")
                
                # Get hierarchy for interactive graph
                cursor = get_db_connection().cursor()
                cursor.execute("""
                    SELECT id, title, doc_level as level
                    FROM document_hierarchy
                    WHERE document_id = %s
                """, (document_id,))
                
                hierarchy_data = []
                for row in cursor.fetchall():
                    hierarchy_data.append({
                        'id': row[0],
                        'title': row[1],
                        'level': row[2]
                    })
                cursor.close()
                
                visualizer.create_interactive_graph(hierarchy_data, relationships, output_path)
                
                with open(output_path, 'r') as f:
                    html_content = f.read()
                
                return HTMLResponse(content=html_content)
                
    except Exception as e:
        logger.error(f"Error visualizing relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{query}")
async def visualize_search_results(
    query: str,
    limit: int = Query(10, description="Number of results to visualize"),
    format: str = Query("png", enum=["png", "json"])
) -> Any:
    """
    Visualize search results with relevance scores.
    
    Args:
        query: Search query
        limit: Number of results to show
        format: Output format
        
    Returns:
        Search results visualization
    """
    try:
        # Import here to avoid circular dependency
        from ..services.search_service import SearchService
        
        search_service = SearchService()
        results = await search_service.search(query, limit)
        
        if format == "json":
            return results
        
        # Create visualization
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(save_path=temp_dir)
            visualizer = get_visualizer(config)
            
            visualizer.visualize_search_results(results, query)
            file_path = os.path.join(temp_dir, f"search_results_{query}.png")
            
            return FileResponse(file_path, media_type="image/png",
                              filename=f"search_{query}.png")
            
    except Exception as e:
        logger.error(f"Error visualizing search results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keywords/{document_id}")
async def visualize_keywords(
    document_id: int,
    limit: int = Query(20, description="Number of keywords to show"),
    format: str = Query("png", enum=["png", "json"])
) -> Any:
    """
    Visualize keyword distribution for a document.
    
    Args:
        document_id: ID of the document
        limit: Number of keywords to show
        format: Output format
        
    Returns:
        Keyword visualization
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT k.keyword, k.importance
            FROM document_keywords k
            JOIN document_hierarchy h ON k.node_id = h.id
            WHERE h.document_id = %s
            ORDER BY k.importance DESC
            LIMIT %s
        """, (document_id, limit))
        
        keywords = []
        for row in cursor.fetchall():
            keywords.append({
                'keyword': row[0],
                'importance': float(row[1])
            })
        
        cursor.close()
        conn.close()
        
        if format == "json":
            return keywords
        
        # Get document info
        document_service = DocumentService()
        document = await document_service.get_document(document_id)
        
        # Create visualization
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(save_path=temp_dir)
            visualizer = get_visualizer(config)
            
            visualizer.visualize_keyword_distribution(keywords, document.title)
            file_path = os.path.join(temp_dir, f"keywords_{document.title}.png")
            
            return FileResponse(file_path, media_type="image/png",
                              filename=f"keywords_{document_id}.png")
            
    except Exception as e:
        logger.error(f"Error visualizing keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report")
async def generate_index_report() -> HTMLResponse:
    """
    Generate a comprehensive report of the index.
    
    Returns:
        HTML report with statistics and visualizations
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Gather statistics
        stats = {}
        
        # Total documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        stats['total_documents'] = cursor.fetchone()[0]
        
        # Total nodes
        cursor.execute("SELECT COUNT(*) FROM document_hierarchy")
        stats['total_nodes'] = cursor.fetchone()[0]
        
        # Total relationships
        cursor.execute("SELECT COUNT(*) FROM document_relationships")
        stats['total_relationships'] = cursor.fetchone()[0]
        
        # Total keywords
        cursor.execute("SELECT COUNT(DISTINCT keyword) FROM document_keywords")
        stats['total_keywords'] = cursor.fetchone()[0]
        
        # Average nodes per document
        stats['avg_nodes_per_doc'] = stats['total_nodes'] / max(stats['total_documents'], 1)
        
        # Average relationships per node
        stats['avg_relationships_per_node'] = stats['total_relationships'] / max(stats['total_nodes'], 1)
        
        # Get embedding info
        cursor.execute("""
            SELECT pg_column_size(embedding)::float / 4 as dim
            FROM document_hierarchy
            LIMIT 1
        """)
        result = cursor.fetchone()
        stats['embedding_dim'] = int(result[0]) if result else 384
        
        # Storage size estimate
        cursor.execute("""
            SELECT pg_total_relation_size('document_hierarchy')::float / 1024 / 1024 as size_mb
        """)
        stats['storage_size_mb'] = cursor.fetchone()[0]
        
        stats['index_type'] = 'HNSW'
        stats['similarity_metric'] = 'cosine'
        stats['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.close()
        conn.close()
        
        # Generate report
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(save_path=temp_dir)
            visualizer = get_visualizer(config)
            
            report_path = os.path.join(temp_dir, "index_report.html")
            visualizer.generate_index_report(stats, report_path)
            
            with open(report_path, 'r') as f:
                html_content = f.read()
            
            return HTMLResponse(content=html_content)
            
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))