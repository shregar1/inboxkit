"""Provider package: tempmail.net."""

from __future__ import annotations

from inboxkit.services.providers.tempmail_net.abstraction import (
    ITempmailNetGenerateService,
    ITempmailNetInboxService,
    ITempmailNetService,
)
from inboxkit.services.providers.tempmail_net.generate import TempmailNetGenerateService
from inboxkit.services.providers.tempmail_net.inbox import TempmailNetInboxService

_generate = TempmailNetGenerateService()
_inbox = TempmailNetInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ITempmailNetService",
    "ITempmailNetGenerateService",
    "ITempmailNetInboxService",
    "TempmailNetGenerateService",
    "TempmailNetInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
