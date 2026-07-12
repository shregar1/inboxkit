"""Per-provider error types."""

from __future__ import annotations

from inboxkit.errors.provider.abstraction import IProviderError
from inboxkit.errors.provider.guerrillamail import GuerrillaMailError
from inboxkit.errors.provider.maildrop import MailDropError
from inboxkit.errors.provider.mailtm import MailTmError
from inboxkit.errors.provider.secmail import SecMailError
from inboxkit.errors.provider.temp_mail_app import TempMailAppError
from inboxkit.errors.provider.temp_mail_org import TempMailOrgError
from inboxkit.errors.provider.tempmail_lol import TempMailLolError
from inboxkit.errors.provider.smailpro import SmailProError
from inboxkit.errors.provider.tempail import TempailError
from inboxkit.errors.provider.tempmail_net import TempmailNetError
from inboxkit.errors.provider.tempy import TempyError

__all__ = [
    "GuerrillaMailError",
    "IProviderError",
    "MailDropError",
    "MailTmError",
    "SecMailError",
    "SmailProError",
    "TempMailAppError",
    "TempMailLolError",
    "TempMailOrgError",
    "TempailError",
    "TempmailNetError",
    "TempyError",
]
