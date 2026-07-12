from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class MailTmConfig:
    """Shared mail.tm endpoints / identity.

    Public API (https://docs.mail.tm / OpenAPI, compatible with mail.gw docs):
      GET    /domains
      GET    /domains/{id}
      POST   /accounts
      GET    /accounts/{id}
      DELETE /accounts/{id}
      GET    /me
      POST   /token
      GET    /messages
      GET    /messages/{id}
      DELETE /messages/{id}
      PATCH  /messages/{id}   (mark seen)
      GET    /sources/{id}
    """

    BASE = "https://api.mail.tm"
    PROVIDER = "mail.tm"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class IMailTmGenerateService(MailTmConfig, IProviderGenerateService):
    """mail.tm account / domain lifecycle."""

    @abstractmethod
    def list_domains(self, *, page: int = 1) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_domain(self, domain_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def create_account(self, address: str, password: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_token(self, address: str, password: str) -> str: ...

    @abstractmethod
    def get_account(self, inbox: TempInbox, account_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def delete_account(self, inbox: TempInbox, account_id: str | None = None) -> None: ...

    @abstractmethod
    def me(self, inbox: TempInbox) -> dict[str, Any]: ...


class IMailTmInboxService(MailTmConfig, IProviderInboxService):
    """mail.tm message lifecycle."""

    @abstractmethod
    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def delete_message(self, inbox: TempInbox, message_id: str) -> None: ...

    @abstractmethod
    def mark_seen(self, inbox: TempInbox, message_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_source(self, inbox: TempInbox, message_id: str) -> dict[str, Any]: ...


IMailTmService = IMailTmGenerateService
