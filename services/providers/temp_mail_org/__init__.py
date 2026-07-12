"""Provider package: temp_mail_org."""

from __future__ import annotations

from inboxkit.services.providers.temp_mail_org.abstraction import (
    ITempMailOrgGenerateService,
    ITempMailOrgInboxService,
    ITempMailOrgService,
)
from inboxkit.services.providers.temp_mail_org.generate import TempMailOrgGenerateService
from inboxkit.services.providers.temp_mail_org.inbox import TempMailOrgInboxService

_generate = TempMailOrgGenerateService()
_inbox = TempMailOrgInboxService()

mint = _generate.mint
list_messages = _inbox.list_messages
read_message = _inbox.read_message
_list = list_messages
_read = read_message

__all__ = [
    "ITempMailOrgService",
    "ITempMailOrgGenerateService",
    "ITempMailOrgInboxService",
    "TempMailOrgGenerateService",
    "TempMailOrgInboxService",
    "mint",
    "list_messages",
    "read_message",
    "_list",
    "_read",
]
