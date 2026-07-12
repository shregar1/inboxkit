"""Provider package: mailtm."""

from __future__ import annotations

from inboxkit.services.providers.mailtm.abstraction import (
    IMailTmGenerateService,
    IMailTmInboxService,
    IMailTmService,
)
from inboxkit.services.providers.mailtm.generate import MailTmGenerateService
from inboxkit.services.providers.mailtm.inbox import MailTmInboxService

_generate = MailTmGenerateService()
_inbox = MailTmInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "IMailTmService",
    "IMailTmGenerateService",
    "IMailTmInboxService",
    "MailTmGenerateService",
    "MailTmInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
