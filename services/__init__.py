"""Inbox orchestration services."""

from __future__ import annotations

from inboxkit.abstractions import IService
from inboxkit.services.inbox import (
    InboxService,
    PROVIDER_ORDER,
    create_inbox,
    list_providers,
    poll_verify_link,
)
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
    IProviderService,
)

__all__ = [
    "IProviderGenerateService",
    "IProviderInboxService",
    "IProviderService",
    "IService",
    "InboxService",
    "PROVIDER_ORDER",
    "create_inbox",
    "list_providers",
    "poll_verify_link",
]
