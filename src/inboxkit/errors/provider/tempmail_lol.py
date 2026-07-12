"""tempmail.lol provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class TempMailLolError(IProviderError):
    provider = "tempmail.lol"
