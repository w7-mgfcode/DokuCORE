"""
Unit tests for the search optimization module.
"""

import pytest
from api.indexing.search_optimizer import (
    SearchOptimizer,
    SearchStrategy,
    SearchConfig
)


class TestSearchConfig:
    """Test cases for the SearchConfig dataclass."""
    
    def test_default_config(self):
        """Test default search configuration values."""
        config = SearchConfig()
        
        assert config.top_k == 10
        assert config.similarity_threshold == 0.7
        assert config.keyword_weight == 0.6
        assert config.semantic_weight == 0.4
        assert config.enable_query_expansion is True
        assert config.use_cache is True
        assert config.strategy == SearchStrategy.BALANCED
    
    def test_custom_config(self):
        """Test custom search configuration."""
        config = SearchConfig(
            top_k=20,
            similarity_threshold=0.8,
            keyword_weight=0.7,
            semantic_weight=0.3,
            strategy=SearchStrategy.PRECISION
        )
        
        assert config.top_k == 20
        assert config.similarity_threshold == 0.8
        assert config.strategy == SearchStrategy.PRECISION


class TestSearchOptimizer:
    """Test cases for the SearchOptimizer class."""
    
    def test_strategy_configs(self):
        """Test that all strategies have predefined configurations."""
        for strategy in SearchStrategy:
            config = SearchOptimizer.get_config_for_strategy(strategy)
            assert isinstance(config, SearchConfig)
            assert config.strategy == strategy
    
    def test_precision_strategy(self):
        """Test precision-focused search configuration."""
        config = SearchOptimizer.get_config_for_strategy(SearchStrategy.PRECISION)
        
        assert config.top_k <= 5  # Should return fewer results
        assert config.similarity_threshold >= 0.85  # High threshold
        assert config.keyword_weight > config.semantic_weight  # Prefer exact matches
        assert config.enable_query_expansion is False  # No expansion for precision
    
    def test_recall_strategy(self):
        """Test recall-focused search configuration."""
        config = SearchOptimizer.get_config_for_strategy(SearchStrategy.RECALL)
        
        assert config.top_k >= 20  # Should return more results
        assert config.similarity_threshold <= 0.6  # Lower threshold
        assert config.semantic_weight >= config.keyword_weight  # More semantic understanding
        assert config.enable_query_expansion is True  # Expand queries for recall
        assert config.expansion_terms >= 5  # More expansion terms
    
    def test_fast_strategy(self):
        """Test speed-optimized search configuration."""
        config = SearchOptimizer.get_config_for_strategy(SearchStrategy.FAST)
        
        assert config.top_k <= 5  # Fewer results for speed
        assert config.max_depth <= 1  # Shallow traversal
        assert config.use_cache is True  # Caching enabled
        assert config.enable_query_expansion is False  # No expansion for speed
    
    def test_query_type_optimization(self):
        """Test configuration optimization based on query characteristics."""
        # Short query (likely keyword search)
        short_query = "API docs"
        config = SearchOptimizer.optimize_for_query_type(short_query)
        
        assert config.keyword_weight > config.semantic_weight
        
        # Medium query (balanced)
        medium_query = "how to configure authentication"
        config_medium = SearchOptimizer.optimize_for_query_type(medium_query)
        
        assert config_medium.keyword_weight == config_medium.semantic_weight
        
        # Long query (semantic understanding needed)
        long_query = "explain the process of setting up user authentication with JWT tokens in the FastAPI application"
        config_long = SearchOptimizer.optimize_for_query_type(long_query)
        
        assert config_long.semantic_weight > config_long.keyword_weight
        
        # Question query
        question_query = "what is the purpose of hierarchical indexing?"
        config_question = SearchOptimizer.optimize_for_query_type(question_query)
        
        assert config_question.enable_query_expansion is True
        assert config_question.semantic_weight > 0.5
    
    def test_relevance_score_calculation(self):
        """Test relevance score calculation with different parameters."""
        config = SearchConfig(
            keyword_weight=0.6,
            semantic_weight=0.4,
            keyword_boost=1.5,
            title_boost=2.0,
            relationship_decay=0.8
        )
        
        # Keyword match
        score = SearchOptimizer.calculate_relevance_score(
            base_score=0.8,
            match_type="keyword",
            config=config
        )
        
        assert score > 0.8  # Should be boosted
        assert score <= 1.0  # Should be capped
        
        # Semantic match
        score_semantic = SearchOptimizer.calculate_relevance_score(
            base_score=0.8,
            match_type="semantic",
            config=config
        )
        
        assert score_semantic < score  # Keyword should score higher
        
        # Related match with depth
        score_related = SearchOptimizer.calculate_relevance_score(
            base_score=0.8,
            match_type="related-sibling",
            config=config,
            metadata={"depth": 2}
        )
        
        # Should decay with depth
        expected_decay = config.semantic_weight * (config.relationship_decay ** 2)
        assert abs(score_related - (0.8 * expected_decay)) < 0.01
        
        # Title match boost
        score_title = SearchOptimizer.calculate_relevance_score(
            base_score=0.5,
            match_type="semantic",
            config=config,
            metadata={"is_title": True}
        )
        
        assert score_title > 0.5 * config.semantic_weight
    
    def test_query_expansion(self):
        """Test query expansion term generation."""
        # Basic expansion
        query = "create document"
        expansion_terms = SearchOptimizer.get_query_expansion_terms(
            query,
            config=SearchConfig(enable_query_expansion=True, expansion_terms=3)
        )
        
        assert len(expansion_terms) > 0
        assert len(expansion_terms) <= 3
        
        # Should include plurals
        assert any("documents" in term for term in expansion_terms)
        
        # Should include synonyms
        query_with_synonym = "find document"
        expansion_synonym = SearchOptimizer.get_query_expansion_terms(
            query_with_synonym,
            config=SearchConfig(enable_query_expansion=True, expansion_terms=5)
        )
        
        assert any(term in ["search", "locate", "get"] for term in expansion_synonym)
        
        # Disabled expansion
        no_expansion = SearchOptimizer.get_query_expansion_terms(
            query,
            config=SearchConfig(enable_query_expansion=False)
        )
        
        assert len(no_expansion) == 0
    
    def test_result_diversity_optimization(self):
        """Test result diversity optimization."""
        # Create mock results
        results = [
            {"relevance": 0.9, "document_id": 1, "level": 1, "match_type": "keyword"},
            {"relevance": 0.88, "document_id": 1, "level": 2, "match_type": "semantic"},
            {"relevance": 0.85, "document_id": 2, "level": 1, "match_type": "keyword"},
            {"relevance": 0.82, "document_id": 1, "level": 3, "match_type": "related"}
        ]
        
        optimized = SearchOptimizer.optimize_result_diversity(results, diversity_factor=0.3)
        
        # First result should remain the same (highest score)
        assert optimized[0] == results[0]
        
        # Should prefer different documents for diversity
        assert optimized[1]["document_id"] != optimized[0]["document_id"]
        
        # Test with no diversity
        no_diversity = SearchOptimizer.optimize_result_diversity(results, diversity_factor=0.0)
        
        # Should maintain original order
        assert [r["relevance"] for r in no_diversity] == sorted([r["relevance"] for r in results], reverse=True)
    
    def test_search_plan_creation(self):
        """Test search execution plan creation."""
        # Small corpus
        plan = SearchOptimizer.create_search_plan(
            query="find user authentication",
            corpus_size=100,
            available_memory_mb=500
        )
        
        assert "phases" in plan
        assert "estimated_time_ms" in plan
        assert "memory_usage_mb" in plan
        
        # Should not need index selection for small corpus
        phase_names = [phase["phase"] for phase in plan["phases"]]
        assert "index_selection" not in phase_names
        
        # Large corpus
        plan_large = SearchOptimizer.create_search_plan(
            query="complex search query with multiple terms",
            corpus_size=50000,
            available_memory_mb=100
        )
        
        # Should include more phases
        phase_names_large = [phase["phase"] for phase in plan_large["phases"]]
        assert "index_selection" in phase_names_large
        assert "query_expansion" in phase_names_large
        
        # Should include optimization recommendations if memory is limited
        if plan_large["memory_usage_mb"] > 100:
            assert "optimizations" in plan_large
    
    def test_benchmark_configuration(self):
        """Test benchmark metric calculation."""
        config = SearchConfig(
            top_k=10,
            enable_query_expansion=True,
            similarity_threshold=0.7
        )
        
        test_queries = ["test query 1", "test query 2"]
        
        metrics = SearchOptimizer.benchmark_configuration(
            config,
            test_queries
        )
        
        assert "avg_query_time" in metrics
        assert "avg_result_count" in metrics
        assert metrics["avg_query_time"] > 0
        assert metrics["avg_result_count"] > 0
        
        # With ground truth
        ground_truth = {
            "test query 1": ["doc1", "doc2"],
            "test query 2": ["doc3", "doc4"]
        }
        
        metrics_with_truth = SearchOptimizer.benchmark_configuration(
            config,
            test_queries,
            ground_truth
        )
        
        assert "precision" in metrics_with_truth
        assert "recall" in metrics_with_truth
        assert "f1_score" in metrics_with_truth
        assert 0 <= metrics_with_truth["f1_score"] <= 1