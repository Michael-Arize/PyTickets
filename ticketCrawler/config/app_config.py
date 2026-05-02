# -*- coding: utf-8 -*-
"""Central environment configuration helpers."""
import os
from pathlib import Path


class AppConfig:
    """Read PyTickets settings from environment and optional .env files."""

    def __init__(self, env_path=None):
        self.env_path = Path(env_path or ".env")
        self.load_dotenv()

    def load_dotenv(self):
        """Load simple KEY=VALUE lines without overriding existing env vars."""
        if not self.env_path.exists():
            return

        with self.env_path.open("r", encoding="utf-8") as env_file:
            for line in env_file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    @staticmethod
    def get(name, default=None):
        return os.environ.get(name, default)

    @staticmethod
    def get_int(name, default=0):
        value = os.environ.get(name)
        return int(value) if value not in (None, "") else default

    @staticmethod
    def get_float(name, default=0.0):
        value = os.environ.get(name)
        return float(value) if value not in (None, "") else default

    @staticmethod
    def get_bool(name, default=False):
        value = os.environ.get(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @property
    def database_path(self):
        return self.get("PYTICKETS_DB_PATH", "data/pytickets.db")

    @property
    def url_cache_path(self):
        return self.get("PYTICKETS_URL_CACHE", "data/url_cache.json")

    @property
    def notify_mode(self):
        return self.get("PYTICKETS_NOTIFY_MODE", "first").lower()

    @property
    def debug_dir(self):
        return self.get("PYTICKETS_DEBUG_DIR", "data/debug")

    @property
    def proxy_list(self):
        raw = self.get("PYTICKETS_PROXIES", "")
        return [item.strip() for item in raw.split(",") if item.strip()]


config = AppConfig()
