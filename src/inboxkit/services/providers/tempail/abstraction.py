from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class TempailConfig:
    """Tempail — https://tempail.com/en/

    No official public API. Website session endpoints (from page JS):

      GET  / or /en/                          mint session + address
      POST /en/api/kontrol/                   poll inbox (HTML fragment)
      POST /en/api/oku/                       read message (HTML)
      POST /en/api/sil/                       delete message
      POST /en/api/duzelt/                    mark / fix message
      POST /en/api/yoket/                     destroy mailbox (JSON)
      POST /en/api/sifre/                     QR / recover URL (JSON)
      POST /en/api/iletisim/                  contact form (captcha)

    Session fields embedded in the homepage script:
      oturum (session token), tarih (poll watermark), PHPSESSID cookie

    Addresses expire ~1 hour. Site may present a reCAPTCHA challenge
    (bot-kontrol.php) under bot protection — raise TempailError in that case.
    """

    SITE = "https://tempail.com"
    HOME = f"{SITE}/"
    PROVIDER = "tempail"
    DEFAULT_APIS = {
        "kontrol": f"{SITE}/en/api/kontrol/",
        "oku": f"{SITE}/en/api/oku/",
        "sil": f"{SITE}/en/api/sil/",
        "duzelt": f"{SITE}/en/api/duzelt/",
        "yoket": f"{SITE}/en/api/yoket/",
        "sifre": f"{SITE}/en/api/sifre/",
        "iletisim": f"{SITE}/en/api/iletisim/",
    }

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ITempailGenerateService(TempailConfig, IProviderGenerateService):
    @abstractmethod
    def fetch_session(self) -> dict[str, Any]: ...

    @abstractmethod
    def destroy_mailbox(self, inbox: TempInbox) -> Any: ...

    @abstractmethod
    def recover_qr(self, inbox: TempInbox) -> Any: ...

    @abstractmethod
    def mint(self) -> TempInbox: ...


class ITempailInboxService(TempailConfig, IProviderInboxService):
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


ITempailService = ITempailGenerateService
