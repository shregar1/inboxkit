"""Shared constants package (provider-specific values live on each provider config)."""

from __future__ import annotations

from inboxkit.services.providers.registry import DEFAULT_PROVIDER_ORDER as PROVIDER_ORDER

__all__ = ["PROVIDER_ORDER"]
