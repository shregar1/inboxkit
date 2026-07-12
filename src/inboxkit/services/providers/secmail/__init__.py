"""Provider package: secmail."""

from __future__ import annotations

from inboxkit.services.providers.secmail.abstraction import (
    ISecMailGenerateService,
    ISecMailInboxService,
    ISecMailService,
)
from inboxkit.services.providers.secmail.generate import SecMailGenerateService
from inboxkit.services.providers.secmail.inbox import SecMailInboxService

_generate = SecMailGenerateService()
_inbox = SecMailInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ISecMailService",
    "ISecMailGenerateService",
    "ISecMailInboxService",
    "SecMailGenerateService",
    "SecMailInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
