# -*- coding: utf-8 -*-
"""Persistent URL cache for ticket deduplication."""
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path


class URLCache:
    """Track visited ticket URLs across crawler runs."""

    def __init__(self, cache_path=None, ttl_days=30):
        self.cache_path = Path(cache_path or "data/url_cache.json")
        self.ttl_days = ttl_days
        self._entries = {}
        self.load_from_disk()

    def is_visited(self, url):
        """Return True when a URL is already present and still within TTL."""
        if not url:
            return False

        self.clear_old_entries()
        return url in self._entries

    def mark_visited(self, url, metadata=None):
        """Remember a URL with optional ticket metadata."""
        if not url:
            return

        self._entries[url] = {
            "visited_at": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
        }

    def get_metadata(self, url):
        """Return stored metadata for a URL."""
        entry = self._entries.get(url, {})
        return entry.get("metadata", {})

    def save_to_disk(self):
        """Persist cache entries to JSON."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as cache_file:
            json.dump(self._entries, cache_file, indent=2, sort_keys=True)

    def load_from_disk(self):
        """Load cache entries from disk when a cache file exists."""
        if not self.cache_path.exists():
            self._entries = {}
            return

        try:
            with self.cache_path.open("r", encoding="utf-8") as cache_file:
                self._entries = json.load(cache_file)
        except (json.JSONDecodeError, OSError):
            self._entries = {}

        self.clear_old_entries()

    def clear_old_entries(self, days=None):
        """Remove entries older than the configured TTL."""
        max_age = timedelta(days=days or self.ttl_days)
        cutoff = datetime.now(UTC) - max_age
        fresh_entries = {}

        for url, entry in self._entries.items():
            visited_at = self._parse_datetime(entry.get("visited_at"))
            if visited_at is None or visited_at >= cutoff:
                fresh_entries[url] = entry

        self._entries = fresh_entries

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    def __len__(self):
        return len(self._entries)
