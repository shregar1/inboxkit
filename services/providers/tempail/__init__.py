"""Provider package: tempail (https://tempail.com)."""

from __future__ import annotations

from inboxkit.services.providers.tempail.abstraction import (
    ITempailGenerateService,
    ITempailInboxService,
    ITempailService,
)
from inboxkit.services.providers.tempail.generate import TempailGenerateService
from inboxkit.services.providers.tempail.inbox import TempailInboxService

_generate = TempailGenerateService()
_inbox = TempailInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ITempailService",
    "ITempailGenerateService",
    "ITempailInboxService",
    "TempailGenerateService",
    "TempailInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
