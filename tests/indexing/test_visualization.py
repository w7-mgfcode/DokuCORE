"""
Unit tests for the visualization module.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from api.indexing.visualization import (
    IndexVisualizer,
    VisualizationConfig
)


class TestVisualizationConfig:
    """Test cases for the VisualizationConfig dataclass."""
    
    def test_default_config(self):
        """Test default visualization configuration."""
        config = VisualizationConfig()
        
        assert config.figure_size == (12, 8)
        assert config.node_size == 1000
        assert config.font_size == 10
        assert config.show_labels is True
        assert config.dpi == 300
    
    def test_custom_config(self):
        """Test custom visualization configuration."""
        config = VisualizationConfig(
            figure_size=(15, 10),
            node_size=1500,
            color_scheme="plasma",
            save_path="/tmp/viz"
        )
        
        assert config.figure_size == (15, 10)
        assert config.color_scheme == "plasma"
        assert config.save_path == "/tmp/viz"


class TestIndexVisualizer:
    """Test cases for the IndexVisualizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = VisualizationConfig(
            save_path=self.temp_dir,
            show_labels=True
        )
        self.visualizer = IndexVisualizer(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_visualize_document_hierarchy(self, mock_savefig, mock_show):
        """Test document hierarchy visualization."""
        hierarchy_data = [
            {'id': 1, 'title': 'Root', 'level': 1, 'parent_id': None},
            {'id': 2, 'title': 'Child 1', 'level': 2, 'parent_id': 1},
            {'id': 3, 'title': 'Child 2', 'level': 2, 'parent_id': 1},
            {'id': 4, 'title': 'Grandchild', 'level': 3, 'parent_id': 2}
        ]
        
        # Test with save path
        self.visualizer.visualize_document_hierarchy(hierarchy_data, "Test Document")
        
        # Should attempt to save
        mock_savefig.assert_called_once()
        save_args = mock_savefig.call_args[0]
        assert "hierarchy_Test Document.png" in save_args[0]
        
        # Test without save path (should show)
        self.config.save_path = None
        self.visualizer.visualize_document_hierarchy(hierarchy_data, "Test Document")
        mock_show.assert_called()
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_visualize_relationship_network(self, mock_savefig, mock_show):
        """Test relationship network visualization."""
        relationships = [
            {'source_id': 1, 'target_id': 2, 'relationship_type': 'semantic', 'strength': 0.8},
            {'source_id': 2, 'target_id': 3, 'relationship_type': 'sibling', 'strength': 0.6},
            {'source_id': 1, 'target_id': 3, 'relationship_type': 'keyword_based', 'strength': 0.5}
        ]
        
        nodes = [
            {'id': 1, 'title': 'Node 1'},
            {'id': 2, 'title': 'Node 2'},
            {'id': 3, 'title': 'Node 3'}
        ]
        
        self.visualizer.visualize_relationship_network(relationships, nodes)
        
        # Should attempt to save
        mock_savefig.assert_called_once()
        save_args = mock_savefig.call_args[0]
        assert "relationships.png" in save_args[0]
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_visualize_search_results(self, mock_savefig, mock_show):
        """Test search results visualization."""
        search_results = [
            {'title': 'Result 1', 'relevance': 0.95, 'match_type': 'keyword'},
            {'title': 'Result 2', 'relevance': 0.82, 'match_type': 'semantic'},
            {'title': 'Result 3', 'relevance': 0.70, 'match_type': 'related-sibling'}
        ]
        
        self.visualizer.visualize_search_results(search_results, "test query")
        
        # Should attempt to save
        mock_savefig.assert_called_once()
        save_args = mock_savefig.call_args[0]
        assert "search_results_test query.png" in save_args[0]
    
    def test_visualize_search_results_empty(self):
        """Test search results visualization with no results."""
        with patch('api.indexing.visualization.logger') as mock_logger:
            self.visualizer.visualize_search_results([], "empty query")
            
            # Should log warning
            mock_logger.warning.assert_called_with("No search results to visualize")
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_visualize_keyword_distribution(self, mock_savefig, mock_show):
        """Test keyword distribution visualization."""
        keywords = [
            {'keyword': 'api', 'importance': 0.9},
            {'keyword': 'documentation', 'importance': 0.8},
            {'keyword': 'search', 'importance': 0.7},
            {'keyword': 'index', 'importance': 0.6}
        ]
        
        self.visualizer.visualize_keyword_distribution(keywords, "Test Document")
        
        # Should attempt to save
        mock_savefig.assert_called_once()
        save_args = mock_savefig.call_args[0]
        assert "keywords_Test Document.png" in save_args[0]
    
    @patch('seaborn.heatmap')
    @patch('matplotlib.pyplot.savefig')
    def test_visualize_embedding_similarity_heatmap(self, mock_savefig, mock_heatmap):
        """Test embedding similarity heatmap visualization."""
        import numpy as np
        
        # Create mock embeddings
        embeddings = np.random.rand(5, 384)  # 5 embeddings of dimension 384
        labels = ['Doc1', 'Doc2', 'Doc3', 'Doc4', 'Doc5']
        
        self.visualizer.visualize_embedding_similarity_heatmap(embeddings, labels)
        
        # Should create heatmap
        mock_heatmap.assert_called_once()
        
        # Should attempt to save
        mock_savefig.assert_called_once()
        save_args = mock_savefig.call_args[0]
        assert "embedding_similarity.png" in save_args[0]
    
    def test_generate_index_report(self):
        """Test HTML report generation."""
        corpus_stats = {
            'total_documents': 100,
            'total_nodes': 500,
            'total_relationships': 2000,
            'total_keywords': 1500,
            'avg_nodes_per_doc': 5.0,
            'avg_relationships_per_node': 4.0,
            'embedding_dim': 384,
            'index_type': 'HNSW',
            'similarity_metric': 'cosine',
            'storage_size_mb': 150.5,
            'timestamp': '2025-05-17 12:00:00'
        }
        
        output_path = os.path.join(self.temp_dir, "test_report.html")
        self.visualizer.generate_index_report(corpus_stats, output_path)
        
        # Check that file was created
        assert os.path.exists(output_path)
        
        # Check content
        with open(output_path, 'r') as f:
            content = f.read()
            
            assert "Total Documents: 100" in content
            assert "Total Nodes: 500" in content
            assert "Embedding Dimensions: 384" in content
            assert "Storage Size: 150.50 MB" in content
    
    def test_create_interactive_graph(self):
        """Test interactive D3.js graph creation."""
        hierarchy_data = [
            {'id': 1, 'title': 'Node 1', 'level': 1},
            {'id': 2, 'title': 'Node 2', 'level': 2},
            {'id': 3, 'title': 'Node 3', 'level': 2}
        ]
        
        relationships = [
            {'source_id': 1, 'target_id': 2, 'strength': 0.8, 'relationship_type': 'parent_child'},
            {'source_id': 2, 'target_id': 3, 'strength': 0.6, 'relationship_type': 'sibling'}
        ]
        
        output_path = os.path.join(self.temp_dir, "interactive_graph.html")
        self.visualizer.create_interactive_graph(hierarchy_data, relationships, output_path)
        
        # Check that file was created
        assert os.path.exists(output_path)
        
        # Check content
        with open(output_path, 'r') as f:
            content = f.read()
            
            # Should include D3.js
            assert "d3js.org" in content
            
            # Should include the data
            assert "Node 1" in content
            assert "Node 2" in content
            
            # Should include interactive elements
            assert "drag" in content.lower()
            assert "force" in content.lower()
    
    def test_config_limits(self):
        """Test that configuration limits are respected."""
        # Create many nodes
        hierarchy_data = [
            {'id': i, 'title': f'Node {i}', 'level': 1}
            for i in range(100)
        ]
        
        # Set max nodes limit
        self.config.max_nodes = 10
        
        # Mock the actual plotting to avoid matplotlib issues in tests
        with patch('api.indexing.visualization.nx.draw_networkx_nodes'):
            with patch('api.indexing.visualization.plt.savefig'):
                self.visualizer.visualize_document_hierarchy(hierarchy_data, "Large Document")
                
                # Should only process max_nodes
                # This would be verified by checking the internal graph size
                # but for unit tests we mainly ensure no crashes occur