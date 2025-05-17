"""
Relationship strength threshold definitions for hierarchical indexing.

This module defines optimal thresholds for various relationship types
based on research and empirical testing for document similarity.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class RelationshipType(Enum):
    """Types of relationships between document nodes."""
    PARENT_CHILD = "parent_child"
    SIBLING = "sibling"
    SEMANTIC = "semantic"
    KEYWORD_BASED = "keyword_based"
    CROSS_REFERENCE = "cross_reference"
    IMPLICIT = "implicit"

@dataclass
class RelationshipThreshold:
    """
    Threshold configuration for different relationship types.
    
    Based on research findings:
    1. Semantic similarity > 0.7 indicates strong relationship
    2. Keyword overlap > 0.3 suggests topical relevance
    3. Parent-child relationships are always 1.0
    4. Sibling relationships vary by distance (0.3-0.8)
    """
    min_strength: float
    strong_threshold: float
    very_strong_threshold: float
    decay_factor: Optional[float] = None  # For distance-based decay

class RelationshipManager:
    """Manages relationship thresholds and strength calculations."""
    
    # Research-based optimal thresholds
    THRESHOLDS = {
        RelationshipType.PARENT_CHILD: RelationshipThreshold(
            min_strength=1.0,
            strong_threshold=1.0,
            very_strong_threshold=1.0
        ),
        RelationshipType.SIBLING: RelationshipThreshold(
            min_strength=0.3,
            strong_threshold=0.6,
            very_strong_threshold=0.8,
            decay_factor=0.1  # Decay by distance
        ),
        RelationshipType.SEMANTIC: RelationshipThreshold(
            min_strength=0.7,
            strong_threshold=0.8,
            very_strong_threshold=0.9
        ),
        RelationshipType.KEYWORD_BASED: RelationshipThreshold(
            min_strength=0.3,
            strong_threshold=0.5,
            very_strong_threshold=0.7
        ),
        RelationshipType.CROSS_REFERENCE: RelationshipThreshold(
            min_strength=0.5,
            strong_threshold=0.7,
            very_strong_threshold=0.9
        ),
        RelationshipType.IMPLICIT: RelationshipThreshold(
            min_strength=0.4,
            strong_threshold=0.6,
            very_strong_threshold=0.8
        )
    }
    
    @classmethod
    def calculate_sibling_strength(cls, 
                                  level_distance: int, 
                                  sequence_distance: int) -> float:
        """
        Calculate sibling relationship strength based on distance.
        
        Args:
            level_distance: Difference in hierarchy levels (should be 0 for siblings)
            sequence_distance: Distance in sequence numbers
            
        Returns:
            Calculated strength value
        """
        threshold = cls.THRESHOLDS[RelationshipType.SIBLING]
        
        # Siblings must be at the same level
        if level_distance != 0:
            return 0.0
        
        # Calculate strength with decay
        base_strength = threshold.very_strong_threshold
        decay = threshold.decay_factor * sequence_distance
        
        strength = max(threshold.min_strength, base_strength - decay)
        return strength
    
    @classmethod
    def calculate_semantic_strength(cls, cosine_similarity: float) -> float:
        """
        Calculate semantic relationship strength from cosine similarity.
        
        Args:
            cosine_similarity: Cosine similarity between embeddings (0-1)
            
        Returns:
            Relationship strength value
        """
        threshold = cls.THRESHOLDS[RelationshipType.SEMANTIC]
        
        # Only create relationship if above minimum threshold
        if cosine_similarity < threshold.min_strength:
            return 0.0
        
        # Scale the similarity to emphasize stronger relationships
        # Using sigmoid-like scaling
        import math
        
        # Shift and scale to make threshold.min_strength = 0.5
        x = (cosine_similarity - threshold.min_strength) / (1 - threshold.min_strength)
        # Apply sigmoid scaling
        scaled = 1 / (1 + math.exp(-6 * (x - 0.5)))
        
        # Map back to strength range
        strength = threshold.min_strength + scaled * (1 - threshold.min_strength)
        
        return min(1.0, strength)
    
    @classmethod
    def calculate_keyword_strength(cls, 
                                  keyword_overlap: float,
                                  weighted_overlap: float) -> float:
        """
        Calculate keyword-based relationship strength.
        
        Args:
            keyword_overlap: Percentage of overlapping keywords (0-1)
            weighted_overlap: Overlap weighted by keyword importance (0-1)
            
        Returns:
            Relationship strength value
        """
        threshold = cls.THRESHOLDS[RelationshipType.KEYWORD_BASED]
        
        # Combine simple and weighted overlap
        combined_score = 0.3 * keyword_overlap + 0.7 * weighted_overlap
        
        if combined_score < threshold.min_strength:
            return 0.0
        
        # Linear scaling
        strength = threshold.min_strength + (combined_score - threshold.min_strength) * \
                  (1 - threshold.min_strength) / (1 - threshold.min_strength)
        
        return min(1.0, strength)
    
    @classmethod
    def should_create_relationship(cls, 
                                  relationship_type: RelationshipType,
                                  strength: float) -> bool:
        """
        Determine if a relationship should be created based on strength.
        
        Args:
            relationship_type: Type of relationship
            strength: Calculated strength value
            
        Returns:
            True if relationship should be created
        """
        threshold = cls.THRESHOLDS[relationship_type]
        return strength >= threshold.min_strength
    
    @classmethod
    def get_relationship_quality(cls,
                                relationship_type: RelationshipType,
                                strength: float) -> str:
        """
        Get qualitative description of relationship strength.
        
        Args:
            relationship_type: Type of relationship
            strength: Relationship strength value
            
        Returns:
            Quality description ("weak", "moderate", "strong", "very_strong")
        """
        threshold = cls.THRESHOLDS[relationship_type]
        
        if strength < threshold.min_strength:
            return "none"
        elif strength < threshold.strong_threshold:
            return "weak"
        elif strength < threshold.very_strong_threshold:
            return "strong"
        else:
            return "very_strong"
    
    @classmethod
    def get_adaptive_threshold(cls,
                             relationship_type: RelationshipType,
                             document_density: float,
                             domain_specificity: float = 0.5) -> RelationshipThreshold:
        """
        Get adaptive thresholds based on document characteristics.
        
        Args:
            relationship_type: Type of relationship
            document_density: Density of documents in the corpus (0-1)
            domain_specificity: How domain-specific the content is (0-1)
            
        Returns:
            Adapted threshold configuration
        """
        base_threshold = cls.THRESHOLDS[relationship_type]
        
        # For dense document collections, raise thresholds to reduce noise
        density_factor = 1 + (document_density * 0.2)
        
        # For domain-specific content, lower thresholds as relationships are more meaningful
        domain_factor = 1 - (domain_specificity * 0.1)
        
        # Apply factors
        adapted = RelationshipThreshold(
            min_strength=min(0.95, base_threshold.min_strength * density_factor * domain_factor),
            strong_threshold=min(0.95, base_threshold.strong_threshold * density_factor * domain_factor),
            very_strong_threshold=min(0.98, base_threshold.very_strong_threshold * density_factor * domain_factor),
            decay_factor=base_threshold.decay_factor
        )
        
        return adapted
    
    @staticmethod
    def calculate_combined_strength(relationships: Dict[RelationshipType, float]) -> float:
        """
        Calculate combined strength from multiple relationship types.
        
        Args:
            relationships: Dictionary of relationship types and their strengths
            
        Returns:
            Combined strength value
        """
        if not relationships:
            return 0.0
        
        # Weighted combination of different relationship types
        weights = {
            RelationshipType.PARENT_CHILD: 1.0,
            RelationshipType.SEMANTIC: 0.8,
            RelationshipType.CROSS_REFERENCE: 0.7,
            RelationshipType.KEYWORD_BASED: 0.6,
            RelationshipType.SIBLING: 0.5,
            RelationshipType.IMPLICIT: 0.4
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for rel_type, strength in relationships.items():
            weight = weights.get(rel_type, 0.5)
            weighted_sum += strength * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def optimize_thresholds_for_corpus(
        corpus_stats: Dict[str, Any],
        target_relationship_density: float = 0.1
    ) -> Dict[RelationshipType, RelationshipThreshold]:
        """
        Optimize thresholds based on corpus statistics.
        
        Args:
            corpus_stats: Statistics about the document corpus
            target_relationship_density: Desired density of relationships (0-1)
            
        Returns:
            Optimized thresholds for each relationship type
        """
        # Example corpus stats:
        # {
        #     "avg_document_length": 2000,
        #     "total_documents": 500,
        #     "avg_similarity": 0.65,
        #     "similarity_std": 0.15,
        #     "domain": "technical"
        # }
        
        optimized_thresholds = {}
        
        # Base adjustment factor
        avg_similarity = corpus_stats.get("avg_similarity", 0.5)
        similarity_std = corpus_stats.get("similarity_std", 0.2)
        
        # If average similarity is high, we need higher thresholds
        adjustment_factor = 1.0
        if avg_similarity > 0.6:
            adjustment_factor = 1 + (avg_similarity - 0.6) * 0.5
        
        for rel_type, base_threshold in RelationshipManager.THRESHOLDS.items():
            # Adjust based on corpus characteristics
            if rel_type == RelationshipType.SEMANTIC:
                # For semantic relationships, use statistical approach
                # Set threshold at mean + 1 standard deviation
                min_threshold = min(0.9, avg_similarity + similarity_std)
                
                optimized_thresholds[rel_type] = RelationshipThreshold(
                    min_strength=min_threshold,
                    strong_threshold=min(0.95, min_threshold + 0.1),
                    very_strong_threshold=min(0.98, min_threshold + 0.2)
                )
            else:
                # For other types, apply general adjustment
                optimized_thresholds[rel_type] = RelationshipThreshold(
                    min_strength=min(0.95, base_threshold.min_strength * adjustment_factor),
                    strong_threshold=min(0.95, base_threshold.strong_threshold * adjustment_factor),
                    very_strong_threshold=min(0.98, base_threshold.very_strong_threshold * adjustment_factor),
                    decay_factor=base_threshold.decay_factor
                )
        
        return optimized_thresholds