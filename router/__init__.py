"""Public TempMail router — mention a provider, run email ops."""

from __future__ import annotations

from inboxkit.router.abstraction import ITempMailRouter
from inboxkit.router.tempmail import TempMail

__all__ = [
    "ITempMailRouter",
    "TempMail",
]
