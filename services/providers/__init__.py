"""Disposable-mail provider packages."""

from __future__ import annotations

from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
    IProviderService,
)

from . import (
    guerrillamail,
    maildrop,
    mailtm,
    secmail,
    smailpro,
    temp_mail_app,
    temp_mail_org,
    tempail,
    tempmail_net,
    tempmail_lol,
    tempy,
)

__all__ = [
    "IProviderGenerateService",
    "IProviderInboxService",
    "IProviderService",
    "guerrillamail",
    "maildrop",
    "mailtm",
    "secmail",
    "smailpro",
    "temp_mail_app",
    "temp_mail_org",
    "tempail",
    "tempmail_net",
    "tempmail_lol",
    "tempy",
]
