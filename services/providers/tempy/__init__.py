"""Provider package: tempy."""

from __future__ import annotations

from inboxkit.services.providers.tempy.abstraction import (
    ITempyGenerateService,
    ITempyInboxService,
    ITempyService,
)
from inboxkit.services.providers.tempy.generate import TempyGenerateService
from inboxkit.services.providers.tempy.inbox import TempyInboxService

_generate = TempyGenerateService()
_inbox = TempyInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ITempyService",
    "ITempyGenerateService",
    "ITempyInboxService",
    "TempyGenerateService",
    "TempyInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
