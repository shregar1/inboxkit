from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class MailDropConfig:
    """Maildrop GraphQL API (https://docs.maildrop.cc).

    Query: ping, inbox, message, altinbox, statistics, status
    Mutation: delete(mailbox, id)
    Endpoint: POST https://api.maildrop.cc/graphql
    """

    DOMAIN = "maildrop.cc"
    GRAPHQL = "https://api.maildrop.cc/graphql"
    PROVIDER = "maildrop"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class IMailDropGenerateService(MailDropConfig, IProviderGenerateService):
    @abstractmethod
    def ping(self, message: str = "hello") -> str: ...

    @abstractmethod
    def statistics(self) -> dict[str, Any]: ...

    @abstractmethod
    def status(self) -> str: ...

    @abstractmethod
    def altinbox(self, mailbox: str) -> str: ...


class IMailDropInboxService(MailDropConfig, IProviderInboxService):
    @abstractmethod
    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def delete_message(self, inbox: TempInbox, message_id: str) -> bool: ...


IMailDropService = IMailDropGenerateService
