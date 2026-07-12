"""tempmail.net provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class TempmailNetError(IProviderError):
    provider = "tempmail.net"
