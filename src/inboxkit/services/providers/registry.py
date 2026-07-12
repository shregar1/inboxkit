"""Injectable provider registry (DIP for InboxService).

Prefer ``inboxkit.factories.ProviderFactory`` for construction; this module
keeps ``ProviderSpec`` / ``default_provider_specs`` for back-compat.
"""

from __future__ import annotations

from inboxkit.services.providers.spec import ProviderSpec

__all__ = [
    "ProviderSpec",
    "default_provider_specs",
    "DEFAULT_PROVIDER_ORDER",
]


def default_provider_specs() -> list[ProviderSpec]:
    """Production wiring via ``ProviderFactory`` (DIP)."""
    from inboxkit.factories import ProviderFactory

    return ProviderFactory.default().create_specs()


DEFAULT_PROVIDER_ORDER: tuple[str, ...] = tuple(
    s.canonical for s in default_provider_specs()
)
