import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def extract_hierarchy_from_markdown(content: str) -> List[Dict[str, Any]]:
    """
    Process markdown content into hierarchical structure.
    
    Args:
        content (str): Markdown content to parse.
        
    Returns:
        List[Dict[str, Any]]: List of hierarchy nodes with title, content, level, and sequence number.
    """
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