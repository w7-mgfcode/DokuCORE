import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the application."""
    
    _instance = None
    
    def __new__(cls):
        """
        Singleton pattern implementation.
        
        Returns:
            Config: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration values."""
        # Database configuration
        self.db_url = os.environ.get("DATABASE_URL", "postgresql://docuser:docpassword@db:5432/docdb")
        
        # API configuration
        self.api_port = int(os.environ.get("API_PORT", 9000))
        self.api_host = os.environ.get("API_HOST", "0.0.0.0")
        
        # Repository configuration
        self.repo_path = os.environ.get("REPO_PATH", "/app/repo")
        
        # Embedding model configuration
        self.embedding_model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_dimension = int(os.environ.get("EMBEDDING_DIM", 384))
        
        # Search configuration
        self.search_similarity_threshold = float(os.environ.get("SIMILARITY_THRESHOLD", 0.7))
        self.search_max_results = int(os.environ.get("MAX_SEARCH_RESULTS", 10))
        
        # Logging configuration
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        
        # Authentication configuration
        self.jwt_secret_key = os.environ.get("JWT_SECRET_KEY", "insecure-secret-key-change-in-production")
        self.jwt_token_expire_minutes = int(os.environ.get("JWT_TOKEN_EXPIRE_MINUTES", 30))
        
        # Initialize logging
        self._setup_logging()
        
        logger.info("Configuration loaded")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_database_config(self) -> Dict[str, str]:
        """
        Get database configuration.
        
        Returns:
            Dict[str, str]: Database configuration parameters.
        """
        # Parse connection string to extract components
        # Format: postgresql://user:password@host:port/dbname
        url = self.db_url.replace("postgresql://", "")
        user_pass, host_port_db = url.split("@")
        user, password = user_pass.split(":")
        host_port, dbname = host_port_db.split("/")
        host, port = host_port.split(":")
        
        return {
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "dbname": dbname
        }
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """
        Get embedding model configuration.
        
        Returns:
            Dict[str, Any]: Embedding model configuration parameters.
        """
        return {
            "model_name": self.embedding_model_name,
            "dimension": self.embedding_dimension
        }
    
    def get_search_config(self) -> Dict[str, Any]:
        """
        Get search configuration.
        
        Returns:
            Dict[str, Any]: Search configuration parameters.
        """
        return {
            "similarity_threshold": self.search_similarity_threshold,
            "max_results": self.search_max_results
        }
    
    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get all configuration as a dictionary.
        
        Returns:
            Dict[str, Any]: All configuration parameters.
        """
        return {
            "database": self.get_database_config(),
            "api": {
                "port": self.api_port,
                "host": self.api_host
            },
            "repository": {
                "path": self.repo_path
            },
            "embedding": self.get_embedding_config(),
            "search": self.get_search_config(),
            "logging": {
                "level": self.log_level
            },
            "auth": {
                "token_expire_minutes": self.jwt_token_expire_minutes
            }
        }


# Create a singleton instance
config = Config()