"""Public InboxKit router — mention a provider, run email ops."""

from __future__ import annotations

from inboxkit.router.abstraction import IInboxKitRouter
from inboxkit.router.inboxkit import InboxKit

TempMail = InboxKit  # back-compat alias

__all__ = [
    "IInboxKitRouter",
    "InboxKit",
    "TempMail",
]
