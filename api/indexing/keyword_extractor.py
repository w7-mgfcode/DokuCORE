import re
import logging
import nltk
from nltk.corpus import stopwords
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)

def extract_keywords(title: str, content: str) -> Dict[str, float]:
    """
    Extract keywords from text with importance weights.
    
    Args:
        title (str): Title of the document section.
        content (str): Content of the document section.
        
    Returns:
        Dict[str, float]: Dictionary of keywords with importance weights.
    """
    try:
        # Load stopwords
        stop_words = set(stopwords.words('english'))

        # Prepare text
        text = f"{title} {content}".lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)

        # Tokenize
        words = nltk.word_tokenize(text)

        # Remove stopwords and too short words
        words = [word for word in words if word not in stop_words and len(word) > 2]

        # Calculate frequency
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1

        # Normalize by maximum frequency
        max_freq = max(word_freq.values()) if word_freq else 1
        keywords = {word: freq / max_freq for word, freq in word_freq.items()}

        # Keep only the most important keywords (top 10)
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_keywords[:10])
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return {}