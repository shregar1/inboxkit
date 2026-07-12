"""Object factories (provider construction, DIP wiring)."""

from __future__ import annotations

from inboxkit.factories.abstraction import IProviderFactory
from inboxkit.factories.provider import (
    ProviderFactory,
    ProviderRegistration,
    default_registrations,
)

__all__ = [
    "IProviderFactory",
    "ProviderFactory",
    "ProviderRegistration",
    "default_registrations",
]
