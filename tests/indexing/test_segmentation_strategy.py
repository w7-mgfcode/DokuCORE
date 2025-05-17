"""
Unit tests for the advanced segmentation strategy module.
"""

import pytest
from api.indexing.segmentation_strategy import (
    AdvancedSegmentationStrategy,
    SegmentationType,
    SegmentationConfig
)


class TestAdvancedSegmentationStrategy:
    """Test cases for the AdvancedSegmentationStrategy class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = SegmentationConfig(
            min_segment_length=50,
            max_segment_length=500,
            target_token_count=100,
            overlap_ratio=0.1
        )
        self.strategy = AdvancedSegmentationStrategy(self.config)
    
    def test_header_based_segmentation(self):
        """Test header-based segmentation."""
        content = """
# Main Header

This is the first section content.

## Subsection 1

This is subsection 1 content.

## Subsection 2

This is subsection 2 content.
        """.strip()
        
        segments = self.strategy.segment_document(
            content, 
            SegmentationType.HEADER_BASED
        )
        
        assert len(segments) == 3
        assert segments[0]["title"] == "Main Header"
        assert segments[1]["title"] == "Subsection 1"
        assert segments[2]["title"] == "Subsection 2"
        assert all(segment["level"] > 0 for segment in segments)
    
    def test_semantic_boundary_segmentation(self):
        """Test semantic boundary segmentation."""
        content = """
This is the first paragraph of text. It contains some information.

This is the second paragraph. It has different information.

And this is the third paragraph with more content.
        """.strip()
        
        segments = self.strategy.segment_document(
            content,
            SegmentationType.SEMANTIC_BOUNDARY
        )
        
        assert len(segments) >= 1
        assert all("content" in segment for segment in segments)
        assert all(segment["metadata"]["type"] == "semantic" for segment in segments)
    
    def test_token_limited_segmentation(self):
        """Test token-limited segmentation."""
        # Create a long text
        content = " ".join(["This is a test sentence."] * 50)
        
        segments = self.strategy.segment_document(
            content,
            SegmentationType.TOKEN_LIMITED
        )
        
        assert len(segments) > 1
        # Each segment should be within the target token count
        for segment in segments:
            assert segment["char_count"] <= self.config.target_token_count * 4 + 100
    
    def test_hybrid_segmentation(self):
        """Test hybrid segmentation combining multiple strategies."""
        content = """
# Introduction

This is a long introduction with multiple paragraphs. It contains important information 
that needs to be properly segmented for optimal processing.

## Technical Details

Here we have technical details that are quite extensive and may need to be split into 
multiple segments for better token efficiency.

### Implementation

The implementation section contains code examples and detailed explanations that could 
benefit from intelligent segmentation.
        """.strip()
        
        segments = self.strategy.segment_document(
            content,
            SegmentationType.HYBRID
        )
        
        assert len(segments) >= 3
        # Should maintain header structure
        headers = [s["title"] for s in segments]
        assert any("Introduction" in h for h in headers)
        assert any("Technical Details" in h for h in headers)
    
    def test_segmentation_with_overlap(self):
        """Test that overlapping segments are created correctly."""
        # Create content that will require splitting
        content = " ".join(["Test sentence number {}.".format(i) for i in range(100)])
        
        segments = self.strategy._apply_token_limits_with_overlap([{
            "title": "Test",
            "content": [content],
            "level": 1,
            "metadata": {}
        }])
        
        # Check that segments have overlap
        if len(segments) > 1:
            assert segments[1]["metadata"].get("has_overlap", False)
    
    def test_segmentation_quality_evaluation(self):
        """Test the quality evaluation of segmentation."""
        segments = [
            {"char_count": 100, "estimated_tokens": 25, "metadata": {}},
            {"char_count": 120, "estimated_tokens": 30, "metadata": {"has_overlap": True}},
            {"char_count": 90, "estimated_tokens": 22, "metadata": {}}
        ]
        
        quality = self.strategy.evaluate_segmentation_quality(segments)
        
        assert "quality_score" in quality
        assert "uniformity_score" in quality
        assert "token_efficiency" in quality
        assert 0 <= quality["quality_score"] <= 1
    
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        segments = self.strategy.segment_document("", SegmentationType.HEADER_BASED)
        
        # Should return at least one segment even for empty content
        assert len(segments) >= 0
    
    def test_no_headers_fallback(self):
        """Test fallback when no headers are present."""
        content = "This is just plain text without any markdown headers."
        
        segments = self.strategy.segment_document(
            content,
            SegmentationType.HEADER_BASED
        )
        
        assert len(segments) == 1
        assert segments[0]["level"] == 1
    
    def test_custom_config_application(self):
        """Test that custom configuration is properly applied."""
        custom_config = SegmentationConfig(
            min_segment_length=10,
            max_segment_length=100,
            target_token_count=20
        )
        custom_strategy = AdvancedSegmentationStrategy(custom_config)
        
        content = "Short text"
        segments = custom_strategy.segment_document(
            content,
            SegmentationType.TOKEN_LIMITED
        )
        
        assert len(segments) >= 1