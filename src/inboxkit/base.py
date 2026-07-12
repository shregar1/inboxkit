"""Back-compat re-exports — class-based utilities only."""

from __future__ import annotations

from inboxkit.models import TempInbox
from inboxkit.utilities import HttpUtility, NameUtility, VerifyUtility

UA = "inboxkit/0.1"

__all__ = [
    "UA",
    "TempInbox",
    "HttpUtility",
    "NameUtility",
    "VerifyUtility",
]
