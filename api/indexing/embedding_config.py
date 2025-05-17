"""
Embedding model configuration and parameter optimization.

This module defines optimal parameters for embedding models based on research
and benchmarks for hierarchical document indexing.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class EmbeddingModelType(Enum):
    """Supported embedding model types."""
    MINILM = "all-MiniLM-L6-v2"  # Default, 384 dimensions
    MPNET = "all-mpnet-base-v2"  # Higher quality, 768 dimensions
    ADA = "text-embedding-ada-002"  # OpenAI, 1536 dimensions
    INSTRUCTOR = "instructor-large"  # Task-specific, 768 dimensions
    E5 = "e5-large-v2"  # Multilingual, 1024 dimensions

@dataclass
class EmbeddingConfig:
    """
    Configuration for embedding models.
    
    Based on research findings:
    1. Dimension size affects retrieval quality and storage
    2. Batch size impacts performance
    3. Max sequence length affects context understanding
    """
    model_name: str
    embedding_dim: int
    max_sequence_length: int
    batch_size: int
    normalize_embeddings: bool = True
    device: str = "cpu"  # or "cuda"
    pooling_strategy: str = "mean"  # mean, max, or cls
    
    # Advanced parameters
    precision: str = "float32"  # float16 for faster computation
    cache_folder: Optional[str] = None
    show_progress_bar: bool = True
    
    # Task-specific prefixes (for models like instructor)
    query_prefix: Optional[str] = None
    document_prefix: Optional[str] = None

class EmbeddingOptimizer:
    """
    Optimizes embedding parameters for hierarchical document indexing.
    """
    
    # Research-based optimal configurations
    MODEL_CONFIGS = {
        EmbeddingModelType.MINILM: EmbeddingConfig(
            model_name="all-MiniLM-L6-v2",
            embedding_dim=384,
            max_sequence_length=256,
            batch_size=32,
            normalize_embeddings=True,
            pooling_strategy="mean"
        ),
        EmbeddingModelType.MPNET: EmbeddingConfig(
            model_name="all-mpnet-base-v2",
            embedding_dim=768,
            max_sequence_length=384,
            batch_size=16,
            normalize_embeddings=True,
            pooling_strategy="mean"
        ),
        EmbeddingModelType.ADA: EmbeddingConfig(
            model_name="text-embedding-ada-002",
            embedding_dim=1536,
            max_sequence_length=8191,
            batch_size=100,  # API-based
            normalize_embeddings=True,
            pooling_strategy="api"
        ),
        EmbeddingModelType.INSTRUCTOR: EmbeddingConfig(
            model_name="hkunlp/instructor-large",
            embedding_dim=768,
            max_sequence_length=512,
            batch_size=16,
            normalize_embeddings=True,
            pooling_strategy="mean",
            query_prefix="Represent the question for retrieving supporting documents: ",
            document_prefix="Represent the document for retrieval: "
        ),
        EmbeddingModelType.E5: EmbeddingConfig(
            model_name="intfloat/e5-large-v2",
            embedding_dim=1024,
            max_sequence_length=512,
            batch_size=16,
            normalize_embeddings=True,
            pooling_strategy="mean",
            query_prefix="query: ",
            document_prefix="passage: "
        )
    }
    
    @classmethod
    def get_optimal_config(cls, 
                          model_type: EmbeddingModelType,
                          use_case: str = "hierarchical_indexing") -> EmbeddingConfig:
        """
        Get optimal configuration for a specific model and use case.
        
        Args:
            model_type: The embedding model type
            use_case: The specific use case (hierarchical_indexing, semantic_search, etc.)
            
        Returns:
            Optimized embedding configuration
        """
        base_config = cls.MODEL_CONFIGS[model_type]
        
        # Adjust parameters based on use case
        if use_case == "hierarchical_indexing":
            # For hierarchical indexing, we need good context understanding
            config = EmbeddingConfig(
                **base_config.__dict__
            )
            config.max_sequence_length = min(512, base_config.max_sequence_length)
            
        elif use_case == "keyword_extraction":
            # For keywords, shorter sequences are fine
            config = EmbeddingConfig(
                **base_config.__dict__
            )
            config.max_sequence_length = min(128, base_config.max_sequence_length)
            config.batch_size = base_config.batch_size * 2  # Can process more
            
        elif use_case == "semantic_search":
            # For search, we want maximum context
            config = EmbeddingConfig(
                **base_config.__dict__
            )
            # Keep original max sequence length
            
        else:
            config = base_config
            
        return config
    
    @staticmethod
    def calculate_memory_usage(config: EmbeddingConfig, 
                             num_documents: int) -> Dict[str, float]:
        """
        Calculate estimated memory usage for embeddings.
        
        Args:
            config: Embedding configuration
            num_documents: Number of documents to index
            
        Returns:
            Memory usage estimates in MB
        """
        # Base calculation: dim * sizeof(float) * num_docs
        bytes_per_float = 4 if config.precision == "float32" else 2
        
        embedding_memory = (config.embedding_dim * bytes_per_float * num_documents) / (1024 * 1024)
        
        # Model memory (approximate)
        model_memory = {
            "all-MiniLM-L6-v2": 90,  # MB
            "all-mpnet-base-v2": 420,
            "hkunlp/instructor-large": 1350,
            "intfloat/e5-large-v2": 1340,
        }.get(config.model_name, 500)
        
        # Index overhead (pgvector)
        index_overhead = embedding_memory * 0.2  # 20% overhead
        
        return {
            "embedding_storage_mb": embedding_memory,
            "model_memory_mb": model_memory,
            "index_overhead_mb": index_overhead,
            "total_mb": embedding_memory + model_memory + index_overhead
        }
    
    @staticmethod
    def recommend_model(requirements: Dict[str, Any]) -> EmbeddingModelType:
        """
        Recommend an embedding model based on requirements.
        
        Args:
            requirements: Dict with keys like 'max_memory_mb', 'quality_priority', 
                         'speed_priority', 'multilingual', etc.
                         
        Returns:
            Recommended model type
        """
        max_memory = requirements.get('max_memory_mb', float('inf'))
        quality_priority = requirements.get('quality_priority', 5)  # 1-10
        speed_priority = requirements.get('speed_priority', 5)  # 1-10
        multilingual = requirements.get('multilingual', False)
        
        # Score each model
        scores = {}
        
        for model_type in EmbeddingModelType:
            config = EmbeddingOptimizer.MODEL_CONFIGS[model_type]
            score = 0
            
            # Memory constraint
            model_memory = {
                EmbeddingModelType.MINILM: 90,
                EmbeddingModelType.MPNET: 420,
                EmbeddingModelType.ADA: 0,  # API-based
                EmbeddingModelType.INSTRUCTOR: 1350,
                EmbeddingModelType.E5: 1340,
            }[model_type]
            
            if model_memory > max_memory:
                continue
                
            # Quality scoring
            quality_scores = {
                EmbeddingModelType.MINILM: 6,
                EmbeddingModelType.MPNET: 8,
                EmbeddingModelType.ADA: 9,
                EmbeddingModelType.INSTRUCTOR: 8.5,
                EmbeddingModelType.E5: 8.5,
            }
            score += quality_scores[model_type] * quality_priority
            
            # Speed scoring (inverse of model size)
            speed_scores = {
                EmbeddingModelType.MINILM: 9,
                EmbeddingModelType.MPNET: 7,
                EmbeddingModelType.ADA: 6,  # API latency
                EmbeddingModelType.INSTRUCTOR: 5,
                EmbeddingModelType.E5: 5,
            }
            score += speed_scores[model_type] * speed_priority
            
            # Multilingual support
            if multilingual:
                multilingual_bonus = {
                    EmbeddingModelType.MINILM: 0,
                    EmbeddingModelType.MPNET: 0,
                    EmbeddingModelType.ADA: 5,
                    EmbeddingModelType.INSTRUCTOR: 3,
                    EmbeddingModelType.E5: 5,
                }
                score += multilingual_bonus[model_type]
            
            scores[model_type] = score
        
        # Return model with highest score
        return max(scores.items(), key=lambda x: x[1])[0]
    
    @staticmethod
    def optimize_batch_size(config: EmbeddingConfig, 
                          available_memory_mb: float) -> int:
        """
        Optimize batch size based on available memory.
        
        Args:
            config: Current embedding configuration
            available_memory_mb: Available GPU/CPU memory in MB
            
        Returns:
            Optimized batch size
        """
        # Estimate memory per batch item
        # Formula: max_seq_len * hidden_size * 4 bytes * 3 (gradients, activations)
        memory_per_item = (config.max_sequence_length * 768 * 4 * 3) / (1024 * 1024)
        
        # Leave 20% memory headroom
        usable_memory = available_memory_mb * 0.8
        
        # Calculate optimal batch size
        optimal_batch_size = int(usable_memory / memory_per_item)
        
        # Ensure it's within reasonable bounds
        return max(1, min(optimal_batch_size, 128))

    @staticmethod
    def create_model_benchmark_config() -> List[Dict[str, Any]]:
        """
        Create configurations for benchmarking different models.
        
        Returns:
            List of benchmark configurations
        """
        benchmark_configs = []
        
        for model_type in EmbeddingModelType:
            for use_case in ["hierarchical_indexing", "semantic_search", "keyword_extraction"]:
                config = EmbeddingOptimizer.get_optimal_config(model_type, use_case)
                
                benchmark_configs.append({
                    "model_type": model_type.value,
                    "use_case": use_case,
                    "config": config,
                    "test_queries": [
                        "Find documentation about user authentication",
                        "API endpoint for creating documents",
                        "How to configure Docker compose",
                        "Database schema migrations",
                        "Error handling best practices"
                    ]
                })
        
        return benchmark_configs
    
    @staticmethod
    def get_indexing_parameters(config: EmbeddingConfig) -> Dict[str, Any]:
        """
        Get optimal pgvector indexing parameters for the embedding configuration.
        
        Args:
            config: Embedding configuration
            
        Returns:
            Dictionary of indexing parameters
        """
        # Based on pgvector documentation and benchmarks
        if config.embedding_dim <= 384:
            lists = 100  # Smaller dimensions need fewer lists
            probes = 10
        elif config.embedding_dim <= 768:
            lists = 200
            probes = 20
        else:
            lists = 400
            probes = 40
            
        return {
            "index_type": "hnsw",  # or "ivfflat"
            "m": 16,  # Number of connections per layer (HNSW)
            "ef_construction": 64,  # Size of dynamic candidate list
            "ef_search": 40,  # Size of dynamic candidate list for search
            "lists": lists,  # Number of lists (IVFFlat)
            "probes": probes,  # Number of probes (IVFFlat)
            "distance_metric": "cosine"  # or "l2", "inner_product"
        }