"""Provider package: smailpro (Sonjj temporary Gmail / Outlook / domains)."""

from __future__ import annotations

from inboxkit.services.providers.smailpro.abstraction import (
    ISmailProGenerateService,
    ISmailProInboxService,
    ISmailProService,
)
from inboxkit.services.providers.smailpro.generate import SmailProGenerateService
from inboxkit.services.providers.smailpro.inbox import SmailProInboxService

_generate = SmailProGenerateService()
_inbox = SmailProInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ISmailProService",
    "ISmailProGenerateService",
    "ISmailProInboxService",
    "SmailProGenerateService",
    "SmailProInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
