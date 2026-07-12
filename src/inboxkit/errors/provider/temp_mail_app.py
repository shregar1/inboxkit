"""temp-mail.app provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class TempMailAppError(IProviderError):
    provider = "temp-mail.app"
