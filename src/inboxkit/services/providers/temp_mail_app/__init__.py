"""Provider package: temp_mail_app."""

from __future__ import annotations

from inboxkit.services.providers.temp_mail_app.abstraction import (
    ITempMailAppGenerateService,
    ITempMailAppInboxService,
    ITempMailAppService,
)
from inboxkit.services.providers.temp_mail_app.generate import TempMailAppGenerateService
from inboxkit.services.providers.temp_mail_app.inbox import TempMailAppInboxService

_generate = TempMailAppGenerateService()
_inbox = TempMailAppInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ITempMailAppService",
    "ITempMailAppGenerateService",
    "ITempMailAppInboxService",
    "TempMailAppGenerateService",
    "TempMailAppInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
