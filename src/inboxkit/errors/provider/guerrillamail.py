"""guerrillamail provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class GuerrillaMailError(IProviderError):
    provider = "guerrillamail"
