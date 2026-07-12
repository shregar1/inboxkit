"""temp-mail.org provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class TempMailOrgError(IProviderError):
    provider = "temp-mail.org"
