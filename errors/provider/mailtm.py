"""mail.tm provider errors."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError


class MailTmError(IProviderError):
    provider = "mail.tm"
