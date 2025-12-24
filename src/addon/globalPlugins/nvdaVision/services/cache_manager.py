"""Cache manager service.

This module manages recognition result caching using SQLite database.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..schemas.screenshot import Screenshot
from ..schemas.recognition_result import RecognitionResult
from ..infrastructure.cache_database import CacheDatabase
from ..infrastructure.logger import logger


class CacheManager:
    """Manage caching of recognition results."""

    def __init__(
        self,
        cache_dir: Path,
        ttl_seconds: int = 300,
        max_size: int = 1000
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache database
            ttl_seconds: Time-to-live for cache entries (default: 5 minutes)
            max_size: Maximum number of cached results
        """
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size

        # Initialize database
        db_path = cache_dir / "recognition_cache.db"
        self.db = CacheDatabase(db_path)

        logger.info(
            f"Cache manager initialized: ttl={ttl_seconds}s, max_size={max_size}"
        )

    def get(self, screenshot: Screenshot) -> Optional[RecognitionResult]:
        """Get cached recognition result for screenshot.

        Args:
            screenshot: Screenshot to lookup

        Returns:
            Cached RecognitionResult if exists and not expired, else None
        """
        try:
            # Lookup in database
            cached_data = self.db.lookup_cache(screenshot.hash)

            if cached_data is None:
                return None

            # Parse to RecognitionResult
            result = RecognitionResult.from_dict(cached_data)

            # Check if expired
            if result.is_expired:
                logger.debug(f"Cache entry expired: {screenshot.hash[:8]}")
                return None

            logger.info(
                f"Cache hit: {screenshot.hash[:8]}, "
                f"hit_count={cached_data.get('_hit_count', 0)}"
            )

            return result

        except Exception as e:
            logger.exception(f"Cache lookup failed: {e}")
            return None

    def put(
        self,
        screenshot: Screenshot,
        result: RecognitionResult
    ):
        """Store recognition result in cache.

        Args:
            screenshot: Source screenshot
            result: Recognition result to cache
        """
        try:
            # Convert result to dict
            result_dict = result.to_dict()

            # Insert into database
            self.db.insert_cache(
                screenshot_hash=screenshot.hash,
                screenshot_width=screenshot.width,
                screenshot_height=screenshot.height,
                recognition_result=result_dict,
                model_name=result.model_name,
                ttl_minutes=self.ttl_seconds // 60,
                max_results=self.max_size
            )

            logger.info(
                f"Cached result: {screenshot.hash[:8]}, "
                f"elements={result.element_count}"
            )

        except Exception as e:
            logger.exception(f"Cache insertion failed: {e}")

    def clear(self):
        """Clear all cached data."""
        try:
            self.db.clear()
            logger.info("Cache cleared")

        except Exception as e:
            logger.exception(f"Cache clear failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        try:
            stats = self.db.get_stats()
            return stats

        except Exception as e:
            logger.exception(f"Failed to get cache stats: {e}")
            return {}

    def cleanup(self):
        """Cleanup expired entries."""
        try:
            deleted = self.db._cleanup_expired()
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired cache entries")

        except Exception as e:
            logger.exception(f"Cache cleanup failed: {e}")

    def close(self):
        """Close cache database."""
        try:
            self.db.close()
            logger.info("Cache manager closed")

        except Exception as e:
            logger.exception(f"Failed to close cache: {e}")


__all__ = ["CacheManager"]
