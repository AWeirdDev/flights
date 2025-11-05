"""
Simple in-memory cache with TTL (Time To Live) support for flight data.
"""
import time
import hashlib
from typing import Optional, Any, Dict, Tuple
from threading import Lock


class TTLCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache with default TTL.

        Args:
            default_ttl: Default time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()

    def _is_expired(self, expiry_time: float) -> bool:
        """Check if a cache entry has expired."""
        return time.time() > expiry_time

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry_time = self._cache[key]

            if self._is_expired(expiry_time):
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        expiry_time = time.time() + ttl

        with self._lock:
            self._cache[key] = (value, expiry_time)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, (_, expiry_time) in self._cache.items()
                if self._is_expired(expiry_time)
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

    def size(self) -> int:
        """Get current number of cache entries (including expired)."""
        with self._lock:
            return len(self._cache)

    @staticmethod
    def create_cache_key(*args, **kwargs) -> str:
        """
        Create a deterministic cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash-based cache key
        """
        # Create a stable string representation
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)

        # Return hash for consistent key length
        return hashlib.sha256(key_string.encode()).hexdigest()


# Global cache instance for flight queries
_flight_cache: Optional[TTLCache] = None


def get_flight_cache(ttl: int = 300) -> TTLCache:
    """
    Get or create the global flight cache instance.

    Args:
        ttl: Default TTL in seconds (only used when creating new cache)

    Returns:
        Global TTLCache instance
    """
    global _flight_cache
    if _flight_cache is None:
        _flight_cache = TTLCache(default_ttl=ttl)
    return _flight_cache


def clear_flight_cache() -> None:
    """Clear the global flight cache."""
    global _flight_cache
    if _flight_cache is not None:
        _flight_cache.clear()
