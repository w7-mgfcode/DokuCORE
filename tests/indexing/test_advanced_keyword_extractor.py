"""
Unit tests for the advanced keyword extraction module.
"""

import pytest
from api.indexing.advanced_keyword_extractor import (
    AdvancedKeywordExtractor,
    KeywordConfig
)


class TestKeywordConfig:
    """Test cases for the KeywordConfig dataclass."""
    
    def test_default_config(self):
        """Test default keyword configuration."""
        config = KeywordConfig()
        
        assert config.max_keywords == 20
        assert config.min_keyword_length == 2
        assert config.include_phrases is True
        assert config.use_textrank is True
        assert config.use_ner is True
    
    def test_custom_config(self):
        """Test custom keyword configuration."""
        config = KeywordConfig(
            max_keywords=10,
            min_keyword_length=3,
            include_phrases=False,
            domain_terms={"api", "endpoint", "authentication"}
        )
        
        assert config.max_keywords == 10
        assert config.domain_terms == {"api", "endpoint", "authentication"}


class TestAdvancedKeywordExtractor:
    """Test cases for the AdvancedKeywordExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = KeywordConfig(
            max_keywords=10,
            domain_terms={"api", "documentation", "fastapi"}
        )
        self.extractor = AdvancedKeywordExtractor(self.config)
    
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction functionality."""
        text = """
        FastAPI Documentation System
        
        This system provides comprehensive API documentation with advanced search capabilities.
        The documentation includes authentication, endpoints, and data models.
        """
        
        keywords = self.extractor.extract_keywords("FastAPI Docs", text)
        
        assert len(keywords) <= self.config.max_keywords
        assert all(isinstance(score, float) for score in keywords.values())
        assert all(0 <= score <= 1 for score in keywords.values())
        
        # Should include important terms
        keyword_list = list(keywords.keys())
        assert any("documentation" in kw.lower() for kw in keyword_list)
        assert any("api" in kw.lower() for kw in keyword_list)
    
    def test_tfidf_extraction(self):
        """Test TF-IDF keyword extraction."""
        text = "The quick brown fox jumps over the lazy dog. The fox is quick and brown."
        
        keywords = self.extractor._extract_tfidf_keywords(text)
        
        assert len(keywords) > 0
        # Words appearing multiple times should have higher scores
        assert keywords.get("fox", 0) > keywords.get("dog", 0)
        assert keywords.get("quick", 0) > keywords.get("lazy", 0)
    
    def test_textrank_extraction(self):
        """Test TextRank keyword extraction."""
        text = """
        Machine learning is a subset of artificial intelligence. 
        Artificial intelligence encompasses machine learning and deep learning.
        Deep learning is a specialized form of machine learning.
        """
        
        keywords = self.extractor._extract_textrank_keywords(text)
        
        assert len(keywords) > 0
        # Central concepts should have higher scores
        assert "learning" in keywords or "machine" in keywords
    
    def test_ner_extraction(self):
        """Test Named Entity Recognition keyword extraction."""
        text = """
        Google announced its new AI model in San Francisco.
        The CEO of Microsoft, Satya Nadella, discussed cloud computing.
        Amazon Web Services provides infrastructure for many companies.
        """
        
        keywords = self.extractor._extract_ner_keywords(text)
        
        assert len(keywords) > 0
        # Should include organization names
        keyword_list = list(keywords.keys())
        assert any("google" in kw.lower() for kw in keyword_list)
        assert any("microsoft" in kw.lower() for kw in keyword_list)
    
    def test_phrase_extraction(self):
        """Test multi-word phrase extraction."""
        text = """
        The user authentication system uses JSON web tokens.
        API endpoints require proper authentication headers.
        Database connection pooling improves performance significantly.
        """
        
        keywords = self.extractor._extract_phrases(text)
        
        assert len(keywords) > 0
        # Should include multi-word phrases
        keyword_list = list(keywords.keys())
        assert any(len(kw.split()) > 1 for kw in keyword_list)
        
        # Common technical phrases
        assert any("authentication" in kw for kw in keyword_list)
    
    def test_domain_keyword_extraction(self):
        """Test domain-specific keyword extraction."""
        text = """
        The API provides RESTful endpoints for all operations.
        FastAPI automatically generates documentation from your code.
        Authentication is handled through OAuth2 with JWT tokens.
        """
        
        keywords = self.extractor._extract_domain_keywords(text)
        
        assert len(keywords) > 0
        # Should include domain terms with boosted scores
        assert "api" in keywords
        assert "documentation" in keywords
        assert "fastapi" in keywords
        
        # Domain terms should have high scores
        assert all(score > 1.0 for score in keywords.values())
    
    def test_combined_extraction_methods(self):
        """Test combining multiple extraction methods."""
        text = """
        FastAPI Documentation System
        
        This advanced system provides comprehensive API documentation with semantic search.
        It includes user authentication, REST endpoints, and automated documentation generation.
        The system uses PostgreSQL for data storage and pgvector for similarity search.
        """
        
        keywords = self.extractor.extract_keywords("Documentation System", text, use_all_methods=True)
        
        assert len(keywords) <= self.config.max_keywords
        
        # Should include keywords from different methods
        keyword_list = list(keywords.keys())
        
        # Domain terms
        assert any("api" in kw.lower() for kw in keyword_list)
        assert any("documentation" in kw.lower() for kw in keyword_list)
        
        # Technical terms
        assert any("postgresql" in kw.lower() for kw in keyword_list) or any("search" in kw.lower() for kw in keyword_list)
        
        # Should be properly normalized
        assert all(0 <= score <= 1 for score in keywords.values())
    
    def test_tokenization_and_cleaning(self):
        """Test text tokenization and cleaning."""
        text = "This is a TEST!!! With some punctuation... and UPPERCASE words."
        
        words = self.extractor._tokenize_and_clean(text)
        
        assert all(word.islower() for word in words)  # Should be lowercase
        assert all(len(word) >= self.config.min_keyword_length for word in words)
        assert not any(word.isdigit() for word in words)  # No pure numbers
        assert "test" in words
        assert "uppercase" in words
    
    def test_tf_idf_calculations(self):
        """Test TF and IDF calculations."""
        words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
        
        tf = self.extractor._calculate_tf(words)
        
        assert tf["apple"] == 3/6  # 3 occurrences out of 6 total
        assert tf["banana"] == 2/6
        assert tf["cherry"] == 1/6
        
        # Test IDF (simplified version)
        terms = ["apple", "banana", "cherry"]
        idf = self.extractor._calculate_idf(terms)
        
        assert all(score > 0 for score in idf.values())
        # Longer words should have slightly higher IDF
        assert idf["cherry"] >= idf["apple"]
    
    def test_score_normalization(self):
        """Test score normalization."""
        scores = {
            "keyword1": 10.5,
            "keyword2": 5.2,
            "keyword3": 15.8,
            "keyword4": 2.1
        }
        
        normalized = self.extractor._normalize_scores(scores)
        
        assert all(0 <= score <= 1 for score in normalized.values())
        assert normalized["keyword3"] == 1.0  # Highest score
        assert normalized["keyword4"] == 0.0  # Lowest score
        
        # Test with equal scores
        equal_scores = {"a": 5, "b": 5, "c": 5}
        normalized_equal = self.extractor._normalize_scores(equal_scores)
        
        assert all(score == 1.0 for score in normalized_equal.values())
    
    def test_empty_text_handling(self):
        """Test handling of empty or minimal text."""
        # Empty text
        keywords_empty = self.extractor.extract_keywords("", "")
        assert len(keywords_empty) == 0
        
        # Very short text
        keywords_short = self.extractor.extract_keywords("Title", "Word")
        assert len(keywords_short) >= 0  # Should handle gracefully
    
    def test_corpus_statistics_update(self):
        """Test updating corpus statistics for IDF calculation."""
        documents = [
            "Document about API endpoints",
            "Another document about authentication",
            "Third document about database connections"
        ]
        
        self.extractor.update_corpus_statistics(documents)
        
        assert self.extractor.total_documents == 3
        assert len(self.extractor.document_frequencies) > 0
        assert self.extractor.document_frequencies["document"] == 3  # Appears in all
    
    def test_keyword_context_extraction(self):
        """Test extracting context around keywords."""
        text = "This is a long document about API documentation. The API provides various endpoints. Documentation is important."
        keyword = "API"
        
        contexts = self.extractor.get_keyword_context(text, keyword, window_size=20)
        
        assert len(contexts) == 2  # API appears twice
        assert all(keyword in context for context in contexts)
        assert all(len(context) <= 40 + len(keyword) for context in contexts)  # Window size respected