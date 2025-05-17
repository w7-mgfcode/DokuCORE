"""
Unit tests for the relationship thresholds module.
"""

import pytest
from api.indexing.relationship_thresholds import (
    RelationshipManager,
    RelationshipType,
    RelationshipThreshold
)


class TestRelationshipThreshold:
    """Test cases for the RelationshipThreshold dataclass."""
    
    def test_threshold_creation(self):
        """Test creating a relationship threshold."""
        threshold = RelationshipThreshold(
            min_strength=0.5,
            strong_threshold=0.7,
            very_strong_threshold=0.9,
            decay_factor=0.1
        )
        
        assert threshold.min_strength == 0.5
        assert threshold.strong_threshold == 0.7
        assert threshold.very_strong_threshold == 0.9
        assert threshold.decay_factor == 0.1
    
    def test_threshold_ordering(self):
        """Test that thresholds are properly ordered."""
        threshold = RelationshipThreshold(
            min_strength=0.3,
            strong_threshold=0.6,
            very_strong_threshold=0.8
        )
        
        assert threshold.min_strength < threshold.strong_threshold
        assert threshold.strong_threshold < threshold.very_strong_threshold


class TestRelationshipManager:
    """Test cases for the RelationshipManager class."""
    
    def test_default_thresholds(self):
        """Test that default thresholds are properly defined."""
        # Check that all relationship types have thresholds
        for rel_type in RelationshipType:
            assert rel_type in RelationshipManager.THRESHOLDS
            threshold = RelationshipManager.THRESHOLDS[rel_type]
            assert isinstance(threshold, RelationshipThreshold)
    
    def test_sibling_strength_calculation(self):
        """Test sibling relationship strength calculation."""
        # Same level, adjacent siblings
        strength = RelationshipManager.calculate_sibling_strength(
            level_distance=0,
            sequence_distance=1
        )
        assert strength > 0.5  # Should be relatively strong
        
        # Same level, distant siblings
        strength_distant = RelationshipManager.calculate_sibling_strength(
            level_distance=0,
            sequence_distance=5
        )
        assert strength_distant < strength  # Should be weaker
        assert strength_distant >= RelationshipManager.THRESHOLDS[RelationshipType.SIBLING].min_strength
        
        # Different levels (not siblings)
        strength_diff_level = RelationshipManager.calculate_sibling_strength(
            level_distance=1,
            sequence_distance=1
        )
        assert strength_diff_level == 0.0
    
    def test_semantic_strength_calculation(self):
        """Test semantic relationship strength calculation."""
        # High similarity
        strength = RelationshipManager.calculate_semantic_strength(0.9)
        assert strength > 0.8
        
        # Medium similarity
        strength_medium = RelationshipManager.calculate_semantic_strength(0.75)
        assert strength_medium < strength
        assert strength_medium > 0.7
        
        # Below threshold
        strength_low = RelationshipManager.calculate_semantic_strength(0.5)
        assert strength_low == 0.0
        
        # Edge case: exactly at threshold
        threshold = RelationshipManager.THRESHOLDS[RelationshipType.SEMANTIC].min_strength
        strength_threshold = RelationshipManager.calculate_semantic_strength(threshold)
        assert strength_threshold == threshold
    
    def test_keyword_strength_calculation(self):
        """Test keyword-based relationship strength calculation."""
        # High overlap
        strength = RelationshipManager.calculate_keyword_strength(
            keyword_overlap=0.8,
            weighted_overlap=0.9
        )
        assert strength > 0.7
        
        # Low overlap
        strength_low = RelationshipManager.calculate_keyword_strength(
            keyword_overlap=0.2,
            weighted_overlap=0.1
        )
        assert strength_low == 0.0
        
        # Mixed overlap (weighted more important)
        strength_mixed = RelationshipManager.calculate_keyword_strength(
            keyword_overlap=0.2,
            weighted_overlap=0.8
        )
        assert strength_mixed > 0.3  # Should pass threshold due to high weighted overlap
    
    def test_should_create_relationship(self):
        """Test relationship creation decision."""
        # Should create semantic relationship
        should_create = RelationshipManager.should_create_relationship(
            RelationshipType.SEMANTIC,
            strength=0.8
        )
        assert should_create is True
        
        # Should not create weak semantic relationship
        should_not_create = RelationshipManager.should_create_relationship(
            RelationshipType.SEMANTIC,
            strength=0.5
        )
        assert should_not_create is False
        
        # Parent-child always created
        should_create_parent = RelationshipManager.should_create_relationship(
            RelationshipType.PARENT_CHILD,
            strength=1.0
        )
        assert should_create_parent is True
    
    def test_relationship_quality_description(self):
        """Test qualitative relationship descriptions."""
        # Very strong relationship
        quality = RelationshipManager.get_relationship_quality(
            RelationshipType.SEMANTIC,
            strength=0.95
        )
        assert quality == "very_strong"
        
        # Strong relationship
        quality_strong = RelationshipManager.get_relationship_quality(
            RelationshipType.SEMANTIC,
            strength=0.85
        )
        assert quality_strong == "strong"
        
        # Weak relationship
        quality_weak = RelationshipManager.get_relationship_quality(
            RelationshipType.SEMANTIC,
            strength=0.72
        )
        assert quality_weak == "weak"
        
        # No relationship
        quality_none = RelationshipManager.get_relationship_quality(
            RelationshipType.SEMANTIC,
            strength=0.5
        )
        assert quality_none == "none"
    
    def test_adaptive_threshold(self):
        """Test adaptive threshold calculation based on corpus characteristics."""
        # Dense corpus with general content
        adapted_threshold = RelationshipManager.get_adaptive_threshold(
            relationship_type=RelationshipType.SEMANTIC,
            document_density=0.8,
            domain_specificity=0.2
        )
        
        base_threshold = RelationshipManager.THRESHOLDS[RelationshipType.SEMANTIC]
        
        # Dense corpus should have higher thresholds
        assert adapted_threshold.min_strength > base_threshold.min_strength
        
        # Domain-specific sparse corpus
        domain_threshold = RelationshipManager.get_adaptive_threshold(
            relationship_type=RelationshipType.SEMANTIC,
            document_density=0.2,
            domain_specificity=0.9
        )
        
        # Domain-specific content should have lower thresholds
        assert domain_threshold.min_strength < adapted_threshold.min_strength
    
    def test_combined_strength_calculation(self):
        """Test combining multiple relationship types."""
        # Single relationship
        combined = RelationshipManager.calculate_combined_strength({
            RelationshipType.SEMANTIC: 0.8
        })
        assert combined == 0.8
        
        # Multiple relationships
        combined_multi = RelationshipManager.calculate_combined_strength({
            RelationshipType.PARENT_CHILD: 1.0,
            RelationshipType.SEMANTIC: 0.8,
            RelationshipType.KEYWORD_BASED: 0.6
        })
        
        # Should be weighted average
        assert 0.7 < combined_multi < 1.0
        
        # Empty relationships
        combined_empty = RelationshipManager.calculate_combined_strength({})
        assert combined_empty == 0.0
    
    def test_threshold_optimization_for_corpus(self):
        """Test threshold optimization based on corpus statistics."""
        corpus_stats = {
            "avg_document_length": 2000,
            "total_documents": 500,
            "avg_similarity": 0.75,
            "similarity_std": 0.1,
            "domain": "technical"
        }
        
        optimized = RelationshipManager.optimize_thresholds_for_corpus(
            corpus_stats,
            target_relationship_density=0.1
        )
        
        # Should have thresholds for all relationship types
        assert len(optimized) == len(RelationshipType)
        
        # High average similarity should result in higher thresholds
        base_semantic = RelationshipManager.THRESHOLDS[RelationshipType.SEMANTIC]
        optimized_semantic = optimized[RelationshipType.SEMANTIC]
        
        assert optimized_semantic.min_strength > base_semantic.min_strength
        
        # All thresholds should be capped at reasonable values
        for rel_type, threshold in optimized.items():
            assert threshold.min_strength <= 0.95
            assert threshold.very_strong_threshold <= 0.98