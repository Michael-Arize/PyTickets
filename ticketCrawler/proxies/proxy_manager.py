# -*- coding: utf-8 -*-
"""Proxy rotation and health tracking."""
import random
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class ProxyState:
    url: str
    failures: int = 0
    successes: int = 0
    enabled: bool = True
    last_success: str = None
    last_failure: str = None


class ProxyManager:
    """Choose and track proxies using simple health-aware rotation."""

    def __init__(self, proxies=None, strategy="round_robin", max_failures=3):
        self.proxies = [ProxyState(url=p) for p in (proxies or []) if p]
        self.strategy = strategy
        self.max_failures = max_failures
        self._index = 0

    @classmethod
    def from_env(cls):
        import os

        proxies = [
            item.strip()
            for item in os.environ.get("PYTICKETS_PROXIES", "").split(",")
            if item.strip()
        ]
        strategy = os.environ.get("PYTICKETS_PROXY_STRATEGY", "round_robin")
        max_failures = int(os.environ.get("PYTICKETS_PROXY_MAX_FAILURES", "3"))
        return cls(proxies=proxies, strategy=strategy, max_failures=max_failures)

    def has_proxies(self):
        return any(proxy.enabled for proxy in self.proxies)

    def get_next_proxy(self):
        active = [proxy for proxy in self.proxies if proxy.enabled]
        if not active:
            return None

        if self.strategy == "random":
            return random.choice(active).url

        proxy = active[self._index % len(active)]
        self._index += 1
        return proxy.url

    def mark_failed(self, proxy_url):
        proxy = self._find(proxy_url)
        if proxy is None:
            return
        proxy.failures += 1
        proxy.last_failure = datetime.now(UTC).isoformat()
        if proxy.failures >= self.max_failures:
            proxy.enabled = False

    def mark_successful(self, proxy_url):
        proxy = self._find(proxy_url)
        if proxy is None:
            return
        proxy.successes += 1
        proxy.failures = 0
        proxy.enabled = True
        proxy.last_success = datetime.now(UTC).isoformat()

    def get_health_status(self):
        return [
            {
                "url": proxy.url,
                "failures": proxy.failures,
                "successes": proxy.successes,
                "enabled": proxy.enabled,
                "last_success": proxy.last_success,
                "last_failure": proxy.last_failure,
            }
            for proxy in self.proxies
        ]

    def _find(self, proxy_url):
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                return proxy
        return None
