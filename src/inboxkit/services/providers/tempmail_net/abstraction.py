from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class TempmailNetConfig:
    """TempMail.net — https://tempmail.net/

    Same oturum-session stack as tempail.com (unofficial website API):

      GET  /                                  mint session + address
      POST /en/api/kontrol/                   poll inbox (HTML; 304 = unchanged)
      POST /en/api/oku/                       read message (HTML)
      POST /en/api/sil/                       delete message
      POST /en/api/duzelt/                    mark message
      POST /en/api/yoket/                     destroy mailbox (JSON)
      POST /en/api/iletisim/                  contact form

    No sifre/QR endpoint on this host. Session: oturum + PHPSESSID.
    """

    SITE = "https://tempmail.net"
    HOME = f"{SITE}/"
    PROVIDER = "tempmail.net"
    DEFAULT_APIS = {
        "kontrol": f"{SITE}/en/api/kontrol/",
        "oku": f"{SITE}/en/api/oku/",
        "sil": f"{SITE}/en/api/sil/",
        "duzelt": f"{SITE}/en/api/duzelt/",
        "yoket": f"{SITE}/en/api/yoket/",
        "iletisim": f"{SITE}/en/api/iletisim/",
    }

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ITempmailNetGenerateService(TempmailNetConfig, IProviderGenerateService):
    @abstractmethod
    def fetch_session(self) -> dict[str, Any]: ...

    @abstractmethod
    def destroy_mailbox(self, inbox: TempInbox) -> Any: ...

    @abstractmethod
    def mint(self) -> TempInbox: ...


class ITempmailNetInboxService(TempmailNetConfig, IProviderInboxService):
    @abstractmethod
    def poll_inbox(self, inbox: TempInbox) -> str: ...

    @abstractmethod
    def get_message(
        self, inbox: TempInbox, message_id: str, *, alt_id: str | None = None
    ) -> str: ...

    @abstractmethod
    def delete_message(
        self, inbox: TempInbox, message_id: str, *, alt_id: str | None = None
    ) -> None: ...

    @abstractmethod
    def mark_message(
        self, inbox: TempInbox, message_id: str, *, alt_id: str | None = None
    ) -> None: ...


ITempmailNetService = ITempmailNetGenerateService
