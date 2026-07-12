"""Provider package: maildrop."""

from __future__ import annotations

from inboxkit.services.providers.maildrop.abstraction import (
    IMailDropGenerateService,
    IMailDropInboxService,
    IMailDropService,
)
from inboxkit.services.providers.maildrop.generate import MailDropGenerateService
from inboxkit.services.providers.maildrop.inbox import MailDropInboxService

_generate = MailDropGenerateService()
_inbox = MailDropInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "IMailDropService",
    "IMailDropGenerateService",
    "IMailDropInboxService",
    "MailDropGenerateService",
    "MailDropInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
