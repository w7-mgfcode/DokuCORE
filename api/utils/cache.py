import logging
import time
from typing import Dict, Any, Optional, Callable, Tuple
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheItem:
    """
    A cache item with expiration.
    
    Attributes:
        value: The cached value.
        expiry: When this item expires.
    """
    def __init__(self, value: Any, ttl_seconds: int):
        """
        Initialize a cache item.
        
        Args:
            value: The value to cache.
            ttl_seconds: Time to live in seconds.
        """
        self.value = value
        self.expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        
    def is_expired(self) -> bool:
        """
        Check if this item is expired.
        
        Returns:
            bool: True if expired, False otherwise.
        """
        return datetime.now() > self.expiry


class Cache:
    """
    A simple in-memory cache with expiration.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Singleton pattern implementation.
        
        Returns:
            Cache: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the cache."""
        self._cache: Dict[str, CacheItem] = {}
        self._hits = 0
        self._misses = 0
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=10)  # Run cleanup every 10 minutes
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            Optional[Any]: The cached value, or None if not found or expired.
        """
        self._maybe_cleanup()
        
        if key not in self._cache:
            self._misses += 1
            return None
            
        item = self._cache[key]
        if item.is_expired():
            self._misses += 1
            del self._cache[key]  # Clean up expired item
            return None
            
        self._hits += 1
        return item.value
        
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
            ttl_seconds: Time to live in seconds (default: 1 hour).
        """
        self._maybe_cleanup()
        self._cache[key] = CacheItem(value, ttl_seconds)
        
    def invalidate(self, key: str) -> None:
        """
        Remove a key from the cache.
        
        Args:
            key: The cache key.
        """
        if key in self._cache:
            del self._cache[key]
            
    def invalidate_pattern(self, pattern: str) -> None:
        """
        Remove all keys that contain a pattern.
        
        Args:
            pattern: The pattern to match against keys.
        """
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self._cache[key]
            
    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        
    def _maybe_cleanup(self) -> None:
        """
        Periodically clean up expired items.
        
        This avoids having to iterate through the entire cache on every operation.
        """
        now = datetime.now()
        if now - self._last_cleanup > self._cleanup_interval:
            self.cleanup()
            self._last_cleanup = now
            
    def cleanup(self) -> int:
        """
        Remove all expired items from the cache.
        
        Returns:
            int: Number of items removed.
        """
        initial_size = len(self._cache)
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        
        for key in expired_keys:
            del self._cache[key]
            
        removed = initial_size - len(self._cache)
        if removed > 0:
            logger.info(f"Cache cleanup: removed {removed} expired items")
        
        return removed
        
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics.
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2%}",
            "last_cleanup": self._last_cleanup.isoformat()
        }


# Function decorator for caching
def cached(
    ttl_seconds: int = 3600,
    key_prefix: str = "",
    cache_instance: Optional[Cache] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live in seconds (default: 1 hour).
        key_prefix: Prefix for cache keys.
        cache_instance: Cache instance to use (default: global instance).
        key_func: Function to generate cache key from args and kwargs.
        
    Returns:
        Callable: Decorated function.
    """
    if cache_instance is None:
        cache_instance = Cache()
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation: prefix + function name + args + kwargs
                arg_str = str(args) if args else ""
                kwarg_str = str(sorted(kwargs.items())) if kwargs else ""
                cache_key = f"{key_prefix}:{func.__name__}:{arg_str}:{kwarg_str}"
                
            # Check cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Cache miss, execute function
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache result
            cache_instance.set(cache_key, result, ttl_seconds)
            
            # Log caching info for slow operations
            if execution_time > 0.5:  # Log if execution takes more than 500ms
                logger.info(f"Cached slow operation '{func.__name__}', execution time: {execution_time:.3f}s")
                
            return result
        return wrapper
    return decorator


# Create a singleton cache instance
cache = Cache()