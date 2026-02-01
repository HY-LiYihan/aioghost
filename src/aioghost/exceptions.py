"""Exceptions for the Ghost Admin API client."""


class GhostError(Exception):
    """Base exception for Ghost API errors."""


class GhostAuthError(GhostError):
    """Authentication failed (invalid API key or expired token)."""


class GhostConnectionError(GhostError):
    """Failed to connect to the Ghost API."""


class GhostNotFoundError(GhostError):
    """Requested resource was not found."""


class GhostValidationError(GhostError):
    """Request validation failed."""
