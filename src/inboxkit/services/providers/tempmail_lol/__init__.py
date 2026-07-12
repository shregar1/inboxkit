"""Provider package: tempmail_lol."""

from __future__ import annotations

from inboxkit.services.providers.tempmail_lol.abstraction import (
    ITempMailLolGenerateService,
    ITempMailLolInboxService,
    ITempMailLolService,
)
from inboxkit.services.providers.tempmail_lol.generate import TempMailLolGenerateService
from inboxkit.services.providers.tempmail_lol.inbox import TempMailLolInboxService

_generate = TempMailLolGenerateService()
_inbox = TempMailLolInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ITempMailLolService",
    "ITempMailLolGenerateService",
    "ITempMailLolInboxService",
    "TempMailLolGenerateService",
    "TempMailLolInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
