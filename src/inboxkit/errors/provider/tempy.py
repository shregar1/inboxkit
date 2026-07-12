"""tempy.email provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class TempyError(IProviderError):
    provider = "tempy.email"
