"""Provider package: guerrillamail."""

from __future__ import annotations

from inboxkit.services.providers.guerrillamail.abstraction import (
    IGuerrillaMailGenerateService,
    IGuerrillaMailInboxService,
    IGuerrillaMailService,
)
from inboxkit.services.providers.guerrillamail.generate import GuerrillaMailGenerateService
from inboxkit.services.providers.guerrillamail.inbox import GuerrillaMailInboxService

_generate = GuerrillaMailGenerateService()
_inbox = GuerrillaMailInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "IGuerrillaMailService",
    "IGuerrillaMailGenerateService",
    "IGuerrillaMailInboxService",
    "GuerrillaMailGenerateService",
    "GuerrillaMailInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
