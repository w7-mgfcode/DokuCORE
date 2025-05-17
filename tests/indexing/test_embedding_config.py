"""
Unit tests for the embedding configuration module.
"""

import pytest
from api.indexing.embedding_config import (
    EmbeddingOptimizer,
    EmbeddingModelType,
    EmbeddingConfig
)


class TestEmbeddingConfig:
    """Test cases for the EmbeddingConfig dataclass."""
    
    def test_default_config_creation(self):
        """Test creating a default embedding configuration."""
        config = EmbeddingConfig(
            model_name="test-model",
            embedding_dim=384,
            max_sequence_length=256,
            batch_size=32
        )
        
        assert config.model_name == "test-model"
        assert config.embedding_dim == 384
        assert config.max_sequence_length == 256
        assert config.batch_size == 32
        assert config.normalize_embeddings is True  # Default value
        assert config.device == "cpu"  # Default value
    
    def test_custom_config_values(self):
        """Test creating config with custom values."""
        config = EmbeddingConfig(
            model_name="custom-model",
            embedding_dim=768,
            max_sequence_length=512,
            batch_size=16,
            normalize_embeddings=False,
            device="cuda",
            precision="float16",
            query_prefix="Query: ",
            document_prefix="Document: "
        )
        
        assert config.precision == "float16"
        assert config.query_prefix == "Query: "
        assert config.document_prefix == "Document: "


class TestEmbeddingOptimizer:
    """Test cases for the EmbeddingOptimizer class."""
    
    def test_get_optimal_config_for_model(self):
        """Test getting optimal configuration for different models."""
        # Test MiniLM configuration
        config = EmbeddingOptimizer.get_optimal_config(
            EmbeddingModelType.MINILM,
            use_case="hierarchical_indexing"
        )
        
        assert config.model_name == "all-MiniLM-L6-v2"
        assert config.embedding_dim == 384
        assert config.max_sequence_length <= 512
        
        # Test MPNet configuration
        config = EmbeddingOptimizer.get_optimal_config(
            EmbeddingModelType.MPNET,
            use_case="semantic_search"
        )
        
        assert config.model_name == "all-mpnet-base-v2"
        assert config.embedding_dim == 768
    
    def test_use_case_specific_optimization(self):
        """Test that different use cases produce different configurations."""
        # Hierarchical indexing config
        hier_config = EmbeddingOptimizer.get_optimal_config(
            EmbeddingModelType.MINILM,
            use_case="hierarchical_indexing"
        )
        
        # Keyword extraction config
        keyword_config = EmbeddingOptimizer.get_optimal_config(
            EmbeddingModelType.MINILM,
            use_case="keyword_extraction"
        )
        
        # Semantic search config
        search_config = EmbeddingOptimizer.get_optimal_config(
            EmbeddingModelType.MINILM,
            use_case="semantic_search"
        )
        
        # Different use cases should have different parameters
        assert keyword_config.max_sequence_length < hier_config.max_sequence_length
        assert keyword_config.batch_size > hier_config.batch_size
    
    def test_memory_usage_calculation(self):
        """Test memory usage calculation for embeddings."""
        config = EmbeddingConfig(
            model_name="all-MiniLM-L6-v2",
            embedding_dim=384,
            max_sequence_length=256,
            batch_size=32,
            precision="float32"
        )
        
        memory_stats = EmbeddingOptimizer.calculate_memory_usage(
            config, 
            num_documents=1000
        )
        
        assert "embedding_storage_mb" in memory_stats
        assert "model_memory_mb" in memory_stats
        assert "index_overhead_mb" in memory_stats
        assert "total_mb" in memory_stats
        
        # Sanity checks
        assert memory_stats["embedding_storage_mb"] > 0
        assert memory_stats["total_mb"] > memory_stats["embedding_storage_mb"]
        
        # Test with float16 precision
        config.precision = "float16"
        memory_stats_fp16 = EmbeddingOptimizer.calculate_memory_usage(
            config,
            num_documents=1000
        )
        
        # float16 should use less memory
        assert memory_stats_fp16["embedding_storage_mb"] < memory_stats["embedding_storage_mb"]
    
    def test_model_recommendation(self):
        """Test model recommendation based on requirements."""
        # Test with high memory constraint
        requirements = {
            'max_memory_mb': 100,
            'quality_priority': 5,
            'speed_priority': 8,
            'multilingual': False
        }
        
        recommended = EmbeddingOptimizer.recommend_model(requirements)
        assert recommended == EmbeddingModelType.MINILM  # Should recommend small model
        
        # Test with quality priority
        requirements = {
            'max_memory_mb': 2000,
            'quality_priority': 9,
            'speed_priority': 3,
            'multilingual': False
        }
        
        recommended = EmbeddingOptimizer.recommend_model(requirements)
        assert recommended in [EmbeddingModelType.MPNET, EmbeddingModelType.ADA, EmbeddingModelType.INSTRUCTOR]
        
        # Test with multilingual requirement
        requirements = {
            'max_memory_mb': 2000,
            'quality_priority': 7,
            'speed_priority': 5,
            'multilingual': True
        }
        
        recommended = EmbeddingOptimizer.recommend_model(requirements)
        assert recommended in [EmbeddingModelType.E5, EmbeddingModelType.ADA]
    
    def test_batch_size_optimization(self):
        """Test batch size optimization based on available memory."""
        config = EmbeddingConfig(
            model_name="test-model",
            embedding_dim=768,
            max_sequence_length=512,
            batch_size=32
        )
        
        # Test with limited memory
        optimized_batch_size = EmbeddingOptimizer.optimize_batch_size(
            config,
            available_memory_mb=100
        )
        
        assert optimized_batch_size > 0
        assert optimized_batch_size <= 128  # Max reasonable batch size
        
        # Test with more memory
        optimized_batch_size_large = EmbeddingOptimizer.optimize_batch_size(
            config,
            available_memory_mb=1000
        )
        
        assert optimized_batch_size_large > optimized_batch_size
    
    def test_benchmark_config_creation(self):
        """Test creation of benchmark configurations."""
        benchmark_configs = EmbeddingOptimizer.create_model_benchmark_config()
        
        assert len(benchmark_configs) > 0
        
        # Check that all model types are included
        model_types = {config["model_type"] for config in benchmark_configs}
        expected_types = {model_type.value for model_type in EmbeddingModelType}
        assert model_types == expected_types
        
        # Check that all use cases are included
        use_cases = {config["use_case"] for config in benchmark_configs}
        assert "hierarchical_indexing" in use_cases
        assert "semantic_search" in use_cases
        assert "keyword_extraction" in use_cases
        
        # Check that test queries are included
        for config in benchmark_configs:
            assert "test_queries" in config
            assert len(config["test_queries"]) > 0
    
    def test_indexing_parameters(self):
        """Test pgvector indexing parameter recommendations."""
        # Test with small embeddings
        small_config = EmbeddingConfig(
            model_name="small-model",
            embedding_dim=384,
            max_sequence_length=256,
            batch_size=32
        )
        
        params = EmbeddingOptimizer.get_indexing_parameters(small_config)
        
        assert "index_type" in params
        assert "distance_metric" in params
        assert params["lists"] == 100  # Expected for small dimensions
        
        # Test with large embeddings
        large_config = EmbeddingConfig(
            model_name="large-model",
            embedding_dim=1536,
            max_sequence_length=512,
            batch_size=16
        )
        
        params_large = EmbeddingOptimizer.get_indexing_parameters(large_config)
        
        assert params_large["lists"] > params["lists"]  # Should have more lists
        assert params_large["probes"] > params["probes"]  # Should have more probes