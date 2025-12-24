"""SQLite cache database for recognition results.

This module implements the database design from spec/dev/db.spec.md
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

from .logger import logger


class CacheDatabase:
    """SQLite cache database for NVDA Vision plugin."""

    def __init__(self, db_path: Path):
        """Initialize database connection and create tables.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,  # Allow multi-threading
            isolation_level='DEFERRED'
        )
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

        self._create_tables()
        self._cleanup_expired()  # Startup cleanup

        logger.info(f"Cache database initialized at {db_path}")

    def _create_tables(self):
        """Create all tables and indexes if not exist."""
        # Create screenshots table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha256_hash TEXT UNIQUE NOT NULL,
                width INTEGER NOT NULL CHECK(width > 0),
                height INTEGER NOT NULL CHECK(height > 0),
                source_window TEXT,
                source_app TEXT,
                captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                file_size_kb INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create recognition_results table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS recognition_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screenshot_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT,
                inference_time_ms INTEGER NOT NULL CHECK(inference_time_ms >= 0),
                confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1),
                element_count INTEGER DEFAULT 0 CHECK(element_count >= 0),
                result_json TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0 CHECK(hit_count >= 0),
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'success',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
            )
        """)

        # Create ui_elements table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ui_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                element_type TEXT NOT NULL,
                text_content TEXT,
                x1 INTEGER NOT NULL,
                y1 INTEGER NOT NULL,
                x2 INTEGER NOT NULL,
                y2 INTEGER NOT NULL,
                confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                actionable BOOLEAN NOT NULL DEFAULT 0,
                parent_element_id INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (result_id) REFERENCES recognition_results(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_element_id) REFERENCES ui_elements(id) ON DELETE SET NULL
            )
        """)

        # Create indexes
        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_screenshots_hash ON screenshots(sha256_hash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_screenshots_expires ON screenshots(expires_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_results_screenshot ON recognition_results(screenshot_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_results_accessed ON recognition_results(last_accessed_at ASC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_elements_result ON ui_elements(result_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_elements_actionable ON ui_elements(actionable)")

        self.conn.commit()

    def lookup_cache(self, screenshot_hash: str) -> Optional[Dict[str, Any]]:
        """Lookup cached recognition result by screenshot hash.

        Args:
            screenshot_hash: SHA-256 hash of screenshot

        Returns:
            Recognition result dict if cache hit, None otherwise
        """
        cursor = self.conn.execute("""
            SELECT r.id, r.result_json, r.hit_count, r.model_name, r.inference_time_ms
            FROM recognition_results r
            JOIN screenshots s ON r.screenshot_id = s.id
            WHERE s.sha256_hash = ?
              AND s.expires_at > ?
            ORDER BY r.created_at DESC
            LIMIT 1
        """, (screenshot_hash, datetime.now().isoformat()))

        row = cursor.fetchone()
        if not row:
            logger.debug(f"Cache miss: {screenshot_hash[:8]}")
            return None

        # Update cache hit statistics
        self.conn.execute("""
            UPDATE recognition_results
            SET hit_count = hit_count + 1,
                last_accessed_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), row['id']))
        self.conn.commit()

        # Parse and return result
        result = json.loads(row['result_json'])
        result['_cache_hit'] = True
        result['_hit_count'] = row['hit_count'] + 1

        logger.debug(f"Cache hit: {screenshot_hash[:8]}")
        return result

    def insert_cache(
        self,
        screenshot_hash: str,
        screenshot_width: int,
        screenshot_height: int,
        recognition_result: Dict[str, Any],
        model_name: str,
        ttl_minutes: int = 5,
        max_results: int = 1000
    ):
        """Insert recognition result into cache.

        Args:
            screenshot_hash: SHA-256 hash
            screenshot_width: Screenshot width
            screenshot_height: Screenshot height
            recognition_result: Recognition result dict
            model_name: Model name used for inference
            ttl_minutes: Time-to-live in minutes
            max_results: Max cached results before LRU eviction
        """
        # Check if cache size limit exceeded
        count = self.conn.execute("SELECT COUNT(*) as cnt FROM recognition_results").fetchone()['cnt']
        if count >= max_results:
            self._evict_lru(max_results)

        # Insert screenshot (or get existing)
        now = datetime.now()
        expires_at = now + timedelta(minutes=ttl_minutes)

        self.conn.execute("""
            INSERT OR IGNORE INTO screenshots (
                sha256_hash, width, height,
                source_window, captured_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            screenshot_hash, screenshot_width, screenshot_height,
            recognition_result.get('source_window', 'Unknown'),
            now.isoformat(), expires_at.isoformat()
        ))

        # Get screenshot_id
        screenshot_id = self.conn.execute(
            "SELECT id FROM screenshots WHERE sha256_hash = ?",
            (screenshot_hash,)
        ).fetchone()['id']

        # Calculate metrics
        elements = recognition_result.get('elements', [])
        element_count = len(elements)
        avg_confidence = sum(e['confidence'] for e in elements) / element_count if element_count > 0 else 0.0
        inference_time_ms = int(recognition_result.get('inference_time', 0) * 1000)

        # Insert recognition result
        cursor = self.conn.execute("""
            INSERT INTO recognition_results (
                screenshot_id, model_name, inference_time_ms,
                confidence_score, element_count, result_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            screenshot_id, model_name, inference_time_ms,
            avg_confidence, element_count, json.dumps(recognition_result),
            recognition_result.get('status', 'success')
        ))
        result_id = cursor.lastrowid

        # Insert UI elements
        for element in elements:
            self.conn.execute("""
                INSERT INTO ui_elements (
                    result_id, element_type, text_content,
                    x1, y1, x2, y2, confidence, actionable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id, element['type'], element.get('text', ''),
                element['bbox'][0], element['bbox'][1],
                element['bbox'][2], element['bbox'][3],
                element['confidence'], element.get('actionable', False)
            ))

        self.conn.commit()
        logger.debug(f"Cached result: {screenshot_hash[:8]}, elements={element_count}")

    def _cleanup_expired(self) -> int:
        """Remove expired screenshots and cascaded results.

        Returns:
            Number of deleted screenshots
        """
        now = datetime.now().isoformat()
        cursor = self.conn.execute("DELETE FROM screenshots WHERE expires_at < ?", (now,))
        deleted_count = cursor.rowcount
        self.conn.commit()

        if deleted_count > 0:
            logger.debug(f"Cleaned up {deleted_count} expired cache entries")

        return deleted_count

    def _evict_lru(self, keep_count: int):
        """Evict least recently used results.

        Args:
            keep_count: Number of results to keep
        """
        current_count = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM recognition_results"
        ).fetchone()['cnt']

        if current_count <= keep_count:
            return

        to_delete = current_count - keep_count
        self.conn.execute("""
            DELETE FROM recognition_results
            WHERE id IN (
                SELECT id FROM recognition_results
                ORDER BY last_accessed_at ASC
                LIMIT ?
            )
        """, (to_delete,))
        self.conn.commit()

        logger.debug(f"Evicted {to_delete} LRU cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        stats = {}

        # Total counts
        stats['total_screenshots'] = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM screenshots"
        ).fetchone()['cnt']

        stats['total_results'] = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM recognition_results"
        ).fetchone()['cnt']

        stats['total_elements'] = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM ui_elements"
        ).fetchone()['cnt']

        # Cache hit statistics
        hit_stats = self.conn.execute("""
            SELECT
                SUM(hit_count) as total_hits,
                AVG(hit_count) as avg_hits
            FROM recognition_results
        """).fetchone()

        stats['total_cache_hits'] = hit_stats['total_hits'] or 0
        stats['avg_hits_per_result'] = hit_stats['avg_hits'] or 0

        # Calculate hit rate
        total_accesses = stats['total_results'] + stats['total_cache_hits']
        stats['hit_rate'] = (stats['total_cache_hits'] / total_accesses * 100) if total_accesses > 0 else 0

        return stats

    def clear(self):
        """Clear all cached data."""
        self.conn.execute("DELETE FROM ui_elements")
        self.conn.execute("DELETE FROM recognition_results")
        self.conn.execute("DELETE FROM screenshots")
        self.conn.commit()

        # Vacuum to reclaim space
        self.conn.execute("VACUUM")

        logger.info("Cache cleared")

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Cache database closed")


__all__ = ["CacheDatabase"]
