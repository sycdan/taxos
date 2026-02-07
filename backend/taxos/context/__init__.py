"""
Global context management for request-scoped data.

This module provides a thread-safe way to store and retrieve request context
(like the current tenant) without having to pass it through all function calls.
"""