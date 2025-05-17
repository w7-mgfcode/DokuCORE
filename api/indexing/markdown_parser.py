import re
import logging
from typing import List, Dict, Any, Optional

from .segmentation_strategy import AdvancedSegmentationStrategy, SegmentationType, SegmentationConfig

logger = logging.getLogger(__name__)

# Global segmentation strategy instance
_segmentation_strategy = None

def get_segmentation_strategy(config: Optional[SegmentationConfig] = None) -> AdvancedSegmentationStrategy:
    """Get or create the segmentation strategy instance."""
    global _segmentation_strategy
    if _segmentation_strategy is None or config is not None:
        _segmentation_strategy = AdvancedSegmentationStrategy(config)
    return _segmentation_strategy

def extract_hierarchy_from_markdown(content: str, use_advanced_segmentation: bool = True) -> List[Dict[str, Any]]:
    """
    Process markdown content into hierarchical structure.
    
    Args:
        content (str): Markdown content to parse.
        use_advanced_segmentation (bool): Whether to use advanced segmentation strategy.
        
    Returns:
        List[Dict[str, Any]]: List of hierarchy nodes with title, content, level, and sequence number.
    """
    if use_advanced_segmentation:
        # Use advanced segmentation strategy
        strategy = get_segmentation_strategy()
        segments = strategy.segment_document(content, SegmentationType.HYBRID)
        
        # Convert segments to nodes format
        nodes = []
        for i, segment in enumerate(segments):
            nodes.append({
                "title": segment["title"],
                "content": segment["content"],
                "level": segment["level"],
                "seq_num": i,
                "metadata": segment.get("metadata", {})
            })
        
        # Log segmentation quality
        quality_metrics = strategy.evaluate_segmentation_quality(segments)
        logger.info(f"Segmentation quality: {quality_metrics}")
        
        return nodes
    
    # Fallback to original implementation
    lines = content.split('\n')
    nodes = []
    current_headers = [None] * 6  # max 6 level headers (h1-h6)
    seq_counter = 0

    current_content = []
    current_level = 0
    current_title = ""

    for line in lines:
        header_match = re.match(r'^(#{1,6})\s+(.+)', line)

        if header_match:
            # If there's previous content, save it
            if current_title:
                nodes.append({
                    "title": current_title,
                    "content": "\n".join(current_content).strip(),
                    "level": current_level,
                    "seq_num": seq_counter
                })
                seq_counter += 1
                current_content = []

            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            current_level = level
            current_title = title
            current_headers[level-1] = title
            # Clear lower level headers
            for i in range(level, 6):
                current_headers[i] = None
        else:
            # Add line to current content
            if current_title:
                current_content.append(line)

    # Don't forget the last section
    if current_title:
        nodes.append({
            "title": current_title,
            "content": "\n".join(current_content).strip(),
            "level": current_level,
            "seq_num": seq_counter
        })

    # If no headers, create a default node
    if not nodes:
        nodes = [{
            "title": "Document Content",
            "content": content,
            "level": 1,
            "seq_num": 0
        }]

    return nodes