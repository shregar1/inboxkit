"""Router operating modes."""

from __future__ import annotations

from inboxkit.abstractions import IEnum


class RouterMode(str, IEnum):
    """How ``InboxKit`` picks a provider when minting.

    sticky
        User pinned one provider. Only that provider is used — no fallback.
    fallback
        Try providers in order (user ``order`` or internal ``DEFAULT_ORDER``)
        until one succeeds.
    """

    STICKY = "sticky"
    FALLBACK = "fallback"

    @classmethod
    def coerce(cls, value: str | RouterMode | None) -> RouterMode | None:
        if value is None:
            return None
        if isinstance(value, RouterMode):
            return value
        key = value.strip().lower()
        for member in cls:
            if member.value == key or member.name.lower() == key:
                return member
        return None
