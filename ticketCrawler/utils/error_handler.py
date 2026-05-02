# -*- coding: utf-8 -*-
"""Error classification and recovery hints for crawler operations."""
from enum import Enum


class ErrorType(Enum):
    RATE_LIMITED = "rate_limited"
    AUTH_FAILED = "auth_failed"
    BLOCKED = "blocked"
    SERVER_ERROR = "server_error"
    NETWORK = "network"
    PARSE = "parse"
    UNKNOWN = "unknown"


class ErrorHandler:
    """Classify common crawler failures and describe retry behavior."""

    RETRYABLE = {
        ErrorType.RATE_LIMITED,
        ErrorType.BLOCKED,
        ErrorType.SERVER_ERROR,
        ErrorType.NETWORK,
    }

    @classmethod
    def classify_error(cls, error):
        text = str(error).lower()

        if any(marker in text for marker in ["429", "rate limit", "too many requests"]):
            return ErrorType.RATE_LIMITED
        if any(marker in text for marker in ["401", "403", "access denied", "forbidden"]):
            return ErrorType.BLOCKED
        if any(marker in text for marker in ["login", "auth", "credential", "facebook"]):
            return ErrorType.AUTH_FAILED
        if any(marker in text for marker in ["500", "502", "503", "504", "server"]):
            return ErrorType.SERVER_ERROR
        if any(marker in text for marker in ["timeout", "connection", "dns", "network"]):
            return ErrorType.NETWORK
        if any(marker in text for marker in ["xpath", "selector", "parse"]):
            return ErrorType.PARSE
        return ErrorType.UNKNOWN

    @classmethod
    def is_retryable(cls, error):
        return cls.classify_error(error) in cls.RETRYABLE

    @classmethod
    def suggest_action(cls, error):
        error_type = cls.classify_error(error)
        actions = {
            ErrorType.RATE_LIMITED: "Back off before retrying; rotate proxy if configured.",
            ErrorType.AUTH_FAILED: "Refresh credentials and re-authenticate before retrying.",
            ErrorType.BLOCKED: "Pause crawling and try a different proxy or browser profile.",
            ErrorType.SERVER_ERROR: "Retry after a short delay.",
            ErrorType.NETWORK: "Retry with exponential backoff.",
            ErrorType.PARSE: "Check selectors against the current site markup.",
            ErrorType.UNKNOWN: "Capture debug HTML and inspect logs.",
        }
        return actions[error_type]
