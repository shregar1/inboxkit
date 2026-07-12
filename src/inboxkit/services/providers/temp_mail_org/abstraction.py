from __future__ import annotations

from abc import abstractmethod
from typing import Any, Literal

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)

Backend = Literal["web", "official"]


class TempMailOrgConfig:
    """Temp Mail — https://temp-mail.io / https://temp-mail.org (same product)

    Product: https://temp-mail.io/en
    Official paid API (https://docs.temp-mail.io/docs/getting-started):
      Base https://api.temp-mail.io/v1 — header X-API-Key
      GET    /domains
      POST   /emails
      GET    /emails/{email}/messages
      GET    /messages/{id}
      GET    /messages/{id}/source
      GET    /messages/{id}/attachments/{aid}
      DELETE /messages/{id}
      DELETE /emails/{email}
      GET    /rate_limit

    Free website backend (used when no API key):
      Base https://api.internal.temp-mail.io/api/v3
      GET  /domains
      POST /email/new
      GET  /email/{address}/messages

    Auth env: TEMP_MAIL_API_KEY or TEMPMAIL_IO_API_KEY
    Aliases: temp-mail.io, tempmail.io, temp-mail.org, …
    """

    BASE = "https://api.internal.temp-mail.io/api/v3"
    OFFICIAL_BASE = "https://api.temp-mail.io/v1"
    SITE = "https://temp-mail.io"
    PROVIDER = "temp-mail.org"
    HEADERS = {
        "Origin": SITE,
        "Referer": f"{SITE}/",
        "Application-Name": "web",
    }

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ITempMailOrgGenerateService(TempMailOrgConfig, IProviderGenerateService):
    @abstractmethod
    def list_domains(self, *, backend: Backend | None = None) -> list[str]: ...

    @abstractmethod
    def create_email(
        self,
        *,
        name: str | None = None,
        domain: str | None = None,
        domain_type: str | None = None,
        backend: Backend | None = None,
        **body: Any,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def delete_email(self, inbox: TempInbox) -> None: ...

    @abstractmethod
    def rate_limit(self) -> Any: ...

    @abstractmethod
    def mint(self, *, backend: Backend | None = None, domain: str | None = None) -> TempInbox: ...


class ITempMailOrgInboxService(TempMailOrgConfig, IProviderInboxService):
    @abstractmethod
    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def delete_message(self, inbox: TempInbox, message_id: str) -> None: ...

    @abstractmethod
    def get_source(self, inbox: TempInbox, message_id: str) -> Any: ...

    @abstractmethod
    def download_attachment(
        self, inbox: TempInbox, message_id: str, attachment_id: str
    ) -> bytes: ...


ITempMailOrgService = ITempMailOrgGenerateService
