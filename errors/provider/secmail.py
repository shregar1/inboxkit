"""1secmail provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class SecMailError(IProviderError):
    provider = "1secmail"
