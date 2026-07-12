"""Shared provider-service contracts (ISP: generate vs inbox)."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.abstractions import IService
from inboxkit.models import TempInbox


class IProviderGenerateService(IService):
    """Mint-only contract for a disposable-mail provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Canonical provider id (e.g. ``mail.tm``)."""

    @abstractmethod
    def mint(self) -> TempInbox:
        """Create a new disposable inbox."""


class IProviderInboxService(IService):
    """List/read-only contract for a disposable-mail provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Canonical provider id (e.g. ``mail.tm``)."""

    @abstractmethod
    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        """List messages in ``inbox``."""

    @abstractmethod
    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        """Read one message body as text/html blob."""


# Back-compat name used by older imports — prefer the split interfaces.
IProviderService = IProviderGenerateService
