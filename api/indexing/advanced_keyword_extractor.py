"""
Advanced keyword extraction algorithms for hierarchical indexing.

This module implements multiple keyword extraction techniques including:
- TF-IDF with corpus statistics
- TextRank graph-based extraction
- Named Entity Recognition (NER)
- Domain-specific keyword detection
- Phrase extraction
"""

import re
import logging
import math
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.chunk import ne_chunk
from nltk.pos_tag import pos_tag
from nltk.util import ngrams
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KeywordConfig:
    """Configuration for keyword extraction."""
    max_keywords: int = 20
    min_keyword_length: int = 2
    max_keyword_length: int = 30
    include_phrases: bool = True
    max_phrase_length: int = 3
    use_textrank: bool = True
    use_ner: bool = True
    domain_terms: Optional[Set[str]] = None
    additional_stopwords: Optional[Set[str]] = None
    
class AdvancedKeywordExtractor:
    """
    Advanced keyword extraction with multiple algorithms.
    
    Combines TF-IDF, TextRank, NER, and phrase extraction for comprehensive
    keyword identification.
    """
    
    def __init__(self, config: Optional[KeywordConfig] = None):
        """Initialize the keyword extractor."""
        self.config = config or KeywordConfig()
        self.stop_words = set(stopwords.words('english'))
        if self.config.additional_stopwords:
            self.stop_words.update(self.config.additional_stopwords)
        
        # Document frequency for IDF calculation
        self.document_frequencies = defaultdict(int)
        self.total_documents = 0
        
        # Domain-specific terms with boosted importance
        self.domain_terms = self.config.domain_terms or set()
        
    def extract_keywords(self, title: str, content: str, 
                        use_all_methods: bool = True) -> Dict[str, float]:
        """
        Extract keywords using multiple methods.
        
        Args:
            title: Document title
            content: Document content
            use_all_methods: Whether to use all extraction methods
            
        Returns:
            Dictionary of keywords with importance scores (0-1)
        """
        text = f"{title} {title} {content}"  # Title counted twice for importance
        
        # Method 1: Enhanced TF-IDF
        tfidf_keywords = self._extract_tfidf_keywords(text)
        
        # Method 2: TextRank algorithm
        textrank_keywords = {}
        if use_all_methods and self.config.use_textrank:
            textrank_keywords = self._extract_textrank_keywords(text)
        
        # Method 3: Named Entity Recognition
        ner_keywords = {}
        if use_all_methods and self.config.use_ner:
            ner_keywords = self._extract_ner_keywords(text)
        
        # Method 4: Phrase extraction
        phrase_keywords = {}
        if use_all_methods and self.config.include_phrases:
            phrase_keywords = self._extract_phrases(text)
        
        # Method 5: Domain-specific terms
        domain_keywords = self._extract_domain_keywords(text)
        
        # Combine all methods with weighted scoring
        combined_keywords = self._combine_keyword_scores(
            tfidf_keywords,
            textrank_keywords,
            ner_keywords,
            phrase_keywords,
            domain_keywords
        )
        
        # Limit to max keywords
        sorted_keywords = sorted(combined_keywords.items(), 
                               key=lambda x: x[1], reverse=True)
        return dict(sorted_keywords[:self.config.max_keywords])
    
    def _extract_tfidf_keywords(self, text: str) -> Dict[str, float]:
        """Extract keywords using enhanced TF-IDF."""
        # Tokenize and clean
        words = self._tokenize_and_clean(text)
        
        # Calculate term frequency
        tf = self._calculate_tf(words)
        
        # Calculate IDF (simplified without corpus)
        idf = self._calculate_idf(tf.keys())
        
        # Calculate TF-IDF
        tfidf_scores = {}
        for word, freq in tf.items():
            tfidf_scores[word] = freq * idf.get(word, 1.0)
            
            # Boost domain terms
            if word in self.domain_terms:
                tfidf_scores[word] *= 2.0
        
        # Normalize scores
        return self._normalize_scores(tfidf_scores)
    
    def _extract_textrank_keywords(self, text: str) -> Dict[str, float]:
        """Extract keywords using TextRank algorithm."""
        try:
            sentences = sent_tokenize(text)
            words_per_sentence = []
            vocabulary = set()
            
            for sentence in sentences:
                words = self._tokenize_and_clean(sentence)
                words_per_sentence.append(words)
                vocabulary.update(words)
            
            if not vocabulary:
                return {}
            
            # Build co-occurrence matrix
            vocab_list = list(vocabulary)
            vocab_index = {word: i for i, word in enumerate(vocab_list)}
            co_occurrence = np.zeros((len(vocabulary), len(vocabulary)))
            
            window_size = 5
            for words in words_per_sentence:
                for i, word1 in enumerate(words):
                    for j in range(max(0, i-window_size), min(len(words), i+window_size+1)):
                        if i != j:
                            word2 = words[j]
                            co_occurrence[vocab_index[word1]][vocab_index[word2]] += 1
            
            # Convert to transition matrix
            degrees = np.sum(co_occurrence, axis=0)
            transition_matrix = np.zeros_like(co_occurrence)
            
            for i in range(len(vocabulary)):
                if degrees[i] > 0:
                    transition_matrix[:, i] = co_occurrence[:, i] / degrees[i]
            
            # Run PageRank algorithm
            damping = 0.85
            scores = np.ones(len(vocabulary)) / len(vocabulary)
            
            for _ in range(30):  # iterations
                scores = (1 - damping) / len(vocabulary) + damping * np.dot(transition_matrix, scores)
            
            # Create keyword scores
            keyword_scores = {word: scores[vocab_index[word]] 
                            for word in vocabulary}
            
            return self._normalize_scores(keyword_scores)
            
        except Exception as e:
            logger.error(f"Error in TextRank extraction: {str(e)}")
            return {}
    
    def _extract_ner_keywords(self, text: str) -> Dict[str, float]:
        """Extract named entities as keywords."""
        try:
            sentences = sent_tokenize(text)
            entities = []
            
            for sentence in sentences:
                words = word_tokenize(sentence)
                pos_tags = pos_tag(words)
                chunks = ne_chunk(pos_tags, binary=False)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity = ' '.join(c[0] for c in chunk)
                        entity_type = chunk.label()
                        entities.append((entity.lower(), entity_type))
            
            # Score entities based on type and frequency
            entity_scores = defaultdict(float)
            entity_type_weights = {
                'PERSON': 0.8,
                'ORGANIZATION': 0.9,
                'GPE': 0.7,  # Geo-political entity
                'LOCATION': 0.6,
                'FACILITY': 0.7,
                'PRODUCT': 0.8,
                'EVENT': 0.7,
                'WORK_OF_ART': 0.6,
                'LANGUAGE': 0.5,
            }
            
            for entity, entity_type in entities:
                weight = entity_type_weights.get(entity_type, 0.5)
                entity_scores[entity] += weight
            
            return self._normalize_scores(dict(entity_scores))
            
        except Exception as e:
            logger.error(f"Error in NER extraction: {str(e)}")
            return {}
    
    def _extract_phrases(self, text: str) -> Dict[str, float]:
        """Extract multi-word phrases as keywords."""
        try:
            sentences = sent_tokenize(text)
            phrases = defaultdict(int)
            
            # POS patterns for valid phrases
            patterns = [
                ['JJ', 'NN'],  # Adjective + Noun
                ['JJ', 'NNS'],  # Adjective + Plural Noun
                ['NN', 'NN'],  # Noun + Noun
                ['NN', 'NNS'],  # Noun + Plural Noun
                ['JJ', 'JJ', 'NN'],  # Two Adjectives + Noun
                ['JJ', 'NN', 'NN'],  # Adjective + Two Nouns
                ['NN', 'IN', 'NN'],  # Noun + Preposition + Noun
            ]
            
            for sentence in sentences:
                words = word_tokenize(sentence.lower())
                pos_tags = pos_tag(words)
                
                # Extract phrases matching patterns
                for pattern in patterns:
                    pattern_length = len(pattern)
                    if pattern_length > self.config.max_phrase_length:
                        continue
                    
                    for i in range(len(pos_tags) - pattern_length + 1):
                        window = pos_tags[i:i+pattern_length]
                        tags = [tag for _, tag in window]
                        
                        if tags == pattern:
                            phrase_words = [word for word, _ in window]
                            # Check if all words are valid (not stopwords)
                            if all(word not in self.stop_words for word in phrase_words):
                                phrase = ' '.join(phrase_words)
                                phrases[phrase] += 1
            
            # Calculate scores based on frequency
            phrase_scores = {}
            max_freq = max(phrases.values()) if phrases else 1
            
            for phrase, freq in phrases.items():
                score = freq / max_freq
                # Boost longer phrases slightly
                word_count = len(phrase.split())
                score *= (1 + 0.1 * (word_count - 1))
                phrase_scores[phrase] = score
            
            return self._normalize_scores(phrase_scores)
            
        except Exception as e:
            logger.error(f"Error in phrase extraction: {str(e)}")
            return {}
    
    def _extract_domain_keywords(self, text: str) -> Dict[str, float]:
        """Extract domain-specific keywords."""
        if not self.domain_terms:
            return {}
        
        words = self._tokenize_and_clean(text)
        word_freq = Counter(words)
        
        domain_keywords = {}
        for term in self.domain_terms:
            if term in word_freq:
                # Score based on frequency and domain importance
                domain_keywords[term] = word_freq[term] * 2.0
        
        return self._normalize_scores(domain_keywords)
    
    def _combine_keyword_scores(self, *keyword_dicts) -> Dict[str, float]:
        """Combine scores from multiple extraction methods."""
        combined_scores = defaultdict(float)
        
        # Weights for different methods
        method_weights = [
            0.3,  # TF-IDF
            0.25,  # TextRank
            0.2,  # NER
            0.15,  # Phrases
            0.1   # Domain terms
        ]
        
        for i, keyword_dict in enumerate(keyword_dicts):
            weight = method_weights[i] if i < len(method_weights) else 0.1
            
            for keyword, score in keyword_dict.items():
                combined_scores[keyword] += score * weight
        
        return dict(combined_scores)
    
    def _tokenize_and_clean(self, text: str) -> List[str]:
        """Tokenize and clean text."""
        # Basic cleaning
        text = text.lower()
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Tokenize
        words = word_tokenize(text)
        
        # Filter
        words = [
            word for word in words 
            if word not in self.stop_words 
            and self.config.min_keyword_length <= len(word) <= self.config.max_keyword_length
            and not word.isdigit()
        ]
        
        return words
    
    def _calculate_tf(self, words: List[str]) -> Dict[str, float]:
        """Calculate term frequency."""
        word_freq = Counter(words)
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        tf = {}
        for word, freq in word_freq.items():
            tf[word] = freq / total_words
        
        return tf
    
    def _calculate_idf(self, terms: List[str]) -> Dict[str, float]:
        """Calculate inverse document frequency (simplified)."""
        # In a real implementation, this would use corpus statistics
        # Here we use a simplified version based on word length and commonality
        
        idf = {}
        for term in terms:
            # Longer words are generally more specific
            length_factor = min(len(term) / 10, 1.0)
            
            # Estimate document frequency (would be from corpus in production)
            estimated_df = 0.5  # Default estimate
            
            # Calculate IDF
            idf[term] = math.log(2 / (1 + estimated_df)) * (1 + length_factor)
        
        return idf
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return {}
        
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score == min_score:
            return {k: 1.0 for k in scores}
        
        normalized = {}
        for keyword, score in scores.items():
            normalized[keyword] = (score - min_score) / (max_score - min_score)
        
        return normalized
    
    def update_corpus_statistics(self, documents: List[str]):
        """Update corpus statistics for better IDF calculation."""
        self.total_documents = len(documents)
        self.document_frequencies.clear()
        
        for doc in documents:
            words = set(self._tokenize_and_clean(doc))
            for word in words:
                self.document_frequencies[word] += 1
    
    def get_keyword_context(self, text: str, keyword: str, 
                          window_size: int = 50) -> List[str]:
        """Get context windows around keyword occurrences."""
        contexts = []
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        # Find all occurrences
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            
            # Extract context window
            context_start = max(0, pos - window_size)
            context_end = min(len(text), pos + len(keyword) + window_size)
            context = text[context_start:context_end]
            
            contexts.append(context)
            start = pos + 1
        
        return contexts